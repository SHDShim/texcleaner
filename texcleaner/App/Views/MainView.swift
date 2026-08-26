import SwiftUI

struct MainView: View {
    @StateObject private var trackChangesVM = TrackChangesViewModel()
    @StateObject private var arxivVM = ArxivViewModel()
    @ObservedObject private var serverManager = ServerManager.shared

    var body: some View {
        VStack(spacing: 0) {
            if let launchError = serverManager.launchError {
                Label(launchError, systemImage: "exclamationmark.triangle")
                    .foregroundStyle(.red)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
                    .padding(.vertical, 8)
                    .background(Color.red.opacity(0.1))
            }

            TabView {
                TrackChangesTabView(vm: trackChangesVM)
                    .tabItem {
                        Label("Track Changes", systemImage: "doc.plugtrip")
                    }

                ArxivTabView(vm: arxivVM)
                    .tabItem {
                        Label("arXiv", systemImage: "doc.badge.cloud")
                    }
            }
        }
        .frame(minWidth: 760, minHeight: 620)
    }
}
