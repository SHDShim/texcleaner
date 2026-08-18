import AppKit
import SwiftUI

struct OutputResultView: View {
    let path: String

    private var outputURL: URL {
        URL(fileURLWithPath: path)
    }

    var body: some View {
        GroupBox("Output Created") {
            VStack(alignment: .leading, spacing: 8) {
                Label(outputURL.lastPathComponent, systemImage: outputIcon)
                    .font(.headline)

                LabeledContent("Location") {
                    Text(outputURL.deletingLastPathComponent().path)
                        .textSelection(.enabled)
                        .lineLimit(1)
                        .truncationMode(.middle)
                        .help(outputURL.deletingLastPathComponent().path)
                }

                LabeledContent("Full path") {
                    Text(path)
                        .textSelection(.enabled)
                        .lineLimit(1)
                        .truncationMode(.middle)
                        .help(path)
                }

                HStack {
                    Button {
                        NSWorkspace.shared.activateFileViewerSelecting([outputURL])
                    } label: {
                        Label("Show in Finder", systemImage: "folder")
                    }

                    Button {
                        let pasteboard = NSPasteboard.general
                        pasteboard.clearContents()
                        pasteboard.setString(path, forType: .string)
                    } label: {
                        Label("Copy Path", systemImage: "doc.on.doc")
                    }
                }
            }
            .padding(4)
        }
    }

    private var outputIcon: String {
        var isDirectory: ObjCBool = false
        FileManager.default.fileExists(atPath: path, isDirectory: &isDirectory)
        return isDirectory.boolValue ? "folder.fill" : "doc.fill"
    }
}
