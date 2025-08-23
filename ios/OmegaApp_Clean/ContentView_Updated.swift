import SwiftUI

struct ContentView: View {
    @StateObject private var apiClient = OmegaAPIClient()
    @State private var selectedTab = 0
    @State private var showingOnboarding = false
    
    var body: some View {
        TabView(selection: $selectedTab) {
            // Main Predictions View
            ModernPredictionsView()
                .tabItem {
                    Image(systemName: "brain.head.profile")
                    Text("Predicciones")
                }
                .tag(0)
            
            // Results History (if needed)
            HistoryView()
                .tabItem {
                    Image(systemName: "clock.fill")
                    Text("Historial")
                }
                .tag(1)
            
            // System Status
            SystemStatusView()
                .tabItem {
                    Image(systemName: "chart.line.uptrend.xyaxis")
                    Text("Estado")
                }
                .tag(2)
            
            // Settings
            AppSettingsView()
                .tabItem {
                    Image(systemName: "gearshape.fill")
                    Text("Ajustes")
                }
                .tag(3)
        }
        .accentColor(.blue)
        .onAppear {
            setupApp()
        }
        .sheet(isPresented: $showingOnboarding) {
            OnboardingView()
        }
    }
    
    private func setupApp() {
        // Configure API client
        apiClient.configure()
        
        // Check if first launch
        if !UserDefaults.standard.bool(forKey: "hasLaunchedBefore") {
            showingOnboarding = true
            UserDefaults.standard.set(true, forKey: "hasLaunchedBefore")
        }
        
        // Print configuration for debugging
        AppConfig.printEnvironment()
    }
}

// MARK: - History View

struct HistoryView: View {
    @StateObject private var apiClient = OmegaAPIClient()
    
    var body: some View {
        NavigationView {
            VStack {
                if apiClient.predictions.isEmpty {
                    ContentUnavailableView(
                        "Sin Historial",
                        systemImage: "clock",
                        description: Text("Las predicciones generadas aparecerán aquí")
                    )
                } else {
                    List {
                        ForEach(Array(apiClient.predictions.enumerated()), id: \.element.id) { index, prediction in
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Text("Predicción #\(index + 1)")
                                        .font(.headline)
                                    
                                    Spacer()
                                    
                                    Text(prediction.timestamp, style: .time)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                
                                Text(prediction.formattedNumbers)
                                    .font(.title2)
                                    .fontWeight(.bold)
                                
                                HStack {
                                    Text("Confianza: \(prediction.confidencePercentage)")
                                        .font(.caption)
                                        .foregroundColor(.blue)
                                    
                                    Spacer()
                                    
                                    Text(prediction.qualityRating.rawValue)
                                        .font(.caption)
                                        .foregroundColor(prediction.qualityRating.color)
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            }
            .navigationTitle("Historial")
        }
    }
}

// MARK: - System Status View

struct SystemStatusView: View {
    @StateObject private var apiClient = OmegaAPIClient()
    @State private var systemHealth: HealthResponse?
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Connection Status Card
                VStack(spacing: 16) {
                    HStack {
                        Image(systemName: systemHealth?.isHealthy == true ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                            .font(.title)
                            .foregroundColor(systemHealth?.isHealthy == true ? .green : .orange)
                        
                        VStack(alignment: .leading) {
                            Text("Estado del Sistema")
                                .font(.headline)
                            
                            Text(systemHealth?.status ?? "Verificando...")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                    }
                    
                    Divider()
                    
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Servidor:")
                                .fontWeight(.medium)
                            Spacer()
                            Text("Akash Network")
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Text("Versión:")
                                .fontWeight(.medium)
                            Spacer()
                            Text(systemHealth?.version ?? "N/A")
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Text("Servicio:")
                                .fontWeight(.medium)
                            Spacer()
                            Text(systemHealth?.service ?? "OMEGA Pro AI")
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .padding()
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
                
                // System Info
                VStack(alignment: .leading, spacing: 16) {
                    Text("Información del Sistema")
                        .font(.headline)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        InfoRow(title: "App Versión", value: AppConfig.App.version)
                        InfoRow(title: "Build", value: AppConfig.App.buildNumber)
                        InfoRow(title: "Entorno", value: AppConfig.currentEnvironment.rawValue.capitalized)
                        InfoRow(title: "API Base", value: AppConfig.API.baseURL)
                    }
                }
                .padding()
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
                
                // Refresh Button
                Button {
                    checkSystemHealth()
                } label: {
                    HStack {
                        if isLoading {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "arrow.clockwise")
                        }
                        
                        Text("Actualizar Estado")
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(.blue)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                .disabled(isLoading)
                
                Spacer()
            }
            .padding()
            .navigationTitle("Estado del Sistema")
            .onAppear {
                apiClient.configure()
                checkSystemHealth()
            }
        }
    }
    
    private func checkSystemHealth() {
        isLoading = true
        
        Task {
            do {
                let health = try await apiClient.checkHealth()
                await MainActor.run {
                    systemHealth = health
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    systemHealth = nil
                    isLoading = false
                }
                print("Health check failed: \(error)")
            }
        }
    }
}

struct InfoRow: View {
    let title: String
    let value: String
    
    var body: some View {
        HStack {
            Text(title)
                .fontWeight(.medium)
            Spacer()
            Text(value)
                .foregroundColor(.secondary)
                .font(.system(.body, design: .monospaced))
        }
    }
}

// MARK: - App Settings View

struct AppSettingsView: View {
    @AppStorage("notifications_enabled") private var notificationsEnabled = true
    @AppStorage("haptics_enabled") private var hapticsEnabled = true
    @AppStorage("dark_mode_enabled") private var darkModeEnabled = false
    
    var body: some View {
        NavigationView {
            Form {
                Section("General") {
                    HStack {
                        Image(systemName: "bell.fill")
                            .foregroundColor(.blue)
                            .frame(width: 20)
                        
                        Toggle("Notificaciones", isOn: $notificationsEnabled)
                    }
                    
                    HStack {
                        Image(systemName: "hand.tap.fill")
                            .foregroundColor(.orange)
                            .frame(width: 20)
                        
                        Toggle("Haptics", isOn: $hapticsEnabled)
                    }
                    
                    HStack {
                        Image(systemName: "moon.fill")
                            .foregroundColor(.purple)
                            .frame(width: 20)
                        
                        Toggle("Modo Oscuro", isOn: $darkModeEnabled)
                    }
                }
                
                Section("Acerca de") {
                    HStack {
                        Text("Versión")
                        Spacer()
                        Text(AppConfig.App.version)
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("Build")
                        Spacer()
                        Text(AppConfig.App.buildNumber)
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("Sistema")
                        Spacer()
                        Text("OMEGA Pro AI v4.0")
                            .foregroundColor(.secondary)
                    }
                }
                
                Section("Soporte") {
                    Link(destination: URL(string: "https://github.com/omega-pro-ai")!) {
                        HStack {
                            Image(systemName: "questionmark.circle")
                                .foregroundColor(.blue)
                            Text("Ayuda y Soporte")
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .foregroundColor(.secondary)
                                .font(.caption)
                        }
                    }
                }
            }
            .navigationTitle("Ajustes")
        }
    }
}

// MARK: - Onboarding View

struct OnboardingView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack(spacing: 32) {
                Spacer()
                
                // Logo/Icon
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 80))
                    .foregroundColor(.blue)
                
                VStack(spacing: 16) {
                    Text("¡Bienvenido a OMEGA Pro AI!")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .multilineTextAlignment(.center)
                    
                    Text("Sistema avanzado de predicción basado en análisis estadístico y ensemble de modelos de IA")
                        .font(.title3)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }
                
                VStack(alignment: .leading, spacing: 16) {
                    FeatureRow(icon: "chart.line.uptrend.xyaxis", title: "Análisis Estadístico", description: "Basado en datos históricos reales")
                    FeatureRow(icon: "cpu", title: "Modelos de IA", description: "Ensemble de LSTM, Transformer y más")
                    FeatureRow(icon: "cloud", title: "Cloud Descentralizada", description: "Ejecutándose en Akash Network")
                }
                
                Spacer()
                
                Button {
                    dismiss()
                } label: {
                    Text("Comenzar")
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(.blue)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                }
            }
            .padding(32)
            .navigationBarHidden(true)
        }
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String
    
    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.blue)
                .frame(width: 30)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
    }
}

// MARK: - Preview

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}