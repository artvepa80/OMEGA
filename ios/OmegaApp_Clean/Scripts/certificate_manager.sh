#!/bin/bash

# OMEGA Pro AI - Certificate Management Script
# This script manages SSL certificates and provisioning profiles for iOS deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CERTIFICATES_DIR="$PROJECT_DIR/ssl_certificates"
BUNDLE_DIR="$PROJECT_DIR/PinnedCertificates.bundle"

# Akash Network configuration
AKASH_DOMAIN="a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online"
AKASH_PORT="443"

# Certificate types
CERT_TYPES=("development" "staging" "production")

# Bundle identifiers
DEV_BUNDLE_ID="com.omega.OmegaApp.dev"
STAGING_BUNDLE_ID="com.omega.OmegaApp.staging"
PROD_BUNDLE_ID="com.omega.OmegaApp"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    local deps=("openssl" "fastlane" "security" "xcodebuild")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and try again."
        exit 1
    fi
    
    log_success "All dependencies are available"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p "$CERTIFICATES_DIR"
    mkdir -p "$BUNDLE_DIR"
    mkdir -p "$PROJECT_DIR/builds/development"
    mkdir -p "$PROJECT_DIR/builds/staging"
    mkdir -p "$PROJECT_DIR/builds/production"
    
    log_success "Directories created successfully"
}

download_ssl_certificates() {
    log_info "Downloading SSL certificates from Akash Network..."
    
    # Download server certificate
    if timeout 30 openssl s_client -showcerts -connect "$AKASH_DOMAIN:$AKASH_PORT" -servername "$AKASH_DOMAIN" </dev/null 2>/dev/null | openssl x509 -outform PEM > "$CERTIFICATES_DIR/akash_server_cert.pem" 2>/dev/null; then
        log_success "Server certificate downloaded successfully"
    else
        log_warning "Failed to download server certificate - this is expected for development environments"
        # Create a placeholder certificate for development
        echo "-----BEGIN CERTIFICATE-----" > "$CERTIFICATES_DIR/akash_server_cert.pem"
        echo "# Placeholder certificate for development" >> "$CERTIFICATES_DIR/akash_server_cert.pem"
        echo "-----END CERTIFICATE-----" >> "$CERTIFICATES_DIR/akash_server_cert.pem"
    fi
    
    # Download certificate chain
    if timeout 30 openssl s_client -showcerts -connect "$AKASH_DOMAIN:$AKASH_PORT" -servername "$AKASH_DOMAIN" </dev/null 2>/dev/null | sed -n '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/p' > "$CERTIFICATES_DIR/akash_chain.pem" 2>/dev/null; then
        log_success "Certificate chain downloaded successfully"
    else
        log_warning "Failed to download certificate chain"
    fi
    
    # Extract public key from certificate
    if [ -f "$CERTIFICATES_DIR/akash_server_cert.pem" ] && [ -s "$CERTIFICATES_DIR/akash_server_cert.pem" ]; then
        if openssl x509 -in "$CERTIFICATES_DIR/akash_server_cert.pem" -pubkey -noout > "$CERTIFICATES_DIR/akash_public_key.pem" 2>/dev/null; then
            log_success "Public key extracted successfully"
        else
            log_warning "Failed to extract public key from certificate"
        fi
    fi
}

create_certificate_bundle() {
    log_info "Creating certificate bundle for app..."
    
    # Copy certificates to bundle
    if [ -d "$CERTIFICATES_DIR" ]; then
        cp -r "$CERTIFICATES_DIR"/* "$BUNDLE_DIR/" 2>/dev/null || true
        
        # Create bundle info plist
        cat > "$BUNDLE_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.omega.PinnedCertificates</string>
    <key>CFBundleName</key>
    <string>PinnedCertificates</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
</dict>
</plist>
EOF
        
        log_success "Certificate bundle created successfully"
    else
        log_error "Certificates directory not found"
        return 1
    fi
}

manage_provisioning_profiles() {
    local profile_type="$1"
    log_info "Managing provisioning profiles for $profile_type..."
    
    case "$profile_type" in
        "development")
            bundle_id="$DEV_BUNDLE_ID"
            ;;
        "staging")
            bundle_id="$STAGING_BUNDLE_ID"
            ;;
        "production")
            bundle_id="$PROD_BUNDLE_ID"
            ;;
        *)
            log_error "Invalid profile type: $profile_type"
            return 1
            ;;
    esac
    
    # Use fastlane match to manage certificates and profiles
    if command -v fastlane &> /dev/null; then
        cd "$PROJECT_DIR"
        
        case "$profile_type" in
            "development")
                fastlane certificates_dev || log_warning "Failed to setup development certificates"
                ;;
            "staging")
                fastlane certificates_staging || log_warning "Failed to setup staging certificates"
                ;;
            "production")
                fastlane certificates_production || log_warning "Failed to setup production certificates"
                ;;
        esac
    else
        log_warning "Fastlane not available - skipping provisioning profile management"
    fi
}

update_ssl_certificates() {
    log_info "Updating SSL certificates..."
    
    # Run fastlane SSL update lane if it exists
    if command -v fastlane &> /dev/null; then
        cd "$PROJECT_DIR"
        if fastlane update_ssl_certificates &> /dev/null; then
            log_success "SSL certificates updated via fastlane"
        else
            log_warning "Fastlane SSL update failed - continuing with manual process"
        fi
    fi
    
    # Manual certificate download and processing
    download_ssl_certificates
    create_certificate_bundle
}

validate_certificates() {
    log_info "Validating SSL certificates..."
    
    local cert_file="$CERTIFICATES_DIR/akash_server_cert.pem"
    
    if [ ! -f "$cert_file" ]; then
        log_warning "Certificate file not found: $cert_file"
        return 1
    fi
    
    # Check certificate validity
    if openssl x509 -in "$cert_file" -noout -dates 2>/dev/null; then
        local not_after
        not_after=$(openssl x509 -in "$cert_file" -noout -enddate 2>/dev/null | cut -d= -f2)
        log_info "Certificate expires: $not_after"
        
        # Check if certificate is still valid
        if openssl x509 -in "$cert_file" -noout -checkend 86400 2>/dev/null; then
            log_success "Certificate is valid for at least 24 hours"
        else
            log_warning "Certificate expires within 24 hours"
        fi
    else
        log_warning "Failed to validate certificate"
    fi
    
    # Test SSL connection
    log_info "Testing SSL connection to $AKASH_DOMAIN..."
    if timeout 10 openssl s_client -connect "$AKASH_DOMAIN:$AKASH_PORT" -servername "$AKASH_DOMAIN" </dev/null &>/dev/null; then
        log_success "SSL connection test successful"
    else
        log_warning "SSL connection test failed - this may be expected in some environments"
    fi
}

clean_certificates() {
    log_info "Cleaning old certificates..."
    
    if [ -d "$CERTIFICATES_DIR" ]; then
        find "$CERTIFICATES_DIR" -name "*.pem" -mtime +30 -delete 2>/dev/null || true
        log_success "Old certificates cleaned"
    fi
    
    if [ -d "$BUNDLE_DIR" ]; then
        find "$BUNDLE_DIR" -name "*.pem" -mtime +30 -delete 2>/dev/null || true
        log_success "Old bundle certificates cleaned"
    fi
}

backup_certificates() {
    log_info "Creating certificate backup..."
    
    local backup_dir="$PROJECT_DIR/backups/certificates/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    if [ -d "$CERTIFICATES_DIR" ] && [ "$(ls -A "$CERTIFICATES_DIR")" ]; then
        cp -r "$CERTIFICATES_DIR"/* "$backup_dir/" 2>/dev/null || true
        log_success "Certificates backed up to $backup_dir"
    else
        log_info "No certificates to backup"
    fi
}

show_certificate_info() {
    log_info "Certificate Information:"
    echo "======================="
    
    local cert_file="$CERTIFICATES_DIR/akash_server_cert.pem"
    
    if [ -f "$cert_file" ]; then
        echo -e "${BLUE}Certificate Details:${NC}"
        openssl x509 -in "$cert_file" -text -noout 2>/dev/null | grep -E "(Subject:|Issuer:|Not Before:|Not After:|DNS:)" || log_warning "Could not parse certificate details"
        
        echo -e "\n${BLUE}Certificate Fingerprint (SHA256):${NC}"
        openssl x509 -in "$cert_file" -noout -fingerprint -sha256 2>/dev/null || log_warning "Could not get certificate fingerprint"
        
        echo -e "\n${BLUE}Public Key Hash (SHA256):${NC}"
        openssl x509 -in "$cert_file" -pubkey -noout 2>/dev/null | openssl pkey -pubin -outform DER 2>/dev/null | openssl dgst -sha256 -binary | base64 2>/dev/null || log_warning "Could not get public key hash"
    else
        log_warning "Certificate file not found: $cert_file"
    fi
}

# Main function
main() {
    echo -e "${GREEN}OMEGA Pro AI - Certificate Manager${NC}"
    echo "================================="
    
    local command="${1:-help}"
    
    case "$command" in
        "setup")
            check_dependencies
            create_directories
            update_ssl_certificates
            ;;
        "update")
            update_ssl_certificates
            validate_certificates
            ;;
        "download")
            download_ssl_certificates
            ;;
        "bundle")
            create_certificate_bundle
            ;;
        "validate")
            validate_certificates
            ;;
        "profiles")
            local profile_type="${2:-all}"
            if [ "$profile_type" = "all" ]; then
                for type in "${CERT_TYPES[@]}"; do
                    manage_provisioning_profiles "$type"
                done
            else
                manage_provisioning_profiles "$profile_type"
            fi
            ;;
        "clean")
            clean_certificates
            ;;
        "backup")
            backup_certificates
            ;;
        "info")
            show_certificate_info
            ;;
        "help"|*)
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  setup     - Initial setup: create directories and download certificates"
            echo "  update    - Update SSL certificates and validate"
            echo "  download  - Download SSL certificates from Akash Network"
            echo "  bundle    - Create certificate bundle for app"
            echo "  validate  - Validate SSL certificates"
            echo "  profiles  - Manage provisioning profiles [development|staging|production|all]"
            echo "  clean     - Clean old certificates"
            echo "  backup    - Create backup of certificates"
            echo "  info      - Show certificate information"
            echo "  help      - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 setup"
            echo "  $0 update"
            echo "  $0 profiles development"
            echo "  $0 validate"
            ;;
    esac
}

# Run main function with all arguments
main "$@"