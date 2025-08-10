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
            apiClient.configure(baseURL: "http://127.0.0.1:8000")
            authManager.checkAuthStatus()
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

struct StatusIndicator: View {
    let isHealthy: Bool
    
    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(isHealthy ? Color.green : Color.red)
                .frame(width: 12, height: 12)
            
            Text(isHealthy ? "Activo" : "Error")
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(
            Capsule()
                .fill(Color(.systemGray6))
        )
    }
}

struct MetricsGrid: View {
    let status: SystemStatus
    
    var body: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 16) {
            MetricCard(
                title: "Predicciones",
                value: "\(status.statistics.totalPredictions)",
                icon: "brain.head.profile",
                color: .blue
            )
            
            MetricCard(
                title: "Precisión",
                value: "\(Int(status.performance * 100))%",
                icon: "target",
                color: .green
            )
            
            MetricCard(
                title: "Uptime",
                value: status.uptime.formatted,
                icon: "clock",
                color: .orange
            )
            
            MetricCard(
                title: "Modo",
                value: status.currentMode.capitalized,
                icon: "gear",
                color: .purple
            )
        }
        .padding(.horizontal)
    }
}

struct MetricCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.title2)
                
                Spacer()
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(value)
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text(title)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
        )
    }
}

struct RecentPredictionsCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Predicciones Recientes")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Button("Ver todas") {
                    // Navegar a vista completa
                }
                .font(.caption)
                .foregroundColor(.blue)
            }
            
            // Lista de predicciones (placeholder)
            VStack(spacing: 12) {
                PredictionRow(
                    prediction: "Predicción #001",
                    confidence: 0.85,
                    timestamp: Date()
                )
                
                PredictionRow(
                    prediction: "Predicción #002",
                    confidence: 0.92,
                    timestamp: Date().addingTimeInterval(-3600)
                )
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
        )
        .padding(.horizontal)
    }
}

struct PredictionRow: View {
    let prediction: String
    let confidence: Double
    let timestamp: Date
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(prediction)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(timestamp.formatted(date: .omitted, time: .shortened))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("\(Int(confidence * 100))%")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(confidence > 0.8 ? .green : .orange)
                
                Text("confianza")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 8)
    }
}

struct QuickActionsCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Acciones Rápidas")
                .font(.headline)
                .fontWeight(.semibold)
            
            HStack(spacing: 16) {
                QuickActionButton(
                    title: "Nueva Predicción",
                    icon: "plus.circle.fill",
                    color: .blue
                ) {
                    // Acción nueva predicción
                }
                
                QuickActionButton(
                    title: "Entrenar Modelo",
                    icon: "brain.head.profile",
                    color: .green
                ) {
                    // Acción entrenar
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
        )
        .padding(.horizontal)
    }
}

struct QuickActionButton: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)
                
                Text(title)
                    .font(.caption)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.primary)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color(.systemGray6))
            )
        }
    }
}

#Preview {
    ContentView()
}
