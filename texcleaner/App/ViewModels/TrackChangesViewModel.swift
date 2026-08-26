import Foundation
import Combine

class TrackChangesViewModel: ObservableObject {
    @Published var inputPath = ""
    @Published var logs: [String] = []
    @Published var isProcessing = false
    @Published var errorMessage: String?
    @Published var completedOutputPath: String?
    @Published var revisionChoice: RevisionChoice = .new
    @Published var removeAnnotations = true
    @Published var outputSuffix = "-cleaned"
    @Published var overwriteExisting = false

    private let client = BackendClient.shared
    private var webSocketTask: URLSessionWebSocketTask?
    private var cancellables = Set<AnyCancellable>()

    var isOutputSuffixValid: Bool {
        !outputSuffix.isEmpty
            && !outputSuffix.contains("/")
            && !outputSuffix.contains("\\")
            && outputSuffix.unicodeScalars.allSatisfy { !CharacterSet.controlCharacters.contains($0) }
    }

    var outputPath: String? {
        guard !inputPath.isEmpty, isOutputSuffixValid else { return nil }
        let inputURL = URL(fileURLWithPath: inputPath)
        let filename = inputURL.deletingPathExtension().lastPathComponent + outputSuffix
        return inputURL.deletingLastPathComponent()
            .appendingPathComponent(filename)
            .appendingPathExtension(inputURL.pathExtension)
            .path
    }

    func clean() {
        guard !inputPath.isEmpty else {
            errorMessage = "Please select an input file."
            return
        }
        guard isOutputSuffixValid else {
            errorMessage = "Enter a non-empty output suffix without path separators."
            return
        }

        isProcessing = true
        errorMessage = nil
        completedOutputPath = nil
        logs = []

        client.detectModule(at: inputPath) { [weak self] result in
            guard let self = self else { return }

            DispatchQueue.main.async {
                guard case .success(let detected) = result else {
                    if case .failure(let error) = result {
                        self.errorMessage = error.localizedDescription
                    } else {
                        self.errorMessage = "The backend could not be reached."
                    }
                    self.isProcessing = false
                    return
                }
                let label = detected ?? "none"
                self.logs.append("Detected module: \(label)\n")

                guard let module = detected else {
                    self.logs.append("No track changes detected.\n")
                    self.isProcessing = false
                    return
                }

                if module == "trackchanges" {
                    self.startCleaning(endpoint: "trackchanges")
                } else {
                    self.startCleaning(endpoint: "changes")
                }
            }
        }
    }

    private func startCleaning(endpoint: String) {
        if endpoint == "changes" {
            client.changes(
                at: inputPath,
                keepVersion: revisionChoice,
                removeAnnotations: removeAnnotations,
                outputSuffix: outputSuffix,
                overwrite: overwriteExisting
            ) { [weak self] result in
                DispatchQueue.main.async {
                    self?.handleStartedJob(result)
                }
                if case .success(let jobId) = result, !jobId.isEmpty {
                    self?.subscribeToJob(jobId: jobId)
                }
            }
        } else {
            client.trackChanges(
                at: inputPath,
                keepVersion: revisionChoice,
                removeAnnotations: removeAnnotations,
                outputSuffix: outputSuffix,
                overwrite: overwriteExisting
            ) { [weak self] result in
                DispatchQueue.main.async {
                    self?.handleStartedJob(result)
                }
                if case .success(let jobId) = result, !jobId.isEmpty {
                    self?.subscribeToJob(jobId: jobId)
                }
            }
        }
    }

    private func handleStartedJob(_ result: Result<String, Error>) {
        switch result {
        case .success(let jobId) where !jobId.isEmpty:
            logs.append("Job started: \(jobId)\n")
        case .success:
            errorMessage = "The cleaning job could not be started."
            isProcessing = false
        case .failure(let error):
            errorMessage = error.localizedDescription
            isProcessing = false
        }
    }

    private func subscribeToJob(jobId: String) {
        guard !jobId.isEmpty else { return }

        let wsTask = client.connectWebSocket(jobId: jobId) { [weak self] msg in
            DispatchQueue.main.async {
                if !msg.logs.isEmpty || msg.status != nil {
                    self?.logs = msg.logs
                }
                if let status = msg.status {
                    self?.logs.append("Status: \(status)\n")
                    if status == "error" {
                        self?.errorMessage = msg.result
                    } else if status == "success" {
                        self?.completedOutputPath = msg.outputPath
                    }
                    self?.isProcessing = false
                    self?.webSocketTask = nil
                }
            }
        }
        webSocketTask = wsTask
    }

    func cancel() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        isProcessing = false
    }
}
