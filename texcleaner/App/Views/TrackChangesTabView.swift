import SwiftUI
import UniformTypeIdentifiers

struct TrackChangesTabView: View {
    @ObservedObject var vm: TrackChangesViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Clean LaTeX Track Changes")
                .font(.title2)
                .fontWeight(.semibold)

            GroupBox("Input File") {
                HStack {
                    TextField("Select a .tex file", text: $vm.inputPath)
                        .disabled(true)

                    Button("Browse...") {
                        selectFile()
                    }
                    .buttonStyle(.bordered)
                }
                .padding(.horizontal, 4)
            }

            HStack(alignment: .top, spacing: 12) {
                GroupBox("Cleaning Options") {
                    VStack(alignment: .leading, spacing: 10) {
                        Picker("Document version", selection: $vm.revisionChoice) {
                            ForEach(RevisionChoice.allCases) { choice in
                                Text(choice.label).tag(choice)
                            }
                        }
                        .pickerStyle(.segmented)

                        Toggle("Remove annotations and comments", isOn: $vm.removeAnnotations)

                        Text(
                            vm.revisionChoice == .new
                                ? "Accepts additions and replacements and removes deleted text."
                                : "Rejects additions and replacements and restores deleted text."
                        )
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    }
                    .padding(4)
                }
                .frame(maxWidth: .infinity, alignment: .topLeading)

                GroupBox("Output") {
                    VStack(alignment: .leading, spacing: 8) {
                        LabeledContent("Filename suffix") {
                            TextField("-cleaned", text: $vm.outputSuffix)
                                .frame(width: 160)
                        }

                        Toggle("Replace an existing output file", isOn: $vm.overwriteExisting)

                        if let outputPath = vm.outputPath {
                            let outputURL = URL(fileURLWithPath: outputPath)
                            LabeledContent("Output name") {
                                Text(outputURL.lastPathComponent)
                                    .textSelection(.enabled)
                            }
                            LabeledContent("Saved in") {
                                Text(outputURL.deletingLastPathComponent().path)
                                    .textSelection(.enabled)
                                    .lineLimit(1)
                                    .truncationMode(.middle)
                                    .help(outputURL.deletingLastPathComponent().path)
                            }
                        } else if !vm.isOutputSuffixValid {
                            Text("Enter a non-empty suffix without path separators.")
                                .font(.caption)
                                .foregroundStyle(.red)
                        }
                    }
                    .padding(4)
                }
                .frame(maxWidth: .infinity, alignment: .topLeading)
            }

            HStack {
                Button {
                    vm.clean()
                } label: {
                    Label("Detect & Clean", systemImage: "broom")
                }
                .buttonStyle(.borderedProminent)
                .frame(minWidth: 160)
                .disabled(vm.isProcessing || vm.inputPath.isEmpty || !vm.isOutputSuffixValid)

                if vm.isProcessing {
                    ProgressView()
                        .scaleEffect(0.8)
                }
            }

            if let completedOutputPath = vm.completedOutputPath {
                OutputResultView(path: completedOutputPath)
            }

            Divider()

            if !vm.logs.isEmpty {
                Text("Log Output:")
                    .font(.headline)
                    .padding(.top)

                ScrollView {
                    VStack(alignment: .leading, spacing: 2) {
                        ForEach(vm.logs.indices, id: \.self) { i in
                            Text(vm.logs[i])
                                .font(.system(.body, design: .monospaced))
                                .lineLimit(nil)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(8)
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.secondary.opacity(0.3), lineWidth: 1)
                    )
                }
                .frame(maxHeight: .infinity)
            } else {
                Spacer()
            }

            if let error = vm.errorMessage {
                HStack {
                    Text("Error: \(error)")
                        .foregroundColor(.red)
                        .font(.caption)
                    Spacer()
                    Button("Dismiss") {
                        vm.errorMessage = nil
                    }
                }
                .padding(8)
                .background(Color.red.opacity(0.1))
                .cornerRadius(6)
            }
        }
        .padding()
    }

    private func selectFile() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [UTType(filenameExtension: "tex")!]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false

        if panel.runModal() == .OK,
           let url = panel.url {
            vm.inputPath = url.path
        }
    }
}
