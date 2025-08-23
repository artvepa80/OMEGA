import Foundation

// MARK: - JWT Decoder
/// Simple JWT decoder for OMEGA iOS app
struct JWTDecoder {
    
    static func decode(_ token: String) throws -> JWTToken {
        let components = token.components(separatedBy: ".")
        guard components.count == 3 else {
            throw JWTError.invalidFormat
        }
        
        // Decode payload (second component)
        let payload = components[1]
        guard let payloadData = base64UrlDecode(payload),
              let json = try? JSONSerialization.jsonObject(with: payloadData) as? [String: Any] else {
            throw JWTError.invalidPayload
        }
        
        return JWTToken(payload: json)
    }
    
    private static func base64UrlDecode(_ base64Url: String) -> Data? {
        var base64 = base64Url
            .replacingOccurrences(of: "-", with: "+")
            .replacingOccurrences(of: "_", with: "/")
        
        let length = Double(base64.lengthOfBytes(using: String.Encoding.utf8))
        let requiredLength = 4 * ceil(length / 4.0)
        let paddingLength = requiredLength - length
        
        if paddingLength > 0 {
            let padding = String(repeating: "=", count: Int(paddingLength))
            base64 += padding
        }
        
        return Data(base64Encoded: base64)
    }
}

// MARK: - JWT Token

struct JWTToken {
    private let payload: [String: Any]
    
    init(payload: [String: Any]) {
        self.payload = payload
    }
    
    var userID: String? {
        return payload["sub"] as? String ?? payload["user_id"] as? String
    }
    
    var roles: [String] {
        if let roles = payload["roles"] as? [String] {
            return roles
        } else if let role = payload["role"] as? String {
            return [role]
        }
        return ["user"]
    }
    
    var expirationDate: Date? {
        guard let exp = payload["exp"] as? TimeInterval else {
            return nil
        }
        return Date(timeIntervalSince1970: exp)
    }
    
    var issuedAt: Date? {
        guard let iat = payload["iat"] as? TimeInterval else {
            return nil
        }
        return Date(timeIntervalSince1970: iat)
    }
    
    var issuer: String? {
        return payload["iss"] as? String
    }
    
    var audience: String? {
        return payload["aud"] as? String
    }
}

// MARK: - JWT Errors

enum JWTError: LocalizedError {
    case invalidFormat
    case invalidPayload
    case expired
    case notYetValid
    
    var errorDescription: String? {
        switch self {
        case .invalidFormat:
            return "JWT has invalid format"
        case .invalidPayload:
            return "JWT payload is invalid"
        case .expired:
            return "JWT token has expired"
        case .notYetValid:
            return "JWT token is not yet valid"
        }
    }
}