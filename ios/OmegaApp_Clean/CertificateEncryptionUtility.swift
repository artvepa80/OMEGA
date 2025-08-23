import Foundation
import Security
import CryptoKit
import CommonCrypto

// MARK: - Certificate Encryption Utility
/// Utility for encrypting and managing SSL certificates securely
class CertificateEncryptionUtility {
    
    // MARK: - Encryption Configuration
    private static let encryptionKeyDerivation = "OmegaAppCertEncryptionKey2024"
    private static let keyDerivationSalt = "OmegaCertSalt2024"
    private static let keyIterations: UInt32 = 100_000
    
    // MARK: - Key Generation
    private static func generateEncryptionKey() -> SymmetricKey {
        let keyData = encryptionKeyDerivation.data(using: .utf8)!
        let saltData = keyDerivationSalt.data(using: .utf8)!
        
        var derivedKey = Data(count: 32) // 256 bits for AES-256
        
        let result = derivedKey.withUnsafeMutableBytes { derivedKeyBytes in
            keyData.withUnsafeBytes { keyBytes in
                saltData.withUnsafeBytes { saltBytes in
                    CCKeyDerivationPBKDF(
                        CCPBKDFAlgorithm(kCCPBKDF2),
                        keyBytes.bindMemory(to: Int8.self).baseAddress,
                        keyData.count,
                        saltBytes.bindMemory(to: UInt8.self).baseAddress,
                        saltData.count,
                        CCPseudoRandomAlgorithm(kCCPRFHmacAlgSHA256),
                        keyIterations,
                        derivedKeyBytes.bindMemory(to: UInt8.self).baseAddress,
                        32
                    )
                }
            }
        }
        
        guard result == kCCSuccess else {
            fatalError("Key derivation failed")
        }
        
        return SymmetricKey(data: derivedKey)
    }
    
    // MARK: - Certificate Encryption
    static func encryptCertificate(_ certificateData: Data) throws -> Data {
        let key = generateEncryptionKey()
        
        let sealedBox = try AES.GCM.seal(certificateData, using: key)
        guard let combined = sealedBox.combined else {
            throw CertificateEncryptionError.encryptionFailed
        }
        
        return combined
    }
    
    static func decryptCertificate(_ encryptedData: Data) throws -> Data {
        let key = generateEncryptionKey()
        
        let sealedBox = try AES.GCM.SealedBox(combined: encryptedData)
        return try AES.GCM.open(sealedBox, using: key)
    }
    
    // MARK: - Certificate Hash Management
    static func encryptCertificateHash(_ hash: String) throws -> Data {
        guard let hashData = hash.data(using: .utf8) else {
            throw CertificateEncryptionError.invalidHashData
        }
        
        return try encryptCertificate(hashData)
    }
    
    static func decryptCertificateHash(_ encryptedData: Data) throws -> String {
        let decryptedData = try decryptCertificate(encryptedData)
        guard let hash = String(data: decryptedData, encoding: .utf8) else {
            throw CertificateEncryptionError.invalidHashData
        }
        
        return hash
    }
    
    // MARK: - Bundle Management
    static func createEncryptedCertificateBundle(
        certificates: [(data: Data, name: String)],
        publicKeyHashes: [String],
        certificateHashes: [String],
        outputPath: URL
    ) throws {
        let bundlePath = outputPath.appendingPathComponent("EncryptedCertificates.bundle")
        
        // Create bundle directory
        try FileManager.default.createDirectory(at: bundlePath, withIntermediateDirectories: true)
        
        // Encrypt and store certificates
        for (data, name) in certificates {
            let encryptedData = try encryptCertificate(data)
            let certPath = bundlePath.appendingPathComponent("\(name)-cert.enc")
            try encryptedData.write(to: certPath)
            
            print("✅ Encrypted certificate: \(name)")
        }
        
        // Encrypt and store public key hashes
        for (index, hash) in publicKeyHashes.enumerated() {
            let encryptedHash = try encryptCertificateHash(hash)
            let hashPath = bundlePath.appendingPathComponent("pubkey-hash-\(index).enc")
            try encryptedHash.write(to: hashPath)
            
            print("✅ Encrypted public key hash: \(index)")
        }
        
        // Encrypt and store certificate hashes
        for (index, hash) in certificateHashes.enumerated() {
            let encryptedHash = try encryptCertificateHash(hash)
            let hashPath = bundlePath.appendingPathComponent("cert-hash-\(index).enc")
            try encryptedHash.write(to: hashPath)
            
            print("✅ Encrypted certificate hash: \(index)")
        }
        
        // Create Info.plist
        let infoPlistContent = createInfoPlistContent()
        let infoPlistPath = bundlePath.appendingPathComponent("Info.plist")
        try infoPlistContent.write(to: infoPlistPath, atomically: true, encoding: .utf8)
        
        print("🔐 Created encrypted certificate bundle at: \(bundlePath.path)")
    }
    
    private static func createInfoPlistContent() -> String {
        return """
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>CFBundleIdentifier</key>
            <string>com.omega.certificates.encrypted</string>
            <key>CFBundleName</key>
            <string>EncryptedCertificates</string>
            <key>CFBundleVersion</key>
            <string>1.0</string>
            <key>CFBundleShortVersionString</key>
            <string>1.0</string>
            <key>CFBundlePackageType</key>
            <string>BNDL</string>
            <key>CFBundleDevelopmentRegion</key>
            <string>en</string>
            <key>NSHumanReadableCopyright</key>
            <string>Copyright © 2024 OMEGA Pro AI. All rights reserved.</string>
            <key>EncryptionVersion</key>
            <string>AES-256-GCM</string>
            <key>CertificateFormat</key>
            <string>X.509-DER-Encrypted</string>
            <key>CreationDate</key>
            <string>\(Date().description)</string>
        </dict>
        </plist>
        """
    }
    
    // MARK: - Certificate Loading
    static func loadEncryptedCertificates(from bundlePath: String) -> [String: SecCertificate] {
        var certificates: [String: SecCertificate] = [:]
        
        guard let bundle = Bundle(path: bundlePath) else {
            print("❌ Could not load encrypted certificate bundle")
            return certificates
        }
        
        let encryptedFiles = bundle.paths(forResourcesOfType: "enc", inDirectory: nil)
        
        for filePath in encryptedFiles {
            let fileName = URL(fileURLWithPath: filePath).lastPathComponent
            
            if fileName.contains("cert.enc") {
                do {
                    guard let encryptedData = NSData(contentsOfFile: filePath) else {
                        continue
                    }
                    
                    let decryptedData = try decryptCertificate(encryptedData as Data)
                    
                    if let certificate = SecCertificateCreateWithData(nil, decryptedData as CFData) {
                        let name = fileName.replacingOccurrences(of: "-cert.enc", with: "")
                        certificates[name] = certificate
                        print("✅ Loaded encrypted certificate: \(name)")
                    }
                    
                } catch {
                    print("❌ Failed to decrypt certificate \(fileName): \(error)")
                }
            }
        }
        
        return certificates
    }
    
    // MARK: - Hash Loading
    static func loadEncryptedHashes(from bundlePath: String, type: HashType) -> [String] {
        var hashes: [String] = []
        
        guard let bundle = Bundle(path: bundlePath) else {
            return hashes
        }
        
        let pattern = type == .publicKey ? "pubkey-hash" : "cert-hash"
        let encryptedFiles = bundle.paths(forResourcesOfType: "enc", inDirectory: nil)
            .filter { $0.contains(pattern) }
            .sorted()
        
        for filePath in encryptedFiles {
            do {
                guard let encryptedData = NSData(contentsOfFile: filePath) else {
                    continue
                }
                
                let hash = try decryptCertificateHash(encryptedData as Data)
                hashes.append(hash)
                
            } catch {
                print("❌ Failed to decrypt hash from \(filePath): \(error)")
            }
        }
        
        return hashes
    }
    
    // MARK: - Certificate Generation for Testing
    static func generateSampleEncryptedBundle() throws {
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        
        // Sample certificate data (in production, load from actual certificates)
        let sampleCertData = "SAMPLE_CERTIFICATE_DATA".data(using: .utf8)!
        let certificates = [(data: sampleCertData, name: "akash-production")]
        
        // Sample hashes (in production, generate from actual certificates)
        let publicKeyHashes = [
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35"
        ]
        
        let certificateHashes = [
            "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            "b5d4045c3f466fa91fe2cc6abe79232a1a57cdf104f7a26e716e0a1e2789df78"
        ]
        
        try createEncryptedCertificateBundle(
            certificates: certificates,
            publicKeyHashes: publicKeyHashes,
            certificateHashes: certificateHashes,
            outputPath: documentsPath
        )
    }
    
    // MARK: - Certificate Validation
    static func validateEncryptedBundle(at path: String) -> ValidationReport {
        var report = ValidationReport()
        
        guard let bundle = Bundle(path: path) else {
            report.errors.append("Could not load bundle at path: \(path)")
            return report
        }
        
        let encryptedFiles = bundle.paths(forResourcesOfType: "enc", inDirectory: nil)
        report.totalFiles = encryptedFiles.count
        
        for filePath in encryptedFiles {
            do {
                guard let encryptedData = NSData(contentsOfFile: filePath) else {
                    report.errors.append("Could not read file: \(filePath)")
                    continue
                }
                
                // Try to decrypt to validate
                _ = try decryptCertificate(encryptedData as Data)
                report.validFiles += 1
                
            } catch {
                report.errors.append("Decryption failed for \(filePath): \(error)")
            }
        }
        
        report.isValid = report.errors.isEmpty && report.validFiles > 0
        
        return report
    }
}

// MARK: - Supporting Types
enum CertificateEncryptionError: LocalizedError {
    case encryptionFailed
    case decryptionFailed
    case invalidHashData
    case bundleCreationFailed
    
    var errorDescription: String? {
        switch self {
        case .encryptionFailed:
            return "Certificate encryption failed"
        case .decryptionFailed:
            return "Certificate decryption failed"
        case .invalidHashData:
            return "Invalid hash data"
        case .bundleCreationFailed:
            return "Bundle creation failed"
        }
    }
}

enum HashType {
    case publicKey
    case certificate
}

struct ValidationReport {
    var isValid = false
    var totalFiles = 0
    var validFiles = 0
    var errors: [String] = []
    
    var summary: String {
        return """
        Validation Report:
        - Valid: \(isValid)
        - Files: \(validFiles)/\(totalFiles)
        - Errors: \(errors.count)
        \(errors.isEmpty ? "" : "\nErrors:\n" + errors.joined(separator: "\n"))
        """
    }
}