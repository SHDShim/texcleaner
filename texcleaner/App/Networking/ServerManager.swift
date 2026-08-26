import Foundation
import Security

@MainActor
final class ServerManager: ObservableObject {
    static let shared = ServerManager()
    static let authTokenDefaultsKey = "TeXCleaner.APIAuthToken"

    @Published private(set) var isRunning = false
    @Published private(set) var launchError: String?

    private var process: Process?
    private var loggingPipe: Pipe?

    private init() {}

    func start() {
        guard process == nil else { return }

        guard let backendURL = Bundle.main.resourceURL?.appendingPathComponent("backend"),
              FileManager.default.fileExists(
                  atPath: backendURL.appendingPathComponent("texcleaner/server.py").path
              )
        else {
            launchError = "The bundled Python backend is missing. Rebuild TeXCleaner."
            return
        }

        guard let condaURL = Self.condaExecutableURL() else {
            launchError = "Conda was not found. Install Miniforge or Anaconda and create the docflow environment."
            return
        }

        let server = Process()
        let authToken = Self.makeAuthToken()
        server.executableURL = condaURL
        server.arguments = [
            "run", "--no-capture-output", "-n", "docflow",
            "python", "-m", "texcleaner", "--server", "--port", "8765",
            "--auth-token", authToken,
        ]
        server.currentDirectoryURL = backendURL

        let loggingPipe = Pipe()
        server.standardOutput = loggingPipe
        server.standardError = loggingPipe
        loggingPipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            guard !data.isEmpty,
                  let message = String(data: data, encoding: .utf8)
            else { return }
            print("[TeXCleaner backend] \(message)", terminator: "")
        }
        server.terminationHandler = { [weak self] terminatedProcess in
            Task { @MainActor in
                self?.loggingPipe?.fileHandleForReading.readabilityHandler = nil
                self?.loggingPipe = nil
                self?.process = nil
                self?.isRunning = false
                if terminatedProcess.terminationStatus != 0 {
                    self?.launchError = "The Python backend exited with status \(terminatedProcess.terminationStatus)."
                }
            }
        }

        do {
            try server.run()
        } catch {
            launchError = "Failed to start the Python backend: \(error.localizedDescription)"
            return
        }

        process = server
        self.loggingPipe = loggingPipe
        UserDefaults.standard.set(authToken, forKey: Self.authTokenDefaultsKey)
        isRunning = true
        launchError = nil
    }

    func stop() {
        guard let process else { return }
        if process.isRunning {
            process.terminate()
        }
        self.process = nil
        loggingPipe?.fileHandleForReading.readabilityHandler = nil
        loggingPipe = nil
        UserDefaults.standard.removeObject(forKey: Self.authTokenDefaultsKey)
        isRunning = false
    }

    private static func makeAuthToken() -> String {
        var bytes = [UInt8](repeating: 0, count: 32)
        _ = SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes)
        return Data(bytes).base64EncodedString()
    }

    private static func condaExecutableURL() -> URL? {
        let home = FileManager.default.homeDirectoryForCurrentUser
        let candidates = [
            "/opt/homebrew/bin/conda",
            "/usr/local/bin/conda",
            home.appendingPathComponent("miniforge3/bin/conda").path,
            home.appendingPathComponent("anaconda3/bin/conda").path,
        ]

        return candidates
            .first(where: { FileManager.default.isExecutableFile(atPath: $0) })
            .map(URL.init(fileURLWithPath:))
    }
}
