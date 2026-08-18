import SwiftUI

@main
struct TeXCleanerApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            MainView()
        }
        .commands {
            CommandGroup(replacing: .appInfo) {
                Button {
                    NSApp.orderFrontStandardAboutPanel()
                } label: {
                    Text("About TeXCleaner")
                }
            }
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var serverProcess: Process?

    func applicationDidFinishLaunching(_ notification: Notification) {
        ServerManager.shared.start()
    }

    func applicationWillTerminate(_ notification: Notification) {
        ServerManager.shared.stop()
    }
}
