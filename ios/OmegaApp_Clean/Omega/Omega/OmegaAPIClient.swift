import Foundation
import SwiftUI

@MainActor
class OmegaAPIClient: ObservableObject {
    @Published var isLoading = false
    @Published var error: APIError?
    
    private var baseURL: String = ""
    private let networkSecurityManager = NetworkSecurityManager.shared
    private let decoder = JSONDecoder()
    
    // URLSession for non-secure requests (fallback)
    private lazy var session: URLSession = {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = AppConfig.API.requestTimeout
        configuration.timeoutIntervalForResource = AppConfig.API.resourceTimeout
        return URLSession(configuration: configuration)
    }()
    
    init() {
        // Configurar decoder para fechas ISO
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
        decoder.dateDecodingStrategy = .formatted(formatter)
    }
    
    func configure(baseURL: String? = nil) {
        self.baseURL = baseURL ?? AppConfig.API.baseURL
        print("🔧 API configurada para: \(self.baseURL)")
    }
    
    // MARK: - Auth Methods
    
    func login(username: String, password: String) async throws -> AuthResponse {
        guard let url = URL(string: "\(baseURL)\(AppConfig.API.login)") else {
            throw APIError.invalidURL
        }
        
        // Create secure request using NetworkSecurityManager
        var request = networkSecurityManager.createSecureRequest(for: url, method: .POST)
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        
        let bodyData = "username=\(username)&password=\(password)".data(using: .utf8)
        request.httpBody = bodyData
        
        do {
            // Use secure networking with SSL pinning
            let (data, response) = try await networkSecurityManager.performSecureDataTask(with: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            guard httpResponse.statusCode == 200 else {
                throw APIError.serverError(httpResponse.statusCode)
            }
            
            let authResponse = try decoder.decode(AuthResponse.self, from: data)
            return authResponse
            
        } catch let networkError as NetworkSecurityError {
            // Handle SSL/Network security errors
            AppLogger.shared.error("Network security error during login", category: .auth, error: networkError)
            throw APIError.networkError(networkError)
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
        guard let url = URL(string: "\(baseURL)\(AppConfig.API.refresh)") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = AppConfig.API.requestTimeout
        
        // Add current token to request if available
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
            
            let refreshResponse = try decoder.decode(RefreshTokenResponse.self, from: data)
            return refreshResponse
            
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
    
    func createPrediction(parameters: PredictionParameters) async throws -> Prediction {
        let url = URL(string: "\(baseURL)/predictions")!
        var request = createAuthenticatedRequest(for: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let encoder = JSONEncoder()
        request.httpBody = try encoder.encode(parameters)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(Prediction.self, from: data)
    }
    
    // MARK: - Agent Operations
    
    func startAgent() async throws -> AgentResponse {
        let url = URL(string: "\(baseURL)/agent/start")!
        var request = createAuthenticatedRequest(for: url)
        request.httpMethod = "POST"
        
        let (data, _) = try await session.data(for: request)
        return try decoder.decode(AgentResponse.self, from: data)
    }
    
    func stopAgent() async throws -> AgentResponse {
        let url = URL(string: "\(baseURL)/agent/stop")!
        var request = createAuthenticatedRequest(for: url)
        request.httpMethod = "POST"
        
        let (data, _) = try await session.data(for: request)
        return try decoder.decode(AgentResponse.self, from: data)
    }
    
    func getAgentStatus() async throws -> AgentStatus {
        let url = URL(string: "\(baseURL)/agent/status")!
        let request = createAuthenticatedRequest(for: url)
        
        let (data, _) = try await session.data(for: request)
        return try decoder.decode(AgentStatus.self, from: data)
    }
    
    // MARK: - Training
    
    func trainModel(modelType: String, parameters: TrainingParameters) async throws -> TrainingResponse {
        let url = URL(string: "\(baseURL)/train/\(modelType)")!
        var request = createAuthenticatedRequest(for: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let encoder = JSONEncoder()
        request.httpBody = try encoder.encode(parameters)
        
        let (data, _) = try await session.data(for: request)
        return try decoder.decode(TrainingResponse.self, from: data)
    }
    
    // MARK: - Helper Methods
    
    private func createAuthenticatedRequest(for url: URL) -> URLRequest {
        var request = URLRequest(url: url)
        
        if let token = AuthManager.shared.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        return request
    }
    
    private func handleHTTPResponse(_ response: URLResponse) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard 200...299 ~= httpResponse.statusCode else {
            throw APIError.serverError(httpResponse.statusCode)
        }
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
    let message: String?  // Agregar campo opcional
    
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
    let parameters: [String: AnyCodable]?
    
    init(
        id: String = UUID().uuidString, 
        timestamp: Date = Date(), 
        numbers: [Int], 
        confidence: Double, 
        modelUsed: String,
        parameters: [String: AnyCodable]? = nil
    ) {
        self.id = id
        self.timestamp = timestamp
        self.numbers = numbers
        self.confidence = confidence
        self.modelUsed = modelUsed
        self.parameters = parameters
    }
    
    private enum CodingKeys: String, CodingKey {
        case id, timestamp, numbers, confidence
        case modelUsed = "model_used"
        case parameters
    }
}

struct PredictionsResponse: Codable {
    let predictions: [Prediction]
    let total: Int
    let page: Int
    let limit: Int
}

struct PredictionParameters: Codable {
    let modelType: String
    let customParams: [String: AnyCodable]?
    
    init(modelType: String, customParams: [String: AnyCodable]? = nil) {
        self.modelType = modelType
        self.customParams = customParams
    }
    
    private enum CodingKeys: String, CodingKey {
        case modelType = "model_type"
        case customParams = "custom_params"
    }
}

struct AgentResponse: Codable {
    let success: Bool
    let message: String
    let agentStatus: String?
    
    private enum CodingKeys: String, CodingKey {
        case success, message
        case agentStatus = "agent_status"
    }
}

struct AgentStatus: Codable {
    let isRunning: Bool
    let currentTask: String?
    let lastExecution: String?
    let performance: AgentPerformance
    
    private enum CodingKeys: String, CodingKey {
        case isRunning = "is_running"
        case currentTask = "current_task"
        case lastExecution = "last_execution"
        case performance
    }
}

struct AgentPerformance: Codable {
    let successRate: Double
    let averageExecutionTime: Double
    let totalExecutions: Int
    
    private enum CodingKeys: String, CodingKey {
        case successRate = "success_rate"
        case averageExecutionTime = "average_execution_time"
        case totalExecutions = "total_executions"
    }
}

struct TrainingParameters: Codable {
    let epochs: Int?
    let learningRate: Double?
    let batchSize: Int?
    let validationSplit: Double?
    
    private enum CodingKeys: String, CodingKey {
        case epochs
        case learningRate = "learning_rate"
        case batchSize = "batch_size"
        case validationSplit = "validation_split"
    }
}

struct TrainingResponse: Codable {
    let success: Bool
    let message: String
    let trainingId: String?
    let estimatedCompletionTime: String?
    
    private enum CodingKeys: String, CodingKey {
        case success, message
        case trainingId = "training_id"
        case estimatedCompletionTime = "estimated_completion_time"
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

// MARK: - Helper for Any Codable

struct AnyCodable: Codable {
    let value: Any
    
    init<T>(_ value: T?) {
        self.value = value ?? ()
    }
}

extension AnyCodable {
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dictionary = try? container.decode([String: AnyCodable].self) {
            value = dictionary.mapValues { $0.value }
        } else {
            value = ()
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        switch value {
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dictionary as [String: Any]:
            try container.encode(dictionary.mapValues { AnyCodable($0) })
        default:
            try container.encodeNil()
        }
    }
}

// MARK: - Token Refresh

struct RefreshTokenRequest: Codable {
    let refreshToken: String
    
    private enum CodingKeys: String, CodingKey {
        case refreshToken = "refresh_token"
    }
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
