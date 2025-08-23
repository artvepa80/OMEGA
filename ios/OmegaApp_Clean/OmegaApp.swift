import SwiftUI

@main
struct OmegaApp: App {
    
    init() {
        // Configure app on launch
        setupApp()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.automatic)
                .onAppear {
                    // Additional setup when app appears
                    print("🚀 OMEGA Pro AI launched successfully")
                }
        }
    }
    
    private func setupApp() {
        // Print app configuration
        print("🎯 Initializing OMEGA Pro AI...")
        
        // Validate configuration
        guard AppConfig.validateConfiguration() else {
            fatalError("❌ Invalid app configuration")
        }
        
        // Print environment details
        AppConfig.printEnvironment()
        
        print("✅ OMEGA Pro AI initialized successfully")
        print("🌐 Ready to connect to Akash Network")
    }
}