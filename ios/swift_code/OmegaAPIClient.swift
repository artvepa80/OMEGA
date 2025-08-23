import Foundation
import SwiftUI

@MainActor
class OmegaAPIClient: ObservableObject {
    @Published var isLoading = false
    @Published var error: APIError?
    
    private var baseURL: String = "http://127.0.0.1:8001"
    private let decoder = JSONDecoder()
    
    private lazy var session: URLSession = {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 60
        return URLSession(configuration: configuration)
    }()
    
    init() {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
        decoder.dateDecodingStrategy = .formatted(formatter)
    }
    
    func configure(baseURL: String? = nil) {
        self.baseURL = baseURL ?? "http://127.0.0.1:8001"
        print("🔧 API configurada para: \(self.baseURL)")
    }
    
    // MARK: - Auth Methods
    
    func login(username: String, password: String) async throws -> AuthResponse {
        guard let url = URL(string: "\(baseURL)/auth/login") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        
        let bodyData = "username=\(username)&password=\(password)".data(using: .utf8)
        request.httpBody = bodyData
        
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            guard httpResponse.statusCode == 200 else {
                throw APIError.serverError(httpResponse.statusCode)
            }
            
            let authResponse = try decoder.decode(AuthResponse.self, from: data)
            return authResponse
            
        } catch {
            if error is URLError {
                throw APIError.networkError(error)
            } else if error is DecodingError {
                throw APIError.decodingError(error)
            } else {
                throw error
            }
        }
    }
    
    func refreshToken() async throws -> RefreshTokenResponse {
        guard let url = URL(string: "\(baseURL)/auth/refresh") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let token = AuthManager.shared.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            guard httpResponse.statusCode == 200 else {
                if httpResponse.statusCode == 401 {
                    throw APIError.unauthorized
                }
                throw APIError.serverError(httpResponse.statusCode)
            }
            
            return try decoder.decode(RefreshTokenResponse.self, from: data)
            
        } catch {
            if error is URLError {
                throw APIError.networkError(error)
            } else if error is DecodingError {
                throw APIError.decodingError(error)
            } else {
                throw error
            }
        }
    }
    
    // MARK: - System Status
    
    func getSystemStatus() async throws -> SystemStatus {
        let url = URL(string: "\(baseURL)/status")!
        let (data, _) = try await session.data(from: url)
        
        let response = try decoder.decode(StatusResponse.self, from: data)
        return response.status
    }
    
    func getHealthCheck() async throws -> HealthResponse {
        let url = URL(string: "\(baseURL)/health")!
        let (data, _) = try await session.data(from: url)
        
        return try decoder.decode(HealthResponse.self, from: data)
    }
    
    // MARK: - Predictions
    
    func getPredictions(limit: Int = 10) async throws -> [Prediction] {
        let url = URL(string: "\(baseURL)/predictions?limit=\(limit)")!
        let request = createAuthenticatedRequest(for: url)
        
        let (data, _) = try await session.data(for: request)
        let response = try decoder.decode(PredictionsResponse.self, from: data)
        return response.predictions
    }
    
    // MARK: - Helper Methods
    
    private func createAuthenticatedRequest(for url: URL) -> URLRequest {
        var request = URLRequest(url: url)
        
        if let token = AuthManager.shared.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        return request
    }
}

// MARK: - Models

struct StatusResponse: Codable {
    let ok: Bool
    let status: SystemStatus
}

struct SystemStatus: Codable {
    let systemVersion: String
    let pipelineVersion: String
    let agenticVersion: String
    let currentMode: String
    let systemHealth: SystemHealth
    let uptime: Uptime
    let statistics: Statistics
    let performance: Double
    let configuration: Configuration
    
    var isHealthy: Bool {
        systemHealth.pipeline && systemHealth.agentic
    }
    
    private enum CodingKeys: String, CodingKey {
        case systemVersion = "system_version"
        case pipelineVersion = "pipeline_version"
        case agenticVersion = "agentic_version"
        case currentMode = "current_mode"
        case systemHealth = "system_health"
        case uptime, statistics, performance, configuration
    }
}

struct SystemHealth: Codable {
    let pipeline: Bool
    let agentic: Bool
}

struct Uptime: Codable {
    let days: Int
    let hours: Int
    let totalSeconds: Double
    
    var formatted: String {
        if days > 0 {
            return "\(days)d \(hours)h"
        } else if hours > 0 {
            return "\(hours)h"
        } else {
            let minutes = Int(totalSeconds / 60)
            return "\(minutes)m"
        }
    }
    
    private enum CodingKeys: String, CodingKey {
        case days, hours
        case totalSeconds = "total_seconds"
    }
}

struct Statistics: Codable {
    let pipelinePredictions: Int
    let agenticPredictions: Int
    let hybridPredictions: Int
    let adaptiveDecisions: Int
    let systemSwitches: Int
    let totalPredictions: Int
    let startTime: String
    
    private enum CodingKeys: String, CodingKey {
        case pipelinePredictions = "pipeline_predictions"
        case agenticPredictions = "agentic_predictions"
        case hybridPredictions = "hybrid_predictions"
        case adaptiveDecisions = "adaptive_decisions"
        case systemSwitches = "system_switches"
        case totalPredictions = "total_predictions"
        case startTime = "start_time"
    }
}

struct Configuration: Codable {
    let defaultMode: String
    let pipelineConfig: PipelineConfig
    let agenticConfig: AgenticConfig
    
    private enum CodingKeys: String, CodingKey {
        case defaultMode = "default_mode"
        case pipelineConfig = "pipeline_config"
        case agenticConfig = "agentic_config"
    }
}

struct PipelineConfig: Codable {
    let dataPath: String
    let sviProfile: String
    let topN: Int
    let enableModels: [String]
    let exportFormats: [String]
    let retrain: Bool
    let evaluate: Bool
    let backtest: Bool
    
    private enum CodingKeys: String, CodingKey {
        case dataPath = "data_path"
        case sviProfile = "svi_profile"
        case topN = "top_n"
        case enableModels = "enable_models"
        case exportFormats = "export_formats"
        case retrain, evaluate, backtest
    }
}

struct AgenticConfig: Codable {
    let enableAutonomousAgent: Bool
    let enableApiServer: Bool
    let enablePredictions: Bool
    let agentScheduleSeconds: Int
    let maxExperimentsPerCycle: Int
    
    private enum CodingKeys: String, CodingKey {
        case enableAutonomousAgent = "enable_autonomous_agent"
        case enableApiServer = "enable_api_server"
        case enablePredictions = "enable_predictions"
        case agentScheduleSeconds = "agent_schedule_seconds"
        case maxExperimentsPerCycle = "max_experiments_per_cycle"
    }
}

struct HealthResponse: Codable {
    let status: String
    let timestamp: String
    let version: String
    let uptimeSeconds: Double
    
    private enum CodingKeys: String, CodingKey {
        case status, timestamp, version
        case uptimeSeconds = "uptime_seconds"
    }
}

struct AuthResponse: Codable {
    let accessToken: String
    let tokenType: String
    let message: String?
    
    private enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
        case message = "message"
    }
}

struct Prediction: Codable, Identifiable {
    let id: String
    let timestamp: Date
    let numbers: [Int]
    let confidence: Double
    let modelUsed: String
    
    init(
        id: String = UUID().uuidString,
        timestamp: Date = Date(),
        numbers: [Int],
        confidence: Double,
        modelUsed: String
    ) {
        self.id = id
        self.timestamp = timestamp
        self.numbers = numbers
        self.confidence = confidence
        self.modelUsed = modelUsed
    }
    
    private enum CodingKeys: String, CodingKey {
        case id, timestamp, numbers, confidence
        case modelUsed = "model_used"
    }
}

struct PredictionsResponse: Codable {
    let predictions: [Prediction]
    let total: Int
    let page: Int
    let limit: Int
}

struct RefreshTokenResponse: Codable {
    let accessToken: String
    let tokenType: String
    let expiresIn: Int?
    
    private enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
        case expiresIn = "expires_in"
    }
}

// MARK: - Error Types

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case noData
    case decodingError(Error)
    case serverError(Int)
    case networkError(Error)
    case unauthorized
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "URL inválida"
        case .invalidResponse:
            return "Respuesta inválida del servidor"
        case .noData:
            return "No se recibieron datos"
        case .decodingError(let error):
            return "Error decodificando datos: \(error.localizedDescription)"
        case .serverError(let code):
            return "Error del servidor: \(code)"
        case .networkError(let error):
            return "Error de red: \(error.localizedDescription)"
        case .unauthorized:
            return "No autorizado"
        }
    }
}

// MARK: - UI Components

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

struct PredictionCell: View {
    let prediction: Prediction
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Predicción \(prediction.id)")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("\(Int(prediction.confidence * 100))%")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(prediction.confidence > 0.8 ? .green : .orange)
            }
            
            Text("Números: \(prediction.numbers.map { String($0) }.joined(separator: ", "))")
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            HStack {
                Text("Modelo: \(prediction.modelUsed)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(prediction.timestamp.formatted(date: .abbreviated, time: .shortened))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
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