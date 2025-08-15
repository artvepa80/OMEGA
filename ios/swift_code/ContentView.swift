import SwiftUI

struct ContentView: View {
    @StateObject private var authManager = AuthManager()
    @StateObject private var apiClient = OmegaAPIClient()
    @State private var selectedTab = 0
    
    var body: some View {
        Group {
            if authManager.isAuthenticated {
                // Vista principal autenticada
                TabView(selection: $selectedTab) {
                    DashboardView()
                        .tabItem {
                            Image(systemName: "chart.bar.fill")
                            Text("Dashboard")
                        }
                        .tag(0)
                    
                    PredictionsView()
                        .tabItem {
                            Image(systemName: "brain.head.profile")
                            Text("Predicciones")
                        }
                        .tag(1)
                    
                    ResultsView()
                        .tabItem {
                            Image(systemName: "list.bullet.clipboard")
                            Text("Resultados")
                        }
                        .tag(2)
                    
                    SettingsView()
                        .tabItem {
                            Image(systemName: "gear")
                            Text("Configuración")
                        }
                        .tag(3)
                }
                .environmentObject(authManager)
                .environmentObject(apiClient)
            } else {
                // Vista de login
                LoginView()
                    .environmentObject(authManager)
                    .environmentObject(apiClient)
            }
        }
        .onAppear {
            // Configuración automática según ambiente
            print("🚀🚀🚀 OMEGA APP INICIANDO 🚀🚀🚀")
            apiClient.configure()
            print("🚀🚀🚀 CONFIGURACION COMPLETA 🚀🚀🚀")
        }
    }
}

struct DashboardView: View {
    @EnvironmentObject var apiClient: OmegaAPIClient
    @State private var systemStatus: SystemStatus?
    @State private var isLoading = true
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Header
                    HStack {
                        VStack(alignment: .leading) {
                            Text("OMEGA PRO AI")
                                .font(.largeTitle)
                                .fontWeight(.bold)
                                .foregroundColor(.primary)
                            
                            Text("Sistema Agéntico V4.0")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        // Estado del sistema
                        StatusIndicator(isHealthy: systemStatus?.isHealthy ?? false)
                    }
                    .padding()
                    
                    // Métricas principales
                    if let status = systemStatus {
                        MetricsGrid(status: status)
                    }
                    
                    // Predicciones recientes
                    RecentPredictionsCard()
                    
                    // Acciones rápidas
                    QuickActionsCard()
                }
            }
            .navigationBarHidden(true)
            .refreshable {
                await loadSystemStatus()
            }
        }
        .task {
            await loadSystemStatus()
        }
    }
    
    private func loadSystemStatus() async {
        isLoading = true
        do {
            systemStatus = try await apiClient.getSystemStatus()
        } catch {
            print("Error loading system status: \(error)")
        }
        isLoading = false
    }
}

struct PredictionsView: View {
    @EnvironmentObject var apiClient: OmegaAPIClient
    @State private var predictions: [Prediction] = []
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            List(predictions) { prediction in
                PredictionCell(prediction: prediction)
            }
            .navigationTitle("Predicciones")
            .refreshable {
                await loadPredictions()
            }
        }
        .task {
            await loadPredictions()
        }
    }
    
    private func loadPredictions() async {
        isLoading = true
        do {
            predictions = try await apiClient.getPredictions()
        } catch {
            print("Error loading predictions: \(error)")
        }
        isLoading = false
    }
}

struct ResultsView: View {
    var body: some View {
        NavigationView {
            VStack {
                Text("Resultados")
                    .font(.title)
                    .padding()
                
                Text("Próximamente...")
                    .foregroundColor(.secondary)
                
                Spacer()
            }
            .navigationTitle("Resultados")
        }
    }
}

struct SettingsView: View {
    @EnvironmentObject var authManager: AuthManager
    
    var body: some View {
        NavigationView {
            List {
                Section("Cuenta") {
                    if let user = authManager.user {
                        HStack {
                            Text("Usuario")
                            Spacer()
                            Text(user.username)
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Text("Rol")
                            Spacer()
                            Text(user.role.capitalized)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                Section("Configuración") {
                    HStack {
                        Text("Ambiente")
                        Spacer()
                        Text(AppConfig.currentEnvironment.displayName)
                            .foregroundColor(.secondary)
                    }
                }
                
                Section {
                    Button("Cerrar Sesión") {
                        Task {
                            await authManager.logout()
                        }
                    }
                    .foregroundColor(.red)
                }
            }
            .navigationTitle("Configuración")
        }
    }
}

#Preview {
    ContentView()
}