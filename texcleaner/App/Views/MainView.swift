import SwiftUI

struct MainView: View {
    @StateObject private var trackChangesVM = TrackChangesViewModel()
    @StateObject private var arxivVM = ArxivViewModel()

    var body: some View {
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
        .frame(minWidth: 760, minHeight: 620)
    }
}
