import Foundation

class BackendClient: ObservableObject {
    static let shared = BackendClient()

    private let serverURL = URL(string: "http://127.0.0.1:8765")!
    private let session: URLSession

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        session = URLSession(configuration: config)
    }

    func detectModule(at inputPath: String, completion: @escaping (String?) -> Void) {
        var components = URLComponents(url: serverURL.appendingPathComponent("/detect"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "input_path", value: inputPath)]

        let request = URLRequest(url: components.url!)
        let task = session.dataTask(with: request) { data, _, error in
            if let error = error {
                print("Detect failed: \(error)")
                completion(nil)
                return
            }
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let detected = json["detected"] as? String else {
                completion(nil)
                return
            }
            completion(detected)
        }
        task.resume()
    }

    func trackChanges(
        at inputPath: String,
        keepVersion: RevisionChoice,
        removeAnnotations: Bool,
        outputSuffix: String,
        overwrite: Bool,
        completion: @escaping (String) -> Void
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
        completion: @escaping (String) -> Void
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
        completion: @escaping (String) -> Void
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
        let request = URLRequest(url: serverURL.appendingPathComponent("/jobs/\(jobId)"))
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
        let task = session.webSocketTask(with: url)

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
                case .failure:
                    break
                }
            }
        }
        receive()
        return task
    }

    private func performClean(_ endpoint: String, body: [String: Any], completion: @escaping (String) -> Void) {
        var request = URLRequest(url: serverURL.appendingPathComponent("/clean/\(endpoint)"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        let task = session.dataTask(with: request) { data, _, error in
            if let error = error {
                print("Clean failed: \(error)")
                completion("")
                return
            }
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let jobId = json["job_id"] as? String else {
                completion("")
                return
            }
            completion(jobId)
        }
        task.resume()
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
