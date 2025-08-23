import Foundation
import os

// MARK: - Logging Categories
enum LogCategory: String, CaseIterable {
    case auth = "AUTH"
    case network = "NETWORK"
    case ui = "UI"
    case data = "DATA"
    case security = "SECURITY"
    case performance = "PERFORMANCE"
    case general = "GENERAL"
    
    var osLog: OSLog {
        return OSLog(subsystem: AppConfig.App.bundleIdentifier, category: self.rawValue)
    }
}

// MARK: - App Logger
class AppLogger {
    static let shared = AppLogger()
    
    private let dateFormatter: DateFormatter
    private let logQueue = DispatchQueue(label: "com.omega.logger", qos: .utility)
    
    private init() {
        self.dateFormatter = DateFormatter()
        self.dateFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss.SSS"
        self.dateFormatter.timeZone = TimeZone.current
    }
    
    // MARK: - Public Logging Methods
    
    func debug(
        _ message: String,
        category: LogCategory = .general,
        file: String = #file,
        function: String = #function,
        line: Int = #line,
        metadata: [String: Any]? = nil
    ) {
        performLog(level: .debug, message: message, category: category, file: file, function: function, line: line, metadata: metadata)
    }
    
    func info(
        _ message: String,
        category: LogCategory = .general,
        file: String = #file,
        function: String = #function,
        line: Int = #line,
        metadata: [String: Any]? = nil
    ) {
        performLog(level: .info, message: message, category: category, file: file, function: function, line: line, metadata: metadata)
    }
    
    func warning(
        _ message: String,
        category: LogCategory = .general,
        file: String = #file,
        function: String = #function,
        line: Int = #line,
        error: Error? = nil,
        metadata: [String: Any]? = nil
    ) {
        var combinedMetadata = metadata ?? [:]
        if let error = error {
            combinedMetadata["error"] = error.localizedDescription
        }
        performLog(level: .default, message: message, category: category, file: file, function: function, line: line, metadata: combinedMetadata)
    }
    
    func error(
        _ message: String,
        category: LogCategory = .general,
        file: String = #file,
        function: String = #function,
        line: Int = #line,
        error: Error? = nil,
        metadata: [String: Any]? = nil
    ) {
        var combinedMetadata = metadata ?? [:]
        if let error = error {
            combinedMetadata["error"] = error.localizedDescription
        }
        performLog(level: .error, message: message, category: category, file: file, function: function, line: line, metadata: combinedMetadata)
    }
    
    // MARK: - Generic Log Method
    
    func log(
        level: LogLevel,
        message: String,
        category: LogCategory = .general,
        file: String = #file,
        function: String = #function,
        line: Int = #line,
        metadata: [String: Any]? = nil
    ) {
        switch level {
        case .debug:
            debug(message, category: category, file: file, function: function, line: line, metadata: metadata)
        case .info:
            info(message, category: category, file: file, function: function, line: line, metadata: metadata)
        case .warning:
            warning(message, category: category, file: file, function: function, line: line, metadata: metadata)
        case .error:
            error(message, category: category, file: file, function: function, line: line, metadata: metadata)
        }
    }
    
    // MARK: - Private Implementation
    
    private func performLog(
        level: OSLogType,
        message: String,
        category: LogCategory,
        file: String,
        function: String,
        line: Int,
        metadata: [String: Any]?
    ) {
        guard shouldLog(level: level) else { return }
        
        logQueue.async { [weak self] in
            self?.performLogging(
                level: level,
                message: message,
                category: category,
                file: file,
                function: function,
                line: line,
                metadata: metadata
            )
        }
    }
    
    private func performLogging(
        level: OSLogType,
        message: String,
        category: LogCategory,
        file: String,
        function: String,
        line: Int,
        metadata: [String: Any]?
    ) {
        let timestamp = dateFormatter.string(from: Date())
        let fileName = URL(fileURLWithPath: file).lastPathComponent
        let levelString = logLevelString(for: level)
        
        // Format metadata
        let metadataString = formatMetadata(metadata)
        
        // Create log message
        let logMessage = "[\(timestamp)] [\(levelString)] [\(category.rawValue)] [\(fileName):\(line)] \(function) - \(message)\(metadataString)"
        
        // OS Log
        os_log("%{public}@", log: category.osLog, type: level, logMessage)
        
        // Console output in debug mode
        if AppConfig.API.isDevelopment {
            print(logMessage)
        }
        
        // File logging if enabled
        if AppConfig.Logging.fileLoggingEnabled {
            writeToFile(logMessage)
        }
        
        // Remote logging if enabled and appropriate level
        if AppConfig.Logging.remoteLoggingEnabled && level != .debug {
            sendToRemoteLogger(
                level: level,
                message: message,
                category: category,
                metadata: metadata
            )
        }
    }
    
    private func shouldLog(level: OSLogType) -> Bool {
        let configLevel = AppConfig.Logging.level
        
        switch configLevel {
        case .debug:
            return true
        case .info:
            return level != .debug
        case .warning:
            return level == .default || level == .error || level == .fault
        case .error:
            return level == .error || level == .fault
        }
    }
    
    private func logLevelString(for level: OSLogType) -> String {
        switch level {
        case .debug:
            return "DEBUG"
        case .info:
            return "INFO"
        case .default:
            return "WARN"
        case .error:
            return "ERROR"
        case .fault:
            return "FATAL"
        default:
            return "UNKNOWN"
        }
    }
    
    private func formatMetadata(_ metadata: [String: Any]?) -> String {
        guard let metadata = metadata, !metadata.isEmpty else {
            return ""
        }
        
        let metadataStrings = metadata.compactMap { key, value in
            return "\(key)=\(value)"
        }
        
        return " {\(metadataStrings.joined(separator: ", "))}"
    }
    
    private func writeToFile(_ message: String) {
        guard let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else {
            return
        }
        
        let logFileURL = documentsDirectory.appendingPathComponent("omega_app.log")
        
        do {
            let messageWithNewline = message + "\n"
            
            if FileManager.default.fileExists(atPath: logFileURL.path) {
                let fileHandle = try FileHandle(forWritingTo: logFileURL)
                fileHandle.seekToEndOfFile()
                fileHandle.write(messageWithNewline.data(using: .utf8)!)
                fileHandle.closeFile()
                
                // Check file size and rotate if necessary
                checkAndRotateLogFile(at: logFileURL)
            } else {
                try messageWithNewline.write(to: logFileURL, atomically: true, encoding: .utf8)
            }
        } catch {
            // Fallback to console logging if file logging fails
            print("Failed to write to log file: \(error)")
            print(message)
        }
    }
    
    private func checkAndRotateLogFile(at url: URL) {
        do {
            let attributes = try FileManager.default.attributesOfItem(atPath: url.path)
            if let fileSize = attributes[.size] as? Int64,
               fileSize > AppConfig.Logging.maxLogFileSize {
                
                // Rotate log files
                for i in (1..<AppConfig.Logging.maxLogFiles).reversed() {
                    let currentFile = url.appendingPathExtension("\(i)")
                    let nextFile = url.appendingPathExtension("\(i + 1)")
                    
                    if FileManager.default.fileExists(atPath: currentFile.path) {
                        if FileManager.default.fileExists(atPath: nextFile.path) {
                            try FileManager.default.removeItem(at: nextFile)
                        }
                        try FileManager.default.moveItem(at: currentFile, to: nextFile)
                    }
                }
                
                // Move current log to .1
                let backupFile = url.appendingPathExtension("1")
                if FileManager.default.fileExists(atPath: backupFile.path) {
                    try FileManager.default.removeItem(at: backupFile)
                }
                try FileManager.default.moveItem(at: url, to: backupFile)
            }
        } catch {
            print("Failed to rotate log file: \(error)")
        }
    }
    
    private func sendToRemoteLogger(
        level: OSLogType,
        message: String,
        category: LogCategory,
        metadata: [String: Any]?
    ) {
        // Implementation for remote logging service
        // This could send logs to a service like Sentry, LogRocket, etc.
        
        guard AppConfig.currentEnvironment != .development else { return }
        
        Task {
            do {
                let logEntry = RemoteLogEntry(
                    level: logLevelString(for: level),
                    message: message,
                    category: category.rawValue,
                    timestamp: Date(),
                    metadata: metadata,
                    appVersion: AppConfig.App.version,
                    environment: AppConfig.currentEnvironment.rawValue
                )
                
                // Send to remote logging service
                // await remoteLoggingService.send(logEntry)
                
            } catch {
                // Don't log this error to avoid infinite recursion
                print("Failed to send log to remote service: \(error)")
            }
        }
    }
}

// MARK: - Remote Logging Models

private struct RemoteLogEntry: Codable {
    let level: String
    let message: String
    let category: String
    let timestamp: Date
    let metadata: [String: Any]?
    let appVersion: String
    let environment: String
    
    private enum CodingKeys: String, CodingKey {
        case level, message, category, timestamp
        case metadata, appVersion, environment
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(level, forKey: .level)
        try container.encode(message, forKey: .message)
        try container.encode(category, forKey: .category)
        try container.encode(timestamp, forKey: .timestamp)
        try container.encode(appVersion, forKey: .appVersion)
        try container.encode(environment, forKey: .environment)
        
        if let metadata = metadata {
            let jsonData = try JSONSerialization.data(withJSONObject: metadata)
            let jsonString = String(data: jsonData, encoding: .utf8)
            try container.encodeIfPresent(jsonString, forKey: .metadata)
        }
    }
}

// MARK: - Convenience Extensions

extension AppLogger {
    
    /// Log authentication events
    func logAuth(_ message: String, success: Bool, metadata: [String: Any]? = nil) {
        var combinedMetadata = metadata ?? [:]
        combinedMetadata["success"] = success
        
        if success {
            info(message, category: .auth, metadata: combinedMetadata)
        } else {
            warning(message, category: .auth, metadata: combinedMetadata)
        }
    }
    
    /// Log network requests
    func logNetworkRequest(_ method: String, url: String, statusCode: Int? = nil, duration: TimeInterval? = nil) {
        var metadata: [String: Any] = [
            "method": method,
            "url": url
        ]
        
        if let statusCode = statusCode {
            metadata["status_code"] = statusCode
        }
        
        if let duration = duration {
            metadata["duration_ms"] = Int(duration * 1000)
        }
        
        let level: LogCategory = (statusCode ?? 200 >= 400) ? .general : .network
        info("Network request completed", category: level, metadata: metadata)
    }
    
    /// Log performance metrics
    func logPerformance(_ operation: String, duration: TimeInterval, metadata: [String: Any]? = nil) {
        var combinedMetadata = metadata ?? [:]
        combinedMetadata["duration_ms"] = Int(duration * 1000)
        
        info("Performance metric: \(operation)", category: .performance, metadata: combinedMetadata)
    }
}