import SwiftUI

struct ArxivTabView: View {
    @ObservedObject var vm: ArxivViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Clean for arXiv Submission")
                .font(.title2)
                .fontWeight(.semibold)

            GroupBox("Project Folder") {
                HStack {
                    TextField("Select a project folder", text: $vm.folderPath)
                        .disabled(true)

                    Button("Browse...") {
                        selectFolder()
                    }
                    .buttonStyle(.bordered)
                }
                .padding(.horizontal, 4)
            }

            HStack(alignment: .top, spacing: 12) {
                GroupBox("Graphics") {
                    VStack(alignment: .leading, spacing: 10) {
                        Toggle("Resize raster images", isOn: $vm.resizeImages)

                        LabeledContent("Maximum image dimension") {
                            HStack(spacing: 6) {
                                TextField("Pixels", value: $vm.imageSize, format: .number)
                                    .frame(width: 70)
                                    .multilineTextAlignment(.trailing)
                                Text("px")
                                    .foregroundStyle(.secondary)
                                Stepper("", value: $vm.imageSize, in: 100...10000, step: 100)
                                    .labelsHidden()
                            }
                        }
                        .disabled(!vm.resizeImages)

                        Toggle("Compress PDF graphics", isOn: $vm.compressPDF)

                        LabeledContent("PDF image resolution") {
                            HStack(spacing: 6) {
                                TextField("DPI", value: $vm.pdfResolution, format: .number)
                                    .frame(width: 70)
                                    .multilineTextAlignment(.trailing)
                                Text("dpi")
                                    .foregroundStyle(.secondary)
                                Stepper("", value: $vm.pdfResolution, in: 72...2400, step: 25)
                                    .labelsHidden()
                            }
                        }
                        .disabled(!vm.compressPDF)
                    }
                    .padding(4)
                }
                .frame(maxWidth: .infinity, alignment: .topLeading)

                GroupBox("Cleaning and Output") {
                    VStack(alignment: .leading, spacing: 8) {
                        Toggle("Keep BibTeX (.bib) files", isOn: $vm.keepBib)
                        Toggle("Show detailed cleaner output", isOn: $vm.verbose)

                        LabeledContent("Folder suffix") {
                            TextField("-cleaned", text: $vm.outputSuffix)
                                .frame(width: 160)
                        }

                        Toggle("Replace an existing output folder", isOn: $vm.overwriteExisting)

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
                    Label("Clean for arXiv", systemImage: "arrow.up.doc")
                }
                .buttonStyle(.borderedProminent)
                .frame(minWidth: 160)
                .disabled(
                    vm.isProcessing
                        || vm.folderPath.isEmpty
                        || !vm.isOutputSuffixValid
                        || (vm.resizeImages && !(1...10000).contains(vm.imageSize))
                        || (vm.compressPDF && !(1...2400).contains(vm.pdfResolution))
                )

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

    private func selectFolder() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = true
        panel.canChooseFiles = false

        if panel.runModal() == .OK,
           let url = panel.url {
            vm.folderPath = url.path
        }
    }
}
