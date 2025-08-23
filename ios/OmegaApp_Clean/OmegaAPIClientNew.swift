import Foundation
import SwiftUI

// MARK: - Modern OMEGA API Client for Akash Network
@MainActor
class OmegaAPIClient: ObservableObject {
    @Published var isLoading = false
    @Published var error: APIError?
    @Published var predictions: [OmegaPrediction] = []
    
    private var baseURL: String = ""
    private let session: URLSession
    private let decoder = JSONDecoder()
    
    init() {
        // Configure URL session to handle self-signed certificates (Akash Network)
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 60
        
        self.session = URLSession(
            configuration: configuration,
            delegate: SSLDelegate(),
            delegateQueue: nil
        )
        
        // Configure decoder for ISO dates
        let formatter = ISO8601DateFormatter()
        decoder.dateDecodingStrategy = .iso8601
    }
    
    func configure(baseURL: String? = nil) {
        self.baseURL = baseURL ?? AppConfig.API.baseURL
        print("🚀 OMEGA API configurada para: \(self.baseURL)")
    }
    
    // MARK: - Health Check
    
    func checkHealth() async throws -> HealthResponse {
        guard let url = URL(string: "\(baseURL)/health") else {
            throw APIError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        try validateResponse(response)
        
        return try decoder.decode(HealthResponse.self, from: data)
    }
    
    // MARK: - Predictions API
    
    func generatePredictions(count: Int = 10, perfilSVI: String = "moderado") async throws -> [OmegaPrediction] {
        guard let url = URL(string: "\(baseURL)/api/v1/predictions") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = PredictionRequest(count: count, perfil_svi: perfilSVI)
        request.httpBody = try JSONEncoder().encode(requestBody)
        
        self.isLoading = true
        defer { self.isLoading = false }
        
        do {
            let (data, response) = try await session.data(for: request)
            try validateResponse(response)
            
            let predictionResponse = try decoder.decode(PredictionResponse.self, from: data)
            
            // Convert to our model format
            let predictions = predictionResponse.predictions.map { pred in
                OmegaPrediction(
                    id: UUID().uuidString,
                    numbers: pred.combination,
                    confidence: pred.score,
                    sviScore: pred.svi_score ?? 0.0,
                    source: pred.source ?? "omega_ensemble",
                    timestamp: Date(),
                    metrics: pred.metrics ?? [:]
                )
            }
            
            DispatchQueue.main.async {
                self.predictions = predictions
            }
            
            return predictions
            
        } catch {
            DispatchQueue.main.async {
                self.error = error as? APIError ?? APIError.networkError(error)
            }
            throw error
        }
    }
    
    // MARK: - Helper Methods
    
    private func validateResponse(_ response: URLResponse) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard 200...299 ~= httpResponse.statusCode else {
            throw APIError.serverError(httpResponse.statusCode)
        }
    }
}

// MARK: - SSL Delegate for Self-Signed Certificates

class SSLDelegate: NSObject, URLSessionDelegate {
    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        // Accept self-signed certificates for Akash Network
        let credential = URLCredential(trust: challenge.protectionSpace.serverTrust!)
        completionHandler(.useCredential, credential)
    }
}

// MARK: - Models

struct PredictionRequest: Codable {
    let count: Int
    let perfil_svi: String?
    
    init(count: Int, perfil_svi: String = "moderado") {
        self.count = count
        self.perfil_svi = perfil_svi
    }
}

struct PredictionResponse: Codable {
    let predictions: [RawPrediction]
    let count: Int
    let status: String
}

struct RawPrediction: Codable {
    let combination: [Int]
    let score: Double
    let svi_score: Double?
    let source: String?
    let metrics: [String: Double]?
}

struct OmegaPrediction: Identifiable, Codable {
    let id: String
    let numbers: [Int]
    let confidence: Double
    let sviScore: Double
    let source: String
    let timestamp: Date
    let metrics: [String: Double]
    
    var formattedNumbers: String {
        numbers.map { String(format: "%02d", $0) }.joined(separator: " • ")
    }
    
    var confidencePercentage: String {
        String(format: "%.1f%%", confidence * 100)
    }
    
    var sviPercentage: String {
        String(format: "%.1f%%", sviScore * 100)
    }
    
    var qualityRating: PredictionQuality {
        let averageScore = (confidence + sviScore) / 2.0
        switch averageScore {
        case 0.8...:
            return .excellent
        case 0.7..<0.8:
            return .good
        case 0.6..<0.7:
            return .average
        default:
            return .poor
        }
    }
}

enum PredictionQuality: String, CaseIterable {
    case excellent = "Excelente"
    case good = "Buena"
    case average = "Promedio"
    case poor = "Baja"
    
    var color: Color {
        switch self {
        case .excellent:
            return .green
        case .good:
            return .blue
        case .average:
            return .orange
        case .poor:
            return .red
        }
    }
    
    var icon: String {
        switch self {
        case .excellent:
            return "star.fill"
        case .good:
            return "star.leadinghalf.filled"
        case .average:
            return "star"
        case .poor:
            return "star.slash"
        }
    }
}

struct HealthResponse: Codable {
    let status: String
    let version: String?
    let service: String?
    
    var isHealthy: Bool {
        status.lowercased() == "healthy" || status.lowercased() == "operational"
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
    case omegaOffline
    
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
            return "Error de conexión: \(error.localizedDescription)"
        case .unauthorized:
            return "No autorizado"
        case .omegaOffline:
            return "OMEGA está temporalmente fuera de línea"
        }
    }
    
    var recoveryDescription: String {
        switch self {
        case .networkError, .omegaOffline:
            return "Verifica tu conexión a internet e intenta nuevamente"
        case .serverError:
            return "El servidor está experimentando problemas. Intenta más tarde"
        case .unauthorized:
            return "Por favor, inicia sesión nuevamente"
        default:
            return "Intenta nuevamente en unos momentos"
        }
    }
}