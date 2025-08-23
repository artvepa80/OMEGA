#!/usr/bin/env python3
"""
OMEGA Pro AI - Xcode Project Configuration Script
This script configures the Xcode project to use our custom xcconfig files
for different build environments (Development, Staging, Production).
"""

import os
import sys
import re
import shutil
from pathlib import Path

class XcodeProjectConfigurator:
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.pbxproj_path = self.project_path / "project.pbxproj"
        # Look for Configurations directory in the parent directory of the xcodeproj
        self.configurations_path = self.project_path.parent.parent / "Configurations"
        
    def backup_project_file(self):
        """Create a backup of the original project.pbxproj file"""
        backup_path = self.pbxproj_path.with_suffix('.pbxproj.backup')
        shutil.copy2(self.pbxproj_path, backup_path)
        print(f"✅ Backed up project.pbxproj to {backup_path}")
        
    def read_project_file(self):
        """Read the project.pbxproj file"""
        with open(self.pbxproj_path, 'r') as f:
            return f.read()
            
    def write_project_file(self, content):
        """Write the modified content back to project.pbxproj"""
        with open(self.pbxproj_path, 'w') as f:
            f.write(content)
            
    def generate_uuid(self):
        """Generate a UUID for Xcode project elements"""
        import uuid
        return str(uuid.uuid4()).replace('-', '').upper()[:24]
        
    def add_configuration_files_to_project(self, content):
        """Add xcconfig files to the project file references"""
        
        # Add file references for xcconfig files
        file_refs_section = content.find("/* Begin PBXFileReference section */")
        if file_refs_section == -1:
            raise ValueError("Could not find PBXFileReference section")
            
        # Generate UUIDs for the configuration files
        dev_config_uuid = self.generate_uuid()
        staging_config_uuid = self.generate_uuid()
        prod_config_uuid = self.generate_uuid()
        dev_pch_uuid = self.generate_uuid()
        staging_pch_uuid = self.generate_uuid()
        prod_pch_uuid = self.generate_uuid()
        
        # Insert file references
        file_refs_insert = content.find("/* End PBXFileReference section */")
        new_file_refs = f"""		{dev_config_uuid} /* Development.xcconfig */ = {{isa = PBXFileReference; lastKnownFileType = text.xcconfig; path = Development.xcconfig; sourceTree = "<group>"; }};
		{staging_config_uuid} /* Staging.xcconfig */ = {{isa = PBXFileReference; lastKnownFileType = text.xcconfig; path = Staging.xcconfig; sourceTree = "<group>"; }};
		{prod_config_uuid} /* Production.xcconfig */ = {{isa = PBXFileReference; lastKnownFileType = text.xcconfig; path = Production.xcconfig; sourceTree = "<group>"; }};
		{dev_pch_uuid} /* Development-Info.pch */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.c.h; path = "Development-Info.pch"; sourceTree = "<group>"; }};
		{staging_pch_uuid} /* Staging-Info.pch */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.c.h; path = "Staging-Info.pch"; sourceTree = "<group>"; }};
		{prod_pch_uuid} /* Production-Info.pch */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.c.h; path = "Production-Info.pch"; sourceTree = "<group>"; }};
"""
        
        content = content[:file_refs_insert] + new_file_refs + content[file_refs_insert:]
        
        # Add configuration group
        config_group_uuid = self.generate_uuid()
        groups_section = content.find("/* End PBXFileReference section */")
        groups_section = content.find("/* Begin PBXGroup section */", groups_section)
        
        # Find the main group and add Configurations group
        main_group_pattern = r'(CE7EB2C92E4A4C2C009C566B = \{[^}]+children = \([^)]+)\);'
        main_group_match = re.search(main_group_pattern, content, re.DOTALL)
        
        if main_group_match:
            main_group_content = main_group_match.group(1)
            new_main_group = main_group_content + f',\n\t\t\t\t{config_group_uuid} /* Configurations */,'
            content = content.replace(main_group_content + ');', new_main_group + ');')
            
        # Add the Configurations group definition
        groups_end = content.find("/* End PBXGroup section */")
        config_group_def = f"""		{config_group_uuid} /* Configurations */ = {{
			isa = PBXGroup;
			children = (
				{dev_config_uuid} /* Development.xcconfig */,
				{staging_config_uuid} /* Staging.xcconfig */,
				{prod_config_uuid} /* Production.xcconfig */,
				{dev_pch_uuid} /* Development-Info.pch */,
				{staging_pch_uuid} /* Staging-Info.pch */,
				{prod_pch_uuid} /* Production-Info.pch */,
			);
			path = Configurations;
			sourceTree = "<group>";
		}};
"""
        content = content[:groups_end] + config_group_def + content[groups_end:]
        
        return content, {
            'dev_config': dev_config_uuid,
            'staging_config': staging_config_uuid,
            'prod_config': prod_config_uuid
        }
        
    def create_build_configurations(self, content, config_uuids):
        """Create Development, Staging, and Production build configurations"""
        
        # Find the existing build configurations
        build_config_list_pattern = r'(CE7EB2F32E4A4C2F009C566B /\* Build configuration list for PBXNativeTarget "Omega" \*/ = \{[^}]+buildConfigurations = \([^)]+)\);'
        build_config_match = re.search(build_config_list_pattern, content, re.DOTALL)
        
        if not build_config_match:
            print("❌ Could not find build configuration list")
            return content
            
        # Generate UUIDs for new configurations
        dev_config_uuid = self.generate_uuid()
        staging_config_uuid = self.generate_uuid()
        prod_config_uuid = self.generate_uuid()
        
        # Update the build configuration list
        original_configs = build_config_match.group(1)
        new_configs = original_configs.replace(
            'CE7EB2F42E4A4C2F009C566B /* Debug */,\n\t\t\t\tCE7EB2F52E4A4C2F009C566B /* Release */,',
            f'{dev_config_uuid} /* Development */,\n\t\t\t\t{staging_config_uuid} /* Staging */,\n\t\t\t\t{prod_config_uuid} /* Production */,'
        )
        content = content.replace(original_configs + ');', new_configs + ');')
        
        # Add new build configuration definitions
        build_configs_end = content.find("/* End XCBuildConfiguration section */")
        
        new_build_configs = f"""		{dev_config_uuid} /* Development */ = {{
			isa = XCBuildConfiguration;
			baseConfigurationReference = {config_uuids['dev_config']} /* Development.xcconfig */;
			buildSettings = {{
			}};
			name = Development;
		}};
		{staging_config_uuid} /* Staging */ = {{
			isa = XCBuildConfiguration;
			baseConfigurationReference = {config_uuids['staging_config']} /* Staging.xcconfig */;
			buildSettings = {{
			}};
			name = Staging;
		}};
		{prod_config_uuid} /* Production */ = {{
			isa = XCBuildConfiguration;
			baseConfigurationReference = {config_uuids['prod_config']} /* Production.xcconfig */;
			buildSettings = {{
			}};
			name = Production;
		}};
"""
        
        content = content[:build_configs_end] + new_build_configs + content[build_configs_end:]
        
        # Update project-level build configuration list
        project_config_list_pattern = r'(CE7EB2F02E4A4C2F009C566B /\* Build configuration list for PBXProject "Omega" \*/ = \{[^}]+buildConfigurations = \([^)]+)\);'
        project_config_match = re.search(project_config_list_pattern, content, re.DOTALL)
        
        if project_config_match:
            project_dev_uuid = self.generate_uuid()
            project_staging_uuid = self.generate_uuid() 
            project_prod_uuid = self.generate_uuid()
            
            original_project_configs = project_config_match.group(1)
            new_project_configs = original_project_configs.replace(
                'CE7EB2F12E4A4C2F009C566B /* Debug */,\n\t\t\t\tCE7EB2F22E4A4C2F009C566B /* Release */,',
                f'{project_dev_uuid} /* Development */,\n\t\t\t\t{project_staging_uuid} /* Staging */,\n\t\t\t\t{project_prod_uuid} /* Production */,'
            )
            content = content.replace(original_project_configs + ');', new_project_configs + ');')
            
            # Add project-level configurations
            project_build_configs = f"""		{project_dev_uuid} /* Development */ = {{
			isa = XCBuildConfiguration;
			baseConfigurationReference = {config_uuids['dev_config']} /* Development.xcconfig */;
			buildSettings = {{
				ALWAYS_SEARCH_USER_PATHS = NO;
				ASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS = YES;
				CLANG_ANALYZER_NONNULL = YES;
				CLANG_ANALYZER_NUMBER_OBJECT_CONVERSION = YES_AGGRESSIVE;
				CLANG_CXX_LANGUAGE_STANDARD = "gnu++20";
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				CLANG_ENABLE_OBJC_WEAK = YES;
				CLANG_WARN_BLOCK_CAPTURE_AUTORELEASING = YES;
				CLANG_WARN_BOOL_CONVERSION = YES;
				CLANG_WARN_COMMA = YES;
				CLANG_WARN_CONSTANT_CONVERSION = YES;
				CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS = YES;
				CLANG_WARN_DIRECT_OBJC_ISA_USAGE = YES_ERROR;
				CLANG_WARN_DOCUMENTATION_COMMENTS = YES;
				CLANG_WARN_EMPTY_BODY = YES;
				CLANG_WARN_ENUM_CONVERSION = YES;
				CLANG_WARN_INFINITE_RECURSION = YES;
				CLANG_WARN_INT_CONVERSION = YES;
				CLANG_WARN_NON_LITERAL_NULL_CONVERSION = YES;
				CLANG_WARN_OBJC_IMPLICIT_RETAIN_SELF = YES;
				CLANG_WARN_OBJC_LITERAL_CONVERSION = YES;
				CLANG_WARN_OBJC_ROOT_CLASS = YES_ERROR;
				CLANG_WARN_QUOTED_INCLUDE_IN_FRAMEWORK_HEADER = YES;
				CLANG_WARN_RANGE_LOOP_ANALYSIS = YES;
				CLANG_WARN_STRICT_PROTOTYPES = YES;
				CLANG_WARN_SUSPICIOUS_MOVE = YES;
				CLANG_WARN_UNGUARDED_AVAILABILITY = YES_AGGRESSIVE;
				CLANG_WARN_UNREACHABLE_CODE = YES;
				CLANG_WARN__DUPLICATE_METHOD_MATCH = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = dwarf;
				DEVELOPMENT_TEAM = PSXDB5A2NN;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				ENABLE_TESTABILITY = YES;
				ENABLE_USER_SCRIPT_SANDBOXING = YES;
				GCC_C_LANGUAGE_STANDARD = gnu17;
				GCC_DYNAMIC_NO_PIC = NO;
				GCC_NO_COMMON_BLOCKS = YES;
				GCC_OPTIMIZATION_LEVEL = 0;
				GCC_PREPROCESSOR_DEFINITIONS = (
					"DEBUG=1",
					"DEVELOPMENT=1",
					"$(inherited)",
				);
				GCC_WARN_64_TO_32_BIT_CONVERSION = YES;
				GCC_WARN_ABOUT_RETURN_TYPE = YES_ERROR;
				GCC_WARN_UNDECLARED_SELECTOR = YES;
				GCC_WARN_UNINITIALIZED_AUTOS = YES_AGGRESSIVE;
				GCC_WARN_UNUSED_FUNCTION = YES;
				GCC_WARN_UNUSED_VARIABLE = YES;
				IPHONEOS_DEPLOYMENT_TARGET = 15.0;
				LOCALIZATION_PREFERS_STRING_CATALOGS = YES;
				MTL_ENABLE_DEBUG_INFO = INCLUDE_SOURCE;
				MTL_FAST_MATH = YES;
				ONLY_ACTIVE_ARCH = YES;
				SDKROOT = iphoneos;
				SWIFT_ACTIVE_COMPILATION_CONDITIONS = "DEBUG DEVELOPMENT $(inherited)";
				SWIFT_OPTIMIZATION_LEVEL = "-Onone";
			}};
			name = Development;
		}};
		{project_staging_uuid} /* Staging */ = {{
			isa = XCBuildConfiguration;
			baseConfigurationReference = {config_uuids['staging_config']} /* Staging.xcconfig */;
			buildSettings = {{
				ALWAYS_SEARCH_USER_PATHS = NO;
				ASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS = YES;
				CLANG_ANALYZER_NONNULL = YES;
				CLANG_ANALYZER_NUMBER_OBJECT_CONVERSION = YES_AGGRESSIVE;
				CLANG_CXX_LANGUAGE_STANDARD = "gnu++20";
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				CLANG_ENABLE_OBJC_WEAK = YES;
				CLANG_WARN_BLOCK_CAPTURE_AUTORELEASING = YES;
				CLANG_WARN_BOOL_CONVERSION = YES;
				CLANG_WARN_COMMA = YES;
				CLANG_WARN_CONSTANT_CONVERSION = YES;
				CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS = YES;
				CLANG_WARN_DIRECT_OBJC_ISA_USAGE = YES_ERROR;
				CLANG_WARN_DOCUMENTATION_COMMENTS = YES;
				CLANG_WARN_EMPTY_BODY = YES;
				CLANG_WARN_ENUM_CONVERSION = YES;
				CLANG_WARN_INFINITE_RECURSION = YES;
				CLANG_WARN_INT_CONVERSION = YES;
				CLANG_WARN_NON_LITERAL_NULL_CONVERSION = YES;
				CLANG_WARN_OBJC_IMPLICIT_RETAIN_SELF = YES;
				CLANG_WARN_OBJC_LITERAL_CONVERSION = YES;
				CLANG_WARN_OBJC_ROOT_CLASS = YES_ERROR;
				CLANG_WARN_QUOTED_INCLUDE_IN_FRAMEWORK_HEADER = YES;
				CLANG_WARN_RANGE_LOOP_ANALYSIS = YES;
				CLANG_WARN_STRICT_PROTOTYPES = YES;
				CLANG_WARN_SUSPICIOUS_MOVE = YES;
				CLANG_WARN_UNGUARDED_AVAILABILITY = YES_AGGRESSIVE;
				CLANG_WARN_UNREACHABLE_CODE = YES;
				CLANG_WARN__DUPLICATE_METHOD_MATCH = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = "dwarf-with-dsym";
				DEVELOPMENT_TEAM = PSXDB5A2NN;
				ENABLE_NS_ASSERTIONS = NO;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				ENABLE_USER_SCRIPT_SANDBOXING = YES;
				GCC_C_LANGUAGE_STANDARD = gnu17;
				GCC_NO_COMMON_BLOCKS = YES;
				GCC_OPTIMIZATION_LEVEL = s;
				GCC_PREPROCESSOR_DEFINITIONS = (
					"STAGING=1",
					"$(inherited)",
				);
				GCC_WARN_64_TO_32_BIT_CONVERSION = YES;
				GCC_WARN_ABOUT_RETURN_TYPE = YES_ERROR;
				GCC_WARN_UNDECLARED_SELECTOR = YES;
				GCC_WARN_UNINITIALIZED_AUTOS = YES_AGGRESSIVE;
				GCC_WARN_UNUSED_FUNCTION = YES;
				GCC_WARN_UNUSED_VARIABLE = YES;
				IPHONEOS_DEPLOYMENT_TARGET = 15.0;
				LOCALIZATION_PREFERS_STRING_CATALOGS = YES;
				MTL_ENABLE_DEBUG_INFO = NO;
				MTL_FAST_MATH = YES;
				ONLY_ACTIVE_ARCH = NO;
				SDKROOT = iphoneos;
				SWIFT_ACTIVE_COMPILATION_CONDITIONS = "STAGING $(inherited)";
				SWIFT_COMPILATION_MODE = wholemodule;
				SWIFT_OPTIMIZATION_LEVEL = "-O";
				VALIDATE_PRODUCT = YES;
			}};
			name = Staging;
		}};
		{project_prod_uuid} /* Production */ = {{
			isa = XCBuildConfiguration;
			baseConfigurationReference = {config_uuids['prod_config']} /* Production.xcconfig */;
			buildSettings = {{
				ALWAYS_SEARCH_USER_PATHS = NO;
				ASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS = YES;
				CLANG_ANALYZER_NONNULL = YES;
				CLANG_ANALYZER_NUMBER_OBJECT_CONVERSION = YES_AGGRESSIVE;
				CLANG_CXX_LANGUAGE_STANDARD = "gnu++20";
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				CLANG_ENABLE_OBJC_WEAK = YES;
				CLANG_WARN_BLOCK_CAPTURE_AUTORELEASING = YES;
				CLANG_WARN_BOOL_CONVERSION = YES;
				CLANG_WARN_COMMA = YES;
				CLANG_WARN_CONSTANT_CONVERSION = YES;
				CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS = YES;
				CLANG_WARN_DIRECT_OBJC_ISA_USAGE = YES_ERROR;
				CLANG_WARN_DOCUMENTATION_COMMENTS = YES;
				CLANG_WARN_EMPTY_BODY = YES;
				CLANG_WARN_ENUM_CONVERSION = YES;
				CLANG_WARN_INFINITE_RECURSION = YES;
				CLANG_WARN_INT_CONVERSION = YES;
				CLANG_WARN_NON_LITERAL_NULL_CONVERSION = YES;
				CLANG_WARN_OBJC_IMPLICIT_RETAIN_SELF = YES;
				CLANG_WARN_OBJC_LITERAL_CONVERSION = YES;
				CLANG_WARN_OBJC_ROOT_CLASS = YES_ERROR;
				CLANG_WARN_QUOTED_INCLUDE_IN_FRAMEWORK_HEADER = YES;
				CLANG_WARN_RANGE_LOOP_ANALYSIS = YES;
				CLANG_WARN_STRICT_PROTOTYPES = YES;
				CLANG_WARN_SUSPICIOUS_MOVE = YES;
				CLANG_WARN_UNGUARDED_AVAILABILITY = YES_AGGRESSIVE;
				CLANG_WARN_UNREACHABLE_CODE = YES;
				CLANG_WARN__DUPLICATE_METHOD_MATCH = YES;
				COPY_PHASE_STRIP = YES;
				DEBUG_INFORMATION_FORMAT = "dwarf-with-dsym";
				DEPLOYMENT_POSTPROCESSING = YES;
				DEVELOPMENT_TEAM = PSXDB5A2NN;
				ENABLE_NS_ASSERTIONS = NO;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				ENABLE_USER_SCRIPT_SANDBOXING = YES;
				GCC_C_LANGUAGE_STANDARD = gnu17;
				GCC_NO_COMMON_BLOCKS = YES;
				GCC_OPTIMIZATION_LEVEL = s;
				GCC_PREPROCESSOR_DEFINITIONS = (
					"PRODUCTION=1",
					"NDEBUG=1",
					"$(inherited)",
				);
				GCC_WARN_64_TO_32_BIT_CONVERSION = YES;
				GCC_WARN_ABOUT_RETURN_TYPE = YES_ERROR;
				GCC_WARN_UNDECLARED_SELECTOR = YES;
				GCC_WARN_UNINITIALIZED_AUTOS = YES_AGGRESSIVE;
				GCC_WARN_UNUSED_FUNCTION = YES;
				GCC_WARN_UNUSED_VARIABLE = YES;
				IPHONEOS_DEPLOYMENT_TARGET = 15.0;
				LOCALIZATION_PREFERS_STRING_CATALOGS = YES;
				MTL_ENABLE_DEBUG_INFO = NO;
				MTL_FAST_MATH = YES;
				ONLY_ACTIVE_ARCH = NO;
				SDKROOT = iphoneos;
				SWIFT_ACTIVE_COMPILATION_CONDITIONS = "PRODUCTION $(inherited)";
				SWIFT_COMPILATION_MODE = wholemodule;
				SWIFT_OPTIMIZATION_LEVEL = "-O";
				VALIDATE_PRODUCT = YES;
			}};
			name = Production;
		}};
"""
            
            content = content[:build_configs_end] + project_build_configs + content[build_configs_end:]
        
        return content
        
    def update_default_configuration(self, content):
        """Set the default build configuration to Development"""
        # Find and update defaultConfigurationName
        default_config_pattern = r'(defaultConfigurationName = ")[^"]*(")'
        content = re.sub(default_config_pattern, r'\1Development\2', content)
        
        return content
        
    def configure_project(self):
        """Main method to configure the Xcode project"""
        print("🔧 Configuring OMEGA Pro AI Xcode project...")
        
        # Check if configuration files exist
        if not self.configurations_path.exists():
            print(f"❌ Configurations directory not found: {self.configurations_path}")
            return False
            
        config_files = ['Development.xcconfig', 'Staging.xcconfig', 'Production.xcconfig']
        for config_file in config_files:
            config_path = self.configurations_path / config_file
            if not config_path.exists():
                print(f"❌ Configuration file not found: {config_path}")
                return False
                
        # Backup the original project file
        self.backup_project_file()
        
        # Read the current project file
        content = self.read_project_file()
        
        # Add configuration files to project
        content, config_uuids = self.add_configuration_files_to_project(content)
        print("✅ Added configuration files to project")
        
        # Create build configurations
        content = self.create_build_configurations(content, config_uuids)
        print("✅ Created Development, Staging, and Production build configurations")
        
        # Update default configuration
        content = self.update_default_configuration(content)
        print("✅ Set default configuration to Development")
        
        # Write the modified project file
        self.write_project_file(content)
        print("✅ Updated project.pbxproj file")
        
        print("\n🎉 Xcode project configuration completed successfully!")
        print("📋 Next steps:")
        print("   1. Open the Xcode project")
        print("   2. Verify the build configurations in Project Settings")
        print("   3. Test building with different configurations")
        print("   4. Configure code signing for each environment")
        
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 configure_xcode_project.py <path_to_xcodeproj>")
        sys.exit(1)
        
    project_path = sys.argv[1]
    if not os.path.exists(project_path):
        print(f"❌ Xcode project not found: {project_path}")
        sys.exit(1)
        
    configurator = XcodeProjectConfigurator(project_path)
    success = configurator.configure_project()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()