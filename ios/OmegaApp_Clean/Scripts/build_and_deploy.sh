#!/bin/bash

# OMEGA Pro AI - Build and Deploy Script
# This script builds and deploys the iOS app for different environments

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
XCODE_PROJECT="$PROJECT_DIR/Omega/Omega.xcodeproj"
XCODE_WORKSPACE="$PROJECT_DIR/Omega/Omega.xcworkspace"
SCHEME="Omega"
CERTIFICATE_SCRIPT="$SCRIPT_DIR/certificate_manager.sh"

# Build configurations
CONFIGURATIONS=("Development" "Staging" "Production")
EXPORT_METHODS=("development" "app-store" "app-store")

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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Xcode project exists
    if [[ ! -d "$XCODE_PROJECT" ]]; then
        log_error "Xcode project not found: $XCODE_PROJECT"
        exit 1
    fi
    
    # Check required tools
    local tools=("xcodebuild" "xcrun" "plutil")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Check if fastlane is available
    if command -v fastlane &> /dev/null; then
        log_success "Fastlane is available"
    else
        log_warning "Fastlane not found - using xcodebuild directly"
    fi
    
    log_success "Prerequisites check completed"
}

setup_certificates() {
    local environment="$1"
    log_info "Setting up certificates for $environment..."
    
    if [[ -x "$CERTIFICATE_SCRIPT" ]]; then
        "$CERTIFICATE_SCRIPT" setup
        "$CERTIFICATE_SCRIPT" profiles "${environment,,}"
    else
        log_warning "Certificate manager script not found or not executable"
    fi
}

clean_build() {
    log_info "Cleaning build artifacts..."
    
    # Clean derived data
    rm -rf ~/Library/Developer/Xcode/DerivedData/Omega-*
    
    # Clean build folder
    if command -v xcodebuild &> /dev/null; then
        xcodebuild clean -project "$XCODE_PROJECT" -scheme "$SCHEME" &> /dev/null || log_warning "Failed to clean with xcodebuild"
    fi
    
    log_success "Build artifacts cleaned"
}

build_app() {
    local configuration="$1"
    local export_method="$2"
    
    log_info "Building app for $configuration configuration..."
    
    # Build settings
    local build_dir="$PROJECT_DIR/builds/$(echo "$configuration" | tr '[:upper:]' '[:lower:]')"
    local archive_path="$build_dir/Omega.xcarchive"
    local export_path="$build_dir"
    
    # Create build directory
    mkdir -p "$build_dir"
    
    # Archive the app
    log_info "Creating archive for $configuration..."
    if xcodebuild archive \
        -project "$XCODE_PROJECT" \
        -scheme "$SCHEME" \
        -configuration "$configuration" \
        -archivePath "$archive_path" \
        -destination "generic/platform=iOS" \
        -allowProvisioningUpdates \
        CODE_SIGN_STYLE=Automatic \
        DEVELOPMENT_TEAM=PSXDB5A2NN; then
        log_success "Archive created successfully"
    else
        log_error "Failed to create archive for $configuration"
        return 1
    fi
    
    # Create export options plist
    local export_options_plist="$build_dir/ExportOptions.plist"
    create_export_options_plist "$export_options_plist" "$export_method" "$configuration"
    
    # Export IPA
    log_info "Exporting IPA for $configuration..."
    if xcodebuild -exportArchive \
        -archivePath "$archive_path" \
        -exportPath "$export_path" \
        -exportOptionsPlist "$export_options_plist"; then
        log_success "IPA exported successfully"
        
        # List the built products
        log_info "Built artifacts:"
        ls -la "$export_path"/*.ipa 2>/dev/null || log_warning "No IPA files found"
        
    else
        log_error "Failed to export IPA for $configuration"
        return 1
    fi
}

create_export_options_plist() {
    local plist_path="$1"
    local export_method="$2"
    local configuration="$3"
    
    log_info "Creating export options plist..."
    
    # Determine bundle identifier based on configuration
    local bundle_id
    case "$configuration" in
        "Development")
            bundle_id="com.omega.OmegaApp.dev"
            ;;
        "Staging")
            bundle_id="com.omega.OmegaApp.staging"
            ;;
        "Production")
            bundle_id="com.omega.OmegaApp"
            ;;
        *)
            bundle_id="com.omega.OmegaApp"
            ;;
    esac
    
    cat > "$plist_path" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>$export_method</string>
    <key>teamID</key>
    <string>PSXDB5A2NN</string>
    <key>uploadBitcode</key>
    <false/>
    <key>uploadSymbols</key>
    <true/>
    <key>compileBitcode</key>
    <false/>
    <key>stripSwiftSymbols</key>
    <true/>
    <key>thinning</key>
    <string>&lt;none&gt;</string>
    <key>provisioningProfiles</key>
    <dict>
        <key>$bundle_id</key>
        <string>OMEGA ${configuration} Profile</string>
    </dict>
    <key>signingStyle</key>
    <string>automatic</string>
    <key>signingCertificate</key>
    <string>Apple Distribution</string>
</dict>
</plist>
EOF
    
    log_success "Export options plist created: $plist_path"
}

run_tests() {
    local configuration="$1"
    log_info "Running tests for $configuration configuration..."
    
    # Run unit tests
    if xcodebuild test \
        -project "$XCODE_PROJECT" \
        -scheme "$SCHEME" \
        -configuration "$configuration" \
        -destination "platform=iOS Simulator,name=iPhone 15 Pro,OS=latest" \
        -enableCodeCoverage YES; then
        log_success "Tests passed for $configuration"
    else
        log_warning "Some tests failed for $configuration"
        return 1
    fi
}

validate_build() {
    local configuration="$1"
    log_info "Validating build for $configuration..."
    
    local build_dir="$PROJECT_DIR/builds/$(echo "$configuration" | tr '[:upper:]' '[:lower:]')"
    local ipa_files=("$build_dir"/*.ipa)
    
    if [[ -f "${ipa_files[0]}" ]]; then
        local ipa_file="${ipa_files[0]}"
        log_info "Validating IPA: $(basename "$ipa_file")"
        
        # Basic validation - check if IPA can be extracted
        if unzip -t "$ipa_file" &>/dev/null; then
            log_success "IPA validation passed"
        else
            log_error "IPA validation failed"
            return 1
        fi
        
        # Check IPA size
        local size
        size=$(du -h "$ipa_file" | cut -f1)
        log_info "IPA size: $size"
        
    else
        log_error "No IPA file found for validation"
        return 1
    fi
}

deploy_to_testflight() {
    log_info "Deploying to TestFlight..."
    
    if command -v fastlane &> /dev/null; then
        cd "$PROJECT_DIR"
        if fastlane beta; then
            log_success "Successfully deployed to TestFlight"
        else
            log_error "Failed to deploy to TestFlight"
            return 1
        fi
    else
        log_error "Fastlane not available - cannot deploy to TestFlight"
        return 1
    fi
}

deploy_to_app_store() {
    log_info "Deploying to App Store..."
    
    if command -v fastlane &> /dev/null; then
        cd "$PROJECT_DIR"
        if fastlane release; then
            log_success "Successfully deployed to App Store"
        else
            log_error "Failed to deploy to App Store"
            return 1
        fi
    else
        log_error "Fastlane not available - cannot deploy to App Store"
        return 1
    fi
}

update_version() {
    local version_type="$1" # major, minor, patch
    log_info "Updating version ($version_type)..."
    
    # Get current version
    local current_version
    current_version=$(xcodebuild -project "$XCODE_PROJECT" -showBuildSettings | grep MARKETING_VERSION | head -1 | awk '{print $3}')
    
    log_info "Current version: $current_version"
    
    # This would need a more sophisticated version bumping logic
    log_warning "Version update not implemented - please update manually in Xcode"
}

generate_changelog() {
    log_info "Generating changelog..."
    
    local changelog_file="$PROJECT_DIR/CHANGELOG.md"
    local build_date
    build_date=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Simple changelog generation
    if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
        {
            echo "# OMEGA Pro AI - Build Log"
            echo "Generated on: $build_date"
            echo ""
            echo "## Recent Changes"
            git log --oneline -10
            echo ""
        } > "$changelog_file"
        log_success "Changelog generated: $changelog_file"
    else
        log_warning "Git not available - skipping changelog generation"
    fi
}

show_build_status() {
    log_info "Build Status Summary"
    echo "===================="
    
    # Show build artifacts
    for config in "${CONFIGURATIONS[@]}"; do
        local build_dir="$PROJECT_DIR/builds/$(echo "$config" | tr '[:upper:]' '[:lower:]')"
        echo -e "\n${BLUE}$config Build:${NC}"
        
        if [[ -d "$build_dir" ]]; then
            local ipa_count
            ipa_count=$(find "$build_dir" -name "*.ipa" | wc -l)
            echo "  Build directory: $build_dir"
            echo "  IPA files: $ipa_count"
            
            if [[ $ipa_count -gt 0 ]]; then
                echo "  Latest IPA:"
                ls -lt "$build_dir"/*.ipa | head -1 | awk '{print "    " $9 " (" $5 " bytes, " $6 " " $7 " " $8 ")"}'
            fi
        else
            echo "  No builds found"
        fi
    done
    
    # Show certificate status
    if [[ -x "$CERTIFICATE_SCRIPT" ]]; then
        echo -e "\n${BLUE}Certificate Status:${NC}"
        "$CERTIFICATE_SCRIPT" info || log_warning "Certificate info not available"
    fi
}

# Main function
main() {
    echo -e "${GREEN}OMEGA Pro AI - Build and Deploy${NC}"
    echo "================================"
    
    local command="${1:-help}"
    local configuration="${2:-Development}"
    
    case "$command" in
        "build")
            check_prerequisites
            setup_certificates "$configuration"
            clean_build
            
            # Find configuration index
            local config_index=-1
            for i in "${!CONFIGURATIONS[@]}"; do
                if [[ "${CONFIGURATIONS[$i]}" = "$configuration" ]]; then
                    config_index=$i
                    break
                fi
            done
            
            if [[ $config_index -eq -1 ]]; then
                log_error "Invalid configuration: $configuration"
                exit 1
            fi
            
            local export_method="${EXPORT_METHODS[$config_index]}"
            build_app "$configuration" "$export_method"
            validate_build "$configuration"
            ;;
            
        "test")
            check_prerequisites
            run_tests "$configuration"
            ;;
            
        "build-all")
            check_prerequisites
            clean_build
            
            for i in "${!CONFIGURATIONS[@]}"; do
                local config="${CONFIGURATIONS[$i]}"
                local method="${EXPORT_METHODS[$i]}"
                
                log_info "Building configuration: $config"
                setup_certificates "$config"
                
                if build_app "$config" "$method"; then
                    validate_build "$config"
                else
                    log_error "Build failed for $config"
                fi
            done
            ;;
            
        "deploy-testflight")
            deploy_to_testflight
            ;;
            
        "deploy-appstore")
            deploy_to_app_store
            ;;
            
        "certificates")
            setup_certificates "$configuration"
            ;;
            
        "clean")
            clean_build
            ;;
            
        "status")
            show_build_status
            ;;
            
        "version")
            local version_type="${2:-patch}"
            update_version "$version_type"
            ;;
            
        "changelog")
            generate_changelog
            ;;
            
        "help"|*)
            echo "Usage: $0 <command> [configuration] [options]"
            echo ""
            echo "Commands:"
            echo "  build [config]       - Build app for specific configuration (Development|Staging|Production)"
            echo "  build-all           - Build app for all configurations"
            echo "  test [config]       - Run tests for specific configuration"
            echo "  deploy-testflight   - Deploy to TestFlight (requires build)"
            echo "  deploy-appstore     - Deploy to App Store (requires build)"
            echo "  certificates [config] - Setup certificates and profiles"
            echo "  clean               - Clean build artifacts"
            echo "  status              - Show build status"
            echo "  version [type]      - Update version (major|minor|patch)"
            echo "  changelog           - Generate changelog"
            echo "  help                - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 build Development"
            echo "  $0 build-all"
            echo "  $0 test Staging"
            echo "  $0 deploy-testflight"
            echo "  $0 certificates Production"
            ;;
    esac
}

# Run main function with all arguments
main "$@"