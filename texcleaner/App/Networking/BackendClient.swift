import Foundation

enum BackendClientError: LocalizedError {
    case unavailable(String)
    case invalidResponse
    case server(statusCode: Int, detail: String)

    var errorDescription: String? {
        switch self {
        case .unavailable(let message), .server(_, let message):
            return message
        case .invalidResponse:
            return "The TeXCleaner backend returned an invalid response."
        }
    }
}

class BackendClient: ObservableObject {
    static let shared = BackendClient()

    private let serverURL = URL(string: "http://127.0.0.1:8765")!
    private let session: URLSession

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        session = URLSession(configuration: config)
    }

    func detectModule(at inputPath: String, completion: @escaping (Result<String?, Error>) -> Void) {
        var components = URLComponents(url: serverURL.appendingPathComponent("/detect"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "input_path", value: inputPath)]

        var request = URLRequest(url: components.url!)
        addAuthorization(to: &request)
        let task = session.dataTask(with: request) { [weak self] data, response, error in
            if let error = error {
                print("Detect failed: \(error)")
                completion(.failure(BackendClientError.unavailable(error.localizedDescription)))
                return
            }
            guard let data = data else {
                completion(.failure(BackendClientError.invalidResponse))
                return
            }
            guard let self else {
                completion(.failure(BackendClientError.unavailable("The backend client is unavailable.")))
                return
            }
            do {
                let json = try self.decodeJSON(data: data, response: response as? HTTPURLResponse)
                completion(.success(json["detected"] as? String))
            } catch {
                completion(.failure(error))
            }
        }
        task.resume()
    }

    func trackChanges(
        at inputPath: String,
        keepVersion: RevisionChoice,
        removeAnnotations: Bool,
        outputSuffix: String,
        overwrite: Bool,
        completion: @escaping (Result<String, Error>) -> Void
    ) {
        let body: [String: Any] = [
            "input_path": inputPath,
            "keep_version": keepVersion.rawValue,
            "remove_annotations": removeAnnotations,
            "output_suffix": outputSuffix,
            "overwrite": overwrite,
        ]
        performClean("trackchanges", body: body, completion: completion)
    }

    func changes(
        at inputPath: String,
        keepVersion: RevisionChoice,
        removeAnnotations: Bool,
        outputSuffix: String,
        overwrite: Bool,
        completion: @escaping (Result<String, Error>) -> Void
    ) {
        let body: [String: Any] = [
            "input_path": inputPath,
            "keep_version": keepVersion.rawValue,
            "remove_annotations": removeAnnotations,
            "output_suffix": outputSuffix,
            "overwrite": overwrite,
        ]
        performClean("changes", body: body, completion: completion)
    }

    func arxiv(
        at folderPath: String,
        resizeImages: Bool,
        imageSize: Int,
        compressPDF: Bool,
        pdfResolution: Int,
        keepBib: Bool,
        verbose: Bool,
        outputSuffix: String,
        overwrite: Bool,
        completion: @escaping (Result<String, Error>) -> Void
    ) {
        let body: [String: Any] = [
            "folder_path": folderPath,
            "resize_images": resizeImages,
            "image_size": imageSize,
            "compress_pdf": compressPDF,
            "pdf_resolution": pdfResolution,
            "keep_bib": keepBib,
            "verbose": verbose,
            "output_suffix": outputSuffix,
            "overwrite": overwrite,
        ]
        performClean("arxiv", body: body, completion: completion)
    }

    func getJobDetail(jobId: String, completion: @escaping (JobDetail?) -> Void) {
        var request = URLRequest(url: serverURL.appendingPathComponent("/jobs/\(jobId)"))
        addAuthorization(to: &request)
        let task = session.dataTask(with: request) { data, _, error in
            if let error = error {
                print("Job detail failed: \(error)")
                completion(nil)
                return
            }
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                completion(nil)
                return
            }
            let detail = JobDetail(
                jobId: json["job_id"] as? String ?? "",
                status: json["status"] as? String ?? "unknown",
                logs: json["logs"] as? [String] ?? [],
                result: json["result"] as? String,
                outputPath: json["output_path"] as? String,
                createdAt: json["created_at"] as? String,
                finishedAt: json["finished_at"] as? String
            )
            completion(detail)
        }
        task.resume()
    }

    func connectWebSocket(jobId: String, onMessage: @escaping (WebSocketMessage) -> Void) -> URLSessionWebSocketTask? {
        var url = serverURL.appendingPathComponent("/ws/logs/\(jobId)")
        var comps = URLComponents(url: url, resolvingAgainstBaseURL: false)!
        comps.scheme = comps.scheme == "http" ? "ws" : "wss"
        url = comps.url ?? serverURL
        var request = URLRequest(url: url)
        addAuthorization(to: &request)
        let task = session.webSocketTask(with: request)

        task.resume()

        func receive() {
            task.receive { result in
                switch result {
                case .success(let message):
                    switch message {
                    case .string(let text):
                        if let data = text.data(using: .utf8),
                           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                            let msg = WebSocketMessage(
                                logsUpdated: json["logs_updated"] as? Int ?? 0,
                                status: json["status"] as? String,
                                result: json["result"] as? String,
                                outputPath: json["output_path"] as? String,
                                logs: json["logs"] as? [String] ?? []
                            )
                            onMessage(msg)
                        }
                    case .data(let data):
                        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                            let msg = WebSocketMessage(
                                logsUpdated: json["logs_updated"] as? Int ?? 0,
                                status: json["status"] as? String,
                                result: json["result"] as? String,
                                outputPath: json["output_path"] as? String,
                                logs: json["logs"] as? [String] ?? []
                            )
                            onMessage(msg)
                        }
                    @unknown default:
                        break
                    }
                    receive()
                case .failure(let error):
                    onMessage(WebSocketMessage(
                        logsUpdated: 0,
                        status: "error",
                        result: "WebSocket connection failed: \(error.localizedDescription)",
                        outputPath: nil,
                        logs: []
                    ))
                }
            }
        }
        receive()
        return task
    }

    private func performClean(_ endpoint: String, body: [String: Any], completion: @escaping (Result<String, Error>) -> Void) {
        var request = URLRequest(url: serverURL.appendingPathComponent("/clean/\(endpoint)"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        addAuthorization(to: &request)

        let task = session.dataTask(with: request) { [weak self] data, response, error in
            if let error = error {
                print("Clean failed: \(error)")
                completion(.failure(BackendClientError.unavailable(error.localizedDescription)))
                return
            }
            guard let self,
                  let data else {
                completion(.failure(BackendClientError.invalidResponse))
                return
            }
            do {
                let json = try self.decodeJSON(data: data, response: response as? HTTPURLResponse)
                guard let jobId = json["job_id"] as? String else {
                    throw BackendClientError.invalidResponse
                }
                completion(.success(jobId))
            } catch {
                completion(.failure(error))
            }
        }
        task.resume()
    }

    private func addAuthorization(to request: inout URLRequest) {
        if let token = UserDefaults.standard.string(forKey: ServerManager.authTokenDefaultsKey) {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
    }

    private func decodeJSON(data: Data, response: HTTPURLResponse?) throws -> [String: Any] {
        if let response, !(200..<300).contains(response.statusCode) {
            let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String
                ?? "The backend rejected the request (HTTP \(response.statusCode))."
            throw BackendClientError.server(statusCode: response.statusCode, detail: detail)
        }
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw BackendClientError.invalidResponse
        }
        return json
    }
}

struct JobDetail {
    let jobId: String
    let status: String
    let logs: [String]
    let result: String?
    let outputPath: String?
    let createdAt: String?
    let finishedAt: String?
}

struct WebSocketMessage {
    let logsUpdated: Int
    let status: String?
    let result: String?
    let outputPath: String?
    let logs: [String]
}
