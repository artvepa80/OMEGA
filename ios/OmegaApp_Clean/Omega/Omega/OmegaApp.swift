//
//  OmegaApp.swift
//  Omega
//
//  Created by arturo velasquez on 11/08/25.
//

import SwiftUI

@main
struct OmegaApp: App {
    
    init() {
        // Configure app on launch
        setupApp()
    }
    
    var body: some Scene {
        WindowGroup {
            SimpleContentView()
                .onAppear {
                    // Additional setup when app appears
                    print("🚀 OMEGA Pro AI launched successfully")
                }
        }
    }
    
    private func setupApp() {
        // Print app configuration
        print("🎯 Initializing OMEGA Pro AI...")
        print("✅ OMEGA Pro AI initialized successfully")
        print("🌐 Ready to connect to Akash Network")
        print("🚀 API URL: https://a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online")
    }
}
