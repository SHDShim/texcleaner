import Foundation
import Combine

class ArxivViewModel: ObservableObject {
    @Published var folderPath = ""
    @Published var logs: [String] = []
    @Published var isProcessing = false
    @Published var errorMessage: String?
    @Published var completedOutputPath: String?
    @Published var resizeImages = true
    @Published var imageSize = 500
    @Published var compressPDF = false
    @Published var pdfResolution = 500
    @Published var keepBib = false
    @Published var verbose = false
    @Published var outputSuffix = "-cleaned"
    @Published var overwriteExisting = false

    private let client = BackendClient.shared
    private var webSocketTask: URLSessionWebSocketTask?

    var isOutputSuffixValid: Bool {
        !outputSuffix.isEmpty
            && !outputSuffix.contains("/")
            && !outputSuffix.contains("\\")
            && outputSuffix.unicodeScalars.allSatisfy { !CharacterSet.controlCharacters.contains($0) }
    }

    var outputPath: String? {
        guard !folderPath.isEmpty, isOutputSuffixValid else { return nil }
        let inputURL = URL(fileURLWithPath: folderPath)
        return inputURL.deletingLastPathComponent()
            .appendingPathComponent(inputURL.lastPathComponent + outputSuffix)
            .path
    }

    func clean() {
        guard !folderPath.isEmpty else {
            errorMessage = "Please select a project folder."
            return
        }
        guard isOutputSuffixValid else {
            errorMessage = "Enter a non-empty output suffix without path separators."
            return
        }
        guard !resizeImages || (1...10000).contains(imageSize) else {
            errorMessage = "Image size must be between 1 and 10,000 pixels."
            return
        }
        guard !compressPDF || (1...2400).contains(pdfResolution) else {
            errorMessage = "PDF resolution must be between 1 and 2,400 dpi."
            return
        }

        isProcessing = true
        errorMessage = nil
        completedOutputPath = nil
        logs = []

        client.arxiv(
            at: folderPath,
            resizeImages: resizeImages,
            imageSize: imageSize,
            compressPDF: compressPDF,
            pdfResolution: pdfResolution,
            keepBib: keepBib,
            verbose: verbose,
            outputSuffix: outputSuffix,
            overwrite: overwriteExisting
        ) { [weak self] result in
            guard let self = self else { return }
            DispatchQueue.main.async {
                guard case .success(let jobId) = result, !jobId.isEmpty else {
                    if case .failure(let error) = result {
                        self.errorMessage = error.localizedDescription
                    } else {
                        self.errorMessage = "The cleaning job could not be started."
                    }
                    self.isProcessing = false
                    return
                }
                self.logs.append("Job started: \(jobId)\n")
            }
            if case .success(let jobId) = result, !jobId.isEmpty {
                self.subscribeToJob(jobId: jobId)
            }
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
