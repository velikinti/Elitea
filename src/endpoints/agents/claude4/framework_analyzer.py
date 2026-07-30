import os
from pathlib import Path
from typing import Dict, List, Optional
import logging
import openai
from openai import AzureOpenAI
import json
import re
from endpoints.prompts.claude4 import (
    get_framework_analysis_prompt,
    get_framework_analysis_system_message as get_system_message
)

logger = logging.getLogger(__name__)

class FrameworkAnalysis:
    """Represents the analysis results of a test framework."""
    
    def __init__(self):
        self.base_classes = {}
        self.utility_functions = {}
        self.patterns = {
            'test_setup': [],
            'assertions': [],
            'request_patterns': [],
            'response_handling': [],
            'test_markers': [],
            'data_patterns': [],
            'documentation': [],
            'imports': []
        }
        self.client_class = None
        self.response_class = None
        self.assertion_utils = None
        self.test_organization = {
            'markers': [],
            'grouping': '',
            'method_signatures': [],
            'data_setup': []
        }
        self.conventions = {
            'naming': '',
            'organization': '',
            'structure': '',
            'documentation': '',
            'error_handling': '',
            'validation': ''
        }
        self.validation_patterns = {
            'status_checks': [],
            'content_checks': [],
            'error_checks': [],
            'custom_checks': []
        }
    
    def to_dict(self) -> dict:
        """Convert FrameworkAnalysis instance to dictionary for serialization."""
        return {
            'base_classes': self.base_classes,
            'utility_functions': self.utility_functions,
            'patterns': self.patterns,
            'client_class': self.client_class,
            'response_class': self.response_class,
            'assertion_utils': self.assertion_utils,
            'test_organization': self.test_organization,
            'conventions': self.conventions,
            'validation_patterns': self.validation_patterns
        }
    
    def to_markdown(self) -> str:
        """Convert FrameworkAnalysis instance to markdown format."""
        md_lines = []
        md_lines.append("# Framework Analysis Results\n")
        md_lines.append("## Overview\n")
        md_lines.append("This document describes the structure, components, and patterns of the test framework.\n")
        
        # Framework Structure
        md_lines.append("\n## Framework Structure\n")
        md_lines.append("The framework has three main modules:\n")
        md_lines.append("1. **framework/api/** - API testing components\n")
        md_lines.append("2. **framework/ui/** - UI/Web testing components\n")
        md_lines.append("3. **framework/core/** - Core utilities and shared components\n")
        
        # Organize Base Classes by Module
        md_lines.append("\n## Base Classes\n")
        
        # Separate classes by component type
        api_classes = {}
        ui_classes = {}
        core_classes = {}
        
        if self.base_classes:
            for class_name, class_info in self.base_classes.items():
                if isinstance(class_info, dict):
                    component_type = class_info.get('component_type', '').lower()
                    if component_type == 'api':
                        api_classes[class_name] = class_info
                    elif component_type == 'ui':
                        ui_classes[class_name] = class_info
                    else:  # common, core, or empty
                        core_classes[class_name] = class_info
        
        # API Classes Section
        if api_classes:
            md_lines.append("\n### API Components (framework/api/)\n")
            for class_name, class_info in api_classes.items():
                file_path = class_info.get('file', 'Unknown')
                description = class_info.get('description') or class_info.get('purpose') or 'No description available'
                import_path = class_info.get('import_path', '')
                key_methods = class_info.get('key_methods', [])
                
                md_lines.append(f"#### {class_name}\n")
                md_lines.append(f"- **File**: `{file_path}`\n")
                if import_path:
                    md_lines.append(f"- **Import**: `{import_path}`\n")
                md_lines.append(f"- **Description**: {description}\n")
                if key_methods:
                    md_lines.append(f"- **Key Methods**:\n")
                    for method in key_methods[:5]:  # Limit to 5 methods
                        if isinstance(method, dict):
                            method_name = method.get('name', '')
                            method_sig = method.get('signature', '')
                            method_desc = method.get('description', '')
                            if method_sig:
                                md_lines.append(f"  - `{method_sig}`")
                                if method_desc:
                                    md_lines.append(f" - {method_desc}")
                                md_lines.append("\n")
                            elif method_name:
                                md_lines.append(f"  - `{method_name}()`\n")
        
        # UI Classes Section
        if ui_classes:
            md_lines.append("\n### UI Components (framework/ui/)\n")
            for class_name, class_info in ui_classes.items():
                file_path = class_info.get('file', 'Unknown')
                description = class_info.get('description') or class_info.get('purpose') or 'No description available'
                import_path = class_info.get('import_path', '')
                key_methods = class_info.get('key_methods', [])
                
                md_lines.append(f"#### {class_name}\n")
                md_lines.append(f"- **File**: `{file_path}`\n")
                if import_path:
                    md_lines.append(f"- **Import**: `{import_path}`\n")
                md_lines.append(f"- **Description**: {description}\n")
                if key_methods:
                    md_lines.append(f"- **Key Methods**:\n")
                    for method in key_methods[:5]:  # Limit to 5 methods
                        if isinstance(method, dict):
                            method_name = method.get('name', '')
                            method_sig = method.get('signature', '')
                            method_desc = method.get('description', '')
                            if method_sig:
                                md_lines.append(f"  - `{method_sig}`")
                                if method_desc:
                                    md_lines.append(f" - {method_desc}")
                                md_lines.append("\n")
                            elif method_name:
                                md_lines.append(f"  - `{method_name}()`\n")
        
        # Core/Common Classes Section
        if core_classes:
            md_lines.append("\n### Core Components (framework/core/)\n")
            for class_name, class_info in core_classes.items():
                file_path = class_info.get('file', 'Unknown')
                description = class_info.get('description') or class_info.get('purpose') or 'No description available'
                import_path = class_info.get('import_path', '')
                key_methods = class_info.get('key_methods', [])
                
                md_lines.append(f"#### {class_name}\n")
                md_lines.append(f"- **File**: `{file_path}`\n")
                if import_path:
                    md_lines.append(f"- **Import**: `{import_path}`\n")
                md_lines.append(f"- **Description**: {description}\n")
                if key_methods:
                    md_lines.append(f"- **Key Methods**:\n")
                    for method in key_methods[:5]:  # Limit to 5 methods
                        if isinstance(method, dict):
                            method_name = method.get('name', '')
                            method_sig = method.get('signature', '')
                            method_desc = method.get('description', '')
                            if method_sig:
                                md_lines.append(f"  - `{method_sig}`")
                                if method_desc:
                                    md_lines.append(f" - {method_desc}")
                                md_lines.append("\n")
                            elif method_name:
                                md_lines.append(f"  - `{method_name}()`\n")
        
        if not api_classes and not ui_classes and not core_classes:
            md_lines.append("No base classes found.\n")
        
        # Client Class - Show in appropriate module section
        md_lines.append("\n## Client Class\n")
        if self.client_class and isinstance(self.client_class, dict):
            name = self.client_class.get('name', 'Not found')
            file_path = self.client_class.get('file', 'Unknown')
            description = self.client_class.get('description') or self.client_class.get('purpose', '')
            import_path = self.client_class.get('import_path', '')
            key_methods = self.client_class.get('key_methods', [])
            component_type = self.client_class.get('component_type', '').upper()
            
            md_lines.append(f"- **Name**: {name}\n")
            if component_type:
                md_lines.append(f"- **Module**: {component_type}\n")
            md_lines.append(f"- **File**: `{file_path}`\n")
            if import_path:
                md_lines.append(f"- **Import**: `{import_path}`\n")
            if description:
                md_lines.append(f"- **Description**: {description}\n")
            if key_methods:
                md_lines.append(f"- **Key Methods**:\n")
                for method in key_methods[:5]:
                    if isinstance(method, dict):
                        method_sig = method.get('signature', '')
                        method_desc = method.get('description', '')
                        if method_sig:
                            md_lines.append(f"  - `{method_sig}`")
                            if method_desc:
                                md_lines.append(f" - {method_desc}")
                            md_lines.append("\n")
        else:
            md_lines.append("No client class identified.\n")
        
        # Response Class - Show in appropriate module section
        md_lines.append("\n## Response Class\n")
        if self.response_class and isinstance(self.response_class, dict):
            name = self.response_class.get('name', 'Not found')
            file_path = self.response_class.get('file', 'Unknown')
            description = self.response_class.get('description') or self.response_class.get('purpose', '')
            import_path = self.response_class.get('import_path', '')
            key_methods = self.response_class.get('key_methods', [])
            component_type = self.response_class.get('component_type', '').upper()
            
            md_lines.append(f"- **Name**: {name}\n")
            if component_type:
                md_lines.append(f"- **Module**: {component_type}\n")
            md_lines.append(f"- **File**: `{file_path}`\n")
            if import_path:
                md_lines.append(f"- **Import**: `{import_path}`\n")
            if description:
                md_lines.append(f"- **Description**: {description}\n")
            if key_methods:
                md_lines.append(f"- **Key Methods**:\n")
                for method in key_methods[:5]:
                    if isinstance(method, dict):
                        method_sig = method.get('signature', '')
                        method_desc = method.get('description', '')
                        if method_sig:
                            md_lines.append(f"  - `{method_sig}`")
                            if method_desc:
                                md_lines.append(f" - {method_desc}")
                            md_lines.append("\n")
        else:
            md_lines.append("No response class identified.\n")
        
        # Assertion Utils - Show in appropriate module section
        md_lines.append("\n## Assertion Utilities\n")
        if self.assertion_utils and isinstance(self.assertion_utils, dict):
            name = self.assertion_utils.get('name', 'Not found')
            file_path = self.assertion_utils.get('file', 'Unknown')
            description = self.assertion_utils.get('description') or self.assertion_utils.get('purpose', '')
            import_path = self.assertion_utils.get('import_path', '')
            signature = self.assertion_utils.get('signature', '')
            usage_pattern = self.assertion_utils.get('usage_pattern', '')
            component_type = self.assertion_utils.get('component_type', '').upper()
            
            md_lines.append(f"- **Name**: {name}\n")
            if component_type:
                md_lines.append(f"- **Module**: {component_type}\n")
            md_lines.append(f"- **File**: `{file_path}`\n")
            if import_path:
                md_lines.append(f"- **Import**: `{import_path}`\n")
            if signature:
                md_lines.append(f"- **Signature**: `{signature}`\n")
            if description:
                md_lines.append(f"- **Description**: {description}\n")
            if usage_pattern:
                md_lines.append(f"- **Usage Pattern**: {usage_pattern}\n")
        else:
            md_lines.append("No assertion utilities identified.\n")
        
        # Utility Functions - Organized by Module
        md_lines.append("\n## Utility Functions\n")
        
        # Separate utility functions by module
        api_utils = {}
        ui_utils = {}
        core_utils = {}
        
        if self.utility_functions:
            for func_name, func_info in self.utility_functions.items():
                if isinstance(func_info, dict):
                    file_path = func_info.get('file', 'Unknown').lower()
                    # Determine module based on file path
                    if 'api' in file_path and 'ui' not in file_path:
                        api_utils[func_name] = func_info
                    elif 'ui' in file_path and 'api' not in file_path:
                        ui_utils[func_name] = func_info
                    elif 'core' in file_path:
                        core_utils[func_name] = func_info
                    else:
                        # Default to core if unclear
                        core_utils[func_name] = func_info
        
        # API Utilities Section
        if api_utils:
            md_lines.append("\n### API Utilities (framework/api/)\n")
            for func_name, func_info in api_utils.items():
                file_path = func_info.get('file', 'Unknown')
                description = func_info.get('description') or func_info.get('purpose', 'No description available')
                import_path = func_info.get('import_path', '')
                signature = func_info.get('signature', '')
                usage_pattern = func_info.get('usage_pattern', '')
                
                md_lines.append(f"#### {func_name}\n")
                md_lines.append(f"- **File**: `{file_path}`\n")
                if import_path:
                    md_lines.append(f"- **Import**: `{import_path}`\n")
                if signature:
                    md_lines.append(f"- **Signature**: `{signature}`\n")
                md_lines.append(f"- **Description**: {description}\n")
                if usage_pattern:
                    md_lines.append(f"- **Usage Pattern**: {usage_pattern}\n")
        
        # UI Utilities Section
        if ui_utils:
            md_lines.append("\n### UI Utilities (framework/ui/)\n")
            for func_name, func_info in ui_utils.items():
                file_path = func_info.get('file', 'Unknown')
                description = func_info.get('description') or func_info.get('purpose', 'No description available')
                import_path = func_info.get('import_path', '')
                signature = func_info.get('signature', '')
                usage_pattern = func_info.get('usage_pattern', '')
                
                md_lines.append(f"#### {func_name}\n")
                md_lines.append(f"- **File**: `{file_path}`\n")
                if import_path:
                    md_lines.append(f"- **Import**: `{import_path}`\n")
                if signature:
                    md_lines.append(f"- **Signature**: `{signature}`\n")
                md_lines.append(f"- **Description**: {description}\n")
                if usage_pattern:
                    md_lines.append(f"- **Usage Pattern**: {usage_pattern}\n")
        
        # Core Utilities Section
        if core_utils:
            md_lines.append("\n### Core Utilities (framework/core/)\n")
            for func_name, func_info in core_utils.items():
                file_path = func_info.get('file', 'Unknown')
                description = func_info.get('description') or func_info.get('purpose', 'No description available')
                import_path = func_info.get('import_path', '')
                signature = func_info.get('signature', '')
                usage_pattern = func_info.get('usage_pattern', '')
                
                md_lines.append(f"#### {func_name}\n")
                md_lines.append(f"- **File**: `{file_path}`\n")
                if import_path:
                    md_lines.append(f"- **Import**: `{import_path}`\n")
                if signature:
                    md_lines.append(f"- **Signature**: `{signature}`\n")
                md_lines.append(f"- **Description**: {description}\n")
                if usage_pattern:
                    md_lines.append(f"- **Usage Pattern**: {usage_pattern}\n")
        
        if not api_utils and not ui_utils and not core_utils:
            md_lines.append("No utility functions found.\n")
        
        # Patterns
        md_lines.append("\n## Test Patterns\n")
        if self.patterns:
            for pattern_type, pattern_list in self.patterns.items():
                if pattern_list:
                    md_lines.append(f"### {pattern_type.replace('_', ' ').title()}\n")
                    for pattern in pattern_list:
                        if isinstance(pattern, str):
                            md_lines.append(f"- {pattern}\n")
                        elif isinstance(pattern, dict):
                            md_lines.append(f"- {pattern.get('description', str(pattern))}\n")
        else:
            md_lines.append("No patterns identified.\n")
        
        # Test Organization
        md_lines.append("\n## Test Organization\n")
        if self.test_organization:
            if self.test_organization.get('markers'):
                md_lines.append(f"### Test Markers\n")
                for marker in self.test_organization['markers']:
                    md_lines.append(f"- {marker}\n")
            if self.test_organization.get('grouping'):
                md_lines.append(f"### Grouping Strategy\n")
                md_lines.append(f"{self.test_organization['grouping']}\n")
            if self.test_organization.get('method_signatures'):
                md_lines.append(f"### Common Test Method Signatures\n")
                for sig in self.test_organization['method_signatures'][:10]:  # Limit to 10
                    md_lines.append(f"- `{sig}`\n")
            if self.test_organization.get('data_setup'):
                md_lines.append(f"### Data Setup Patterns\n")
                for pattern in self.test_organization['data_setup'][:5]:
                    md_lines.append(f"- {pattern}\n")
        else:
            md_lines.append("No test organization patterns identified.\n")
        
        # Conventions
        md_lines.append("\n## Framework Conventions\n")
        if self.conventions:
            for convention_type, convention_value in self.conventions.items():
                if convention_value:
                    md_lines.append(f"### {convention_type.replace('_', ' ').title()}\n")
                    md_lines.append(f"{convention_value}\n")
        
        # Validation Patterns
        md_lines.append("\n## Validation Patterns\n")
        if self.validation_patterns:
            for pattern_type, pattern_list in self.validation_patterns.items():
                if pattern_list:
                    md_lines.append(f"### {pattern_type.replace('_', ' ').title()}\n")
                    for pattern in pattern_list:
                        if isinstance(pattern, str):
                            md_lines.append(f"- {pattern}\n")
                        elif isinstance(pattern, dict):
                            md_lines.append(f"- {pattern.get('description', str(pattern))}\n")
        else:
            md_lines.append("No validation patterns identified.\n")
        
        return "\n".join(md_lines)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FrameworkAnalysis':
        """Create FrameworkAnalysis instance from dictionary."""
        analysis = cls()
        analysis.base_classes = data.get('base_classes', {})
        analysis.utility_functions = data.get('utility_functions', {})
        analysis.patterns = data.get('patterns', {})
        analysis.client_class = data.get('client_class')
        analysis.response_class = data.get('response_class')
        analysis.assertion_utils = data.get('assertion_utils')
        analysis.test_organization = data.get('test_organization', {})
        analysis.conventions = data.get('conventions', {})
        analysis.validation_patterns = data.get('validation_patterns', {})
        return analysis
    
    @classmethod
    def from_llm_response(cls, llm_response: dict) -> 'FrameworkAnalysis':
        """Create FrameworkAnalysis instance from LLM response."""
        analysis = cls()
        analysis.base_classes = llm_response.get('base_classes', {})
        analysis.utility_functions = llm_response.get('utility_functions', {})
        analysis.patterns = llm_response.get('patterns', {})
        analysis.client_class = llm_response.get('client_class')
        analysis.response_class = llm_response.get('response_class')
        analysis.assertion_utils = llm_response.get('assertion_utils')
        analysis.test_organization = llm_response.get('test_organization', {})
        analysis.conventions = llm_response.get('conventions', {})
        analysis.validation_patterns = llm_response.get('validation_patterns', {})
        return analysis

class FrameworkAnalyzer:
    """Analyzes test framework structure and patterns using LLM."""

    def __init__(self, framework_path: str, api_key: str = None):
        """Initialize analyzer with framework path and API key."""
        self.framework_path = framework_path
        self.api_key = api_key or "dial-cvq36jrf2xxt4sktnhl826j15ro"
        openai.api_key = self.api_key
        self.llm_client = AzureOpenAI(
            api_key=self.api_key,
            api_version="2024-02-01",
            azure_endpoint="https://ai-proxy.lab.epam.com"
        )
        
    def analyze(self) -> FrameworkAnalysis:
        """Analyze the framework using LLM and return results."""
        try:
            # Collect framework code
            framework_code = self._collect_framework_code()
            
            # Validate that we have code content
            if not framework_code or len(framework_code.strip()) < 100:
                error_msg = f"Framework code collection returned empty or insufficient content. Framework path: {self.framework_path}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"Framework code collected: {len(framework_code)} characters")
            logger.debug(f"First 500 chars of framework code: {framework_code[:500]}")
            
            # Get LLM analysis
            prompt = get_framework_analysis_prompt(self.framework_path)
            user_content = f"{prompt}\n\nAnalyze this test framework code:\n\n{framework_code}"
            
            logger.info(f"Sending analysis request to LLM (prompt: {len(prompt)} chars, code: {len(framework_code)} chars)")
            
            completion = self.llm_client.chat.completions.create(
                model="claude-sonnet-4@20250514",
                messages=[
                    {"role": "system", "content": get_system_message()},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=16384,  # Reduced from 16384 for faster processing
                temperature=0.3
            )
            
            # Parse LLM response
            analysis_text = completion.choices[0].message.content.strip()
            logger.info(f"LLM response received: {len(analysis_text)} characters")
            logger.debug(f"First 1000 chars of LLM response: {analysis_text[:1000]}")
            
            try:
                analysis_json = json.loads(analysis_text)
                analysis = FrameworkAnalysis.from_llm_response(analysis_json)
                logger.info("Framework analysis completed successfully using LLM")
                return analysis
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response as direct JSON: {str(e)}")
                # If LLM returns markdown or extra text, extract JSON
                match = re.search(r"\{.*\}", analysis_text, re.DOTALL)
                if match:
                    try:
                        analysis_json = json.loads(match.group(0))
                        analysis = FrameworkAnalysis.from_llm_response(analysis_json)
                        logger.info("Framework analysis completed successfully using LLM (extracted from text)")
                        return analysis
                    except json.JSONDecodeError as e2:
                        logger.error(f"Failed to parse extracted JSON: {str(e2)}")
                        logger.error(f"LLM response content: {analysis_text[:2000]}")
                        raise ValueError(f"LLM response is not valid JSON. Response preview: {analysis_text[:500]}")
                else:
                    logger.error(f"No JSON found in LLM response. Response: {analysis_text[:2000]}")
                    raise ValueError(f"LLM response does not contain valid JSON. Response preview: {analysis_text[:500]}")
                
        except Exception as e:
            logger.error(f"Framework analysis failed: {str(e)}")
            # Fall back to basic analysis
            return self._basic_analysis()
    
    def _collect_framework_code(self) -> str:
        """Collect all Python files in the framework directory."""
        framework_files = []
        
        # Validate framework path exists
        if not os.path.exists(self.framework_path):
            error_msg = f"Framework path does not exist: {self.framework_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if not os.path.isdir(self.framework_path):
            error_msg = f"Framework path is not a directory: {self.framework_path}"
            logger.error(error_msg)
            raise NotADirectoryError(error_msg)
        
        framework_root_name = os.path.basename(os.path.normpath(self.framework_path))
        logger.info(f"Collecting framework code from: {self.framework_path}")
        logger.info(f"Framework root name: {framework_root_name}")
        
        files_collected = 0
        for root, dirs, files in os.walk(self.framework_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    file_path = os.path.join(root, file)
                    # Get relative path from framework root
                    rel_path = os.path.relpath(file_path, self.framework_path)
                    # Convert to import path format (replace \ with /, remove .py)
                    import_path = rel_path.replace(os.sep, '.').replace('.py', '')
                    # Construct full import path with framework root
                    full_import_path = f"{framework_root_name}.{import_path}"
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            framework_files.append(
                                f"# File: {rel_path}\n"
                                f"# Full Path: {file_path}\n"
                                f"# Import Path: {full_import_path}\n"
                                f"{content}\n"
                            )
                            files_collected += 1
                    except Exception as e:
                        logger.warning(f"Failed to read {file_path}: {str(e)}")
        
        logger.info(f"Collected {files_collected} Python files from framework")
        
        if files_collected == 0:
            error_msg = f"No Python files found in framework path: {self.framework_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Detect which directories exist in the framework
        detected_dirs = []
        if os.path.exists(os.path.join(self.framework_path, "api")):
            detected_dirs.append("api")
        if os.path.exists(os.path.join(self.framework_path, "ui")):
            detected_dirs.append("ui")
        if os.path.exists(os.path.join(self.framework_path, "core")):
            detected_dirs.append("core")
        
        dirs_list = ", ".join(detected_dirs) if detected_dirs else "none detected"
        
        # Add framework structure information at the beginning
        structure_info = f"""
# FRAMEWORK STRUCTURE INFORMATION
# Framework Root: {framework_root_name}
# Framework Path: {self.framework_path}
# 
# DETECTED DIRECTORIES: {dirs_list}
# CRITICAL: You MUST extract components from ALL detected directories listed above!
# If you see "api, ui, core" above, you MUST extract from api/, ui/, AND core/ directories.
# If you see "api, core" above, you MUST extract from api/ AND core/ directories.
# DO NOT extract only from api/ - extract from ALL directories that exist!
#
# IMPORTANT: All import paths should start with '{framework_root_name}.' 
# For example, if a file is at framework/api/requests/base_api.py,
# the import path should be: from {framework_root_name}.api.requests.base_api import ClassName
#
# FOLDER STRUCTURE CATEGORIZATION:
# - Files in '{framework_root_name}/api/' or subdirectories → component_type: "api"
# - Files in '{framework_root_name}/ui/' or subdirectories → component_type: "ui"  
# - Files in '{framework_root_name}/core/' or subdirectories → component_type: "common"
# - Any other location → component_type: "common"
#
# CODE FILES START HERE:
"""
        return structure_info + "\n".join(framework_files)
            
    def _basic_analysis(self) -> FrameworkAnalysis:
        """Fallback basic analysis without LLM."""
        logger.info("Performing basic analysis without LLM")
        analysis = FrameworkAnalysis()
        
        for root, dirs, files in os.walk(self.framework_path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                    # Component identification - Identify API and UI components correctly
                    # Determine component type based on file path and class name
                    is_api_file = "api" in file_path.lower() and "ui" not in file_path.lower()
                    is_ui_file = "ui" in file_path.lower() and "api" not in file_path.lower()
                    
                    # Check for API client classes
                    if is_api_file:
                        if "class RestRequest" in content:
                            if not analysis.client_class:
                                analysis.client_class = {"name": "RestRequest", "file": file_path, "component_type": "api"}
                        elif "class APIClient" in content:
                            if not analysis.client_class:
                                analysis.client_class = {"name": "APIClient", "file": file_path, "component_type": "api"}
                        elif "class HttpClient" in content:
                            if not analysis.client_class:
                                analysis.client_class = {"name": "HttpClient", "file": file_path, "component_type": "api"}
                    
                    # Check for UI client classes (only if no API client found)
                    if is_ui_file and not analysis.client_class:
                        if "class Browser" in content:
                            analysis.client_class = {"name": "Browser", "file": file_path, "component_type": "ui"}
                        elif "class WebDriver" in content:
                            analysis.client_class = {"name": "WebDriver", "file": file_path, "component_type": "ui"}
                    
                    # Check for API response classes
                    if is_api_file:
                        if "class APIResponse" in content:
                            if not analysis.response_class:
                                analysis.response_class = {"name": "APIResponse", "file": file_path, "component_type": "api"}
                        elif "class RestResponse" in content:
                            if not analysis.response_class:
                                analysis.response_class = {"name": "RestResponse", "file": file_path, "component_type": "api"}
                    
                    # Check for UI response classes (only if no API response found)
                    if is_ui_file and not analysis.response_class:
                        if "class PageResponse" in content or "class WebResponse" in content:
                            response_name = "PageResponse" if "class PageResponse" in content else "WebResponse"
                            analysis.response_class = {"name": response_name, "file": file_path, "component_type": "ui"}
                    
                    # Extract base classes
                    class_matches = re.findall(r'^class\s+(\w+)(?:\([^)]+\))?:', content, re.MULTILINE)
                    for class_name in class_matches:
                        if class_name not in ['Exception', 'BaseException', 'object']:  # Skip built-in classes
                            if not analysis.base_classes:
                                analysis.base_classes = {}
                            if class_name not in analysis.base_classes:
                                # Extract docstring if available
                                docstring_match = re.search(
                                    rf'class\s+{class_name}.*?\n(?:.*?\n)?(\s*""".*?""")',
                                    content,
                                    re.DOTALL
                                )
                                description = "No description available"
                                if docstring_match:
                                    description = docstring_match.group(1).strip().strip('"""').strip("'''").strip()
                                
                                # Determine component type
                                component_type = "common"
                                if is_api_file:
                                    component_type = "api"
                                elif is_ui_file:
                                    component_type = "ui"
                                
                                # Get relative file path
                                rel_path = os.path.relpath(file_path, self.framework_path)
                                
                                analysis.base_classes[class_name] = {
                                    "file": rel_path,
                                    "description": description,
                                    "import_path": f"from {rel_path.replace(os.sep, '.').replace('.py', '')} import {class_name}",
                                    "component_type": component_type
                                }
                    
                    # Extract utility functions from helper/utils files
                    if "helper" in file_path.lower() or "utils" in file_path.lower() or "common" in file_path.lower():
                        func_matches = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
                        for func_name in func_matches:
                            if not analysis.utility_functions:
                                analysis.utility_functions = {}
                            if func_name not in analysis.utility_functions:
                                # Extract docstring if available
                                docstring_match = re.search(
                                    rf'def\s+{func_name}\s*\(.*?\n(?:.*?\n)?(\s*""".*?""")',
                                    content,
                                    re.DOTALL
                                )
                                description = "No description available"
                                if docstring_match:
                                    description = docstring_match.group(1).strip().strip('"""').strip("'''").strip()
                                
                                # Extract function signature
                                sig_match = re.search(rf'^def\s+{func_name}\s*\([^)]*\)', content, re.MULTILINE)
                                signature = sig_match.group(0) if sig_match else f"def {func_name}(...)"
                                
                                # Get relative file path
                                rel_path = os.path.relpath(file_path, self.framework_path)
                                
                                analysis.utility_functions[func_name] = {
                                    "file": rel_path,
                                    "description": description,
                                    "import_path": f"from {rel_path.replace(os.sep, '.').replace('.py', '')} import {func_name}",
                                    "signature": signature
                                }
                    
                    # Check for API assertion utilities (RestResponse class with validation methods)
                    if is_api_file:
                        if "class RestResponse" in content and "validate_status_code" in content:
                            if not analysis.assertion_utils:
                                # Extract docstring
                                docstring_match = re.search(
                                    r'class\s+RestResponse.*?\n(?:.*?\n)?(\s*""".*?""")',
                                    content,
                                    re.DOTALL
                                )
                                description = "REST Response Validator/Utility class for validation"
                                if docstring_match:
                                    description = docstring_match.group(1).strip().strip('"""').strip("'''").strip()
                                
                                rel_path = os.path.relpath(file_path, self.framework_path)
                                analysis.assertion_utils = {
                                    "name": "RestResponse",
                                    "file": rel_path,
                                    "description": description,
                                    "import_path": f"from {rel_path.replace(os.sep, '.').replace('.py', '')} import RestResponse",
                                    "component_type": "api"
                                }
                        elif "def assert_response" in content:
                            if not analysis.assertion_utils:
                                rel_path = os.path.relpath(file_path, self.framework_path)
                                analysis.assertion_utils = {"name": "assert_response", "file": rel_path, "component_type": "api"}
                        elif "def validate_response" in content:
                            if not analysis.assertion_utils:
                                rel_path = os.path.relpath(file_path, self.framework_path)
                                analysis.assertion_utils = {"name": "validate_response", "file": rel_path, "component_type": "api"}
                    
                    # Check for UI assertion utilities (only if no API assertion found)
                    if is_ui_file and not analysis.assertion_utils:
                        if "def assert_element" in content or "def verify_element" in content:
                            assert_name = "assert_element" if "def assert_element" in content else "verify_element"
                            rel_path = os.path.relpath(file_path, self.framework_path)
                            analysis.assertion_utils = {"name": assert_name, "file": rel_path, "component_type": "ui"}

                    # Extract imports
                    analysis.patterns['imports'].extend([
                        line.strip() for line in lines 
                        if line.strip().startswith(('import ', 'from ')) and not line.strip().startswith('#')
                    ])
                        
                    # Pattern extraction for test files
                    if "def test_" in content:
                        # Test markers and organization
                        analysis.test_organization['markers'].extend([
                            line.strip() for line in lines
                            if line.strip().startswith('@pytest.mark')
                        ])
                        
                        analysis.test_organization['method_signatures'].extend([
                            line.strip() for line in lines
                            if line.strip().startswith('def test_')
                        ])
                        
                        # Documentation patterns
                        analysis.patterns['documentation'].extend([
                            line.strip() for line in lines
                            if '"""' in line or "'''" in line
                        ])
                        
                        # Test setup and fixtures
                        analysis.patterns['test_setup'].extend([
                            line.strip() for line in lines
                            if any(p in line.lower() for p in ['def setup', '@pytest.fixture', 'client ='])
                        ])
                        
                        # Data setup patterns
                        analysis.test_organization['data_setup'].extend([
                            line.strip() for line in lines
                            if any(p in line for p in ['headers =', 'body =', 'query_params ='])
                        ])
                        
                        # Assertions and validation
                        analysis.patterns['assertions'].extend([
                            line.strip() for line in lines
                            if 'assert' in line and not line.strip().startswith('#')
                        ])
                        
                        # Request patterns
                        analysis.patterns['request_patterns'].extend([
                            line.strip() for line in lines
                            if any(p in line for p in ['client.request', 'client.get', 'client.post'])
                        ])
                        
                        # Response handling
                        analysis.patterns['response_handling'].extend([
                            line.strip() for line in lines
                            if 'response.' in line and not line.strip().startswith('#')
                        ])
                        
                        # Validation patterns
                        analysis.validation_patterns['status_checks'].extend([
                            line.strip() for line in lines
                            if 'expected_status_code' in line
                        ])
                        
                        analysis.validation_patterns['content_checks'].extend([
                            line.strip() for line in lines
                            if 'has_content_type' in line or 'response_not_empty' in line
                        ])
                        
                        analysis.validation_patterns['error_checks'].extend([
                            line.strip() for line in lines
                            if 'has_error_message' in line
                        ])
                        
                        analysis.validation_patterns['custom_checks'].extend([
                            line.strip() for line in lines
                            if 'response_time_under' in line or any(
                                custom in line for custom in ['custom_validation', 'check_', 'validate_']
                            )
                        ])
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze {file_path}: {str(e)}")
                    continue
        
        # Remove duplicates while preserving order
        for pattern_type in analysis.patterns:
            analysis.patterns[pattern_type] = list(dict.fromkeys(
                analysis.patterns[pattern_type]
            ))
            
        return analysis
        
    def _get_analysis_prompt(self) -> str:
        """Get the prompt for framework analysis."""
        framework_root_name = os.path.basename(os.path.normpath(self.framework_path))
        
        # Build prompt in parts to avoid f-string nesting issues
        prompt_start = f"""You are an expert test automation framework analyzer. Analyze the provided framework code and extract comprehensive details.

⚠️ CRITICAL FIRST STEP - CHECK FRAMEWORK STRUCTURE:
Before you start extracting, look at the "# FRAMEWORK STRUCTURE INFORMATION" section at the beginning of the code.
It shows "DETECTED DIRECTORIES: ..." - this tells you which directories (api/, ui/, core/) exist in the framework.
YOU MUST EXTRACT COMPONENTS FROM ALL DIRECTORIES LISTED THERE!

If the structure shows "api, ui, core" - you MUST extract from all three:
- Extract ALL classes and functions from api/ directory → component_type: "api"
- Extract ALL classes and functions from ui/ directory → component_type: "ui"  
- Extract ALL classes and functions from core/ directory → component_type: "common"

If you only extract from api/ and ignore ui/ and core/, your analysis is INCOMPLETE and WRONG!

CRITICAL REQUIREMENTS:
1. FIRST: Check the "# DETECTED DIRECTORIES" line in the framework structure information - extract from ALL listed directories
2. Extract descriptions from docstrings (class/function docstrings, not just comments)
3. Accurately identify and categorize components as API, UI, or common based on their ACTUAL FILE LOCATION in the folder structure
4. Extract method signatures with full parameter details including type hints
5. Include CORRECT import paths for all components - they MUST start with '{framework_root_name}.'
6. Extract usage patterns and examples from actual import statements in the code
7. Look at existing import statements in the code files to understand the correct import paths
8. Extract ALL classes and functions - do not skip any directory or file

FRAMEWORK ROOT AND IMPORT PATHS:
- The framework root directory is: '{framework_root_name}'
- ALL import paths MUST start with '{framework_root_name}.'
- Example: If a file is at {framework_root_name}/api/requests/base_api.py, the import should be: from {framework_root_name}.api.requests.base_api import ClassName
- Look at the actual import statements in the code files to see how they import from each other
- The "# Import Path:" comment in each file shows the correct import path - USE IT

COMPONENT TYPE CATEGORIZATION (BASED ON FILE LOCATION):
- Files in '{framework_root_name}/api/' or any subdirectory under api/ → component_type: "api"
- Files in '{framework_root_name}/ui/' or any subdirectory under ui/ → component_type: "ui"
- Files in '{framework_root_name}/core/' or any subdirectory under core/ → component_type: "common"
- Files in any other location → component_type: "common"
- DO NOT guess based on class names - use the actual file path location

⚠️ MANDATORY DIRECTORY SCANNING PROCESS:
You MUST follow this step-by-step process:

STEP 1: Check the "# DETECTED DIRECTORIES" line in the framework structure information
STEP 2: For EACH directory listed (api/, ui/, core/), do the following:
  a) Find ALL Python files in that directory and its subdirectories
  b) Extract ALL classes from those files
  c) Extract ALL functions from those files
  d) Categorize them based on directory:
     - Files in api/ → component_type: "api"
     - Files in ui/ → component_type: "ui"
     - Files in core/ → component_type: "common"

STEP 3: Verify you extracted from ALL directories:
  - If "api" is in DETECTED DIRECTORIES → You MUST have components with component_type: "api"
  - If "ui" is in DETECTED DIRECTORIES → You MUST have components with component_type: "ui"
  - If "core" is in DETECTED DIRECTORIES → You MUST have components with component_type: "common"

FAILURE TO EXTRACT FROM ALL DIRECTORIES WILL RESULT IN INCOMPLETE ANALYSIS!
If you see files in core/ directory, extract them as "common" type components
If you see files in ui/ directory, extract them as "ui" type components  
If you see files in api/ directory, extract them as "api" type components
DO NOT skip any directory - scan the entire framework structure

1. Framework Components (CRITICAL - Extract ALL of these from ALL directories):

- **Base classes**: MUST extract ALL classes found in the framework (every "class ClassName:" definition). For each class:
  * Extract full docstring description (class-level docstring, triple-quoted strings)
  * Extract ALL methods with full signatures (including parameters, return types, decorators like @staticmethod, @classmethod)
  * Extract CORRECT import path - check the "# Import Path:" comment in the file or construct from file location
  * Import path format: from {framework_root_name}.module.submodule import ClassName
  * Categorize component_type based on file location: "api" if in api/, "ui" if in ui/, "common" if in core/ or elsewhere
  * Examples of what to look for:
    - API classes: APIConfiguration, RestRequest, RestResponse, APIResponse, APIClient, HttpClient
    - UI classes: BasePage, BaseLocator, BaseWait, Browser, WebDriver, PageObject, ElementLocator
    - Common/Core classes: LoggerFactory, PropFileReader, ConfigReader, FileHandler, DataManager, BaseActions, BaseVerifications, Utils, Helpers
  * DO NOT skip any classes - scan every file in EVERY directory (api/, ui/, core/, and others) and list every class definition
  * If a directory exists but has no classes, explicitly note that in your analysis
  
- **Utility functions**: MUST extract ALL functions from helper/utility files. For each function:
  * Extract full docstring description (function-level docstring)
  * Extract complete method signature with all parameters and return types
  * Extract usage patterns from actual import statements and usage in the code
  * Extract CORRECT import path - check existing imports in the code or construct from file location
  * Import path format: from {framework_root_name}.module.submodule import function_name
  * Look in files under: helpers/, utils/, common/, core/ directories AND any other utility directories
  * Examples of what to look for:
    - API utilities: build_url, rest_response_handle, convert_to_json, files_to_upload, validate_params, check_json_response, handle_http_error
    - UI utilities: wait_for_element, click_element, get_text, fill_form, scroll_to_element, take_screenshot
    - Common/Core utilities: read_config, get_logger, parse_json, format_date, validate_data, file_operations, string_utils
  * DO NOT skip any functions - scan every helper/utils/common/core file in ALL directories and list every function definition
  * If utility directories exist but have no functions, explicitly note that in your analysis
  
- **Client classes**: Identify the main client classes used for making requests/interactions:
  * API clients: RestRequest, APIClient, HttpClient (usually in api/requests/ or api/ directory)
  * UI clients: Browser, WebDriver (usually in ui/utils/ or ui/ directory)
  * Categorize based on file location (api/ = "api", ui/ = "ui")
  * Extract all methods with signatures
  * Use CORRECT import path from file location
  
- **Response classes**: Identify response handling classes:
  * API responses: APIResponse, RestResponse (usually in api/response/ directory)
  * UI responses: PageResponse, WebResponse (usually in ui/ directory)
  * Extract all methods and properties with signatures
  * Use CORRECT import path from file location
  
- **Assertion utilities**: MUST identify ALL assertion/validation utilities:
  * Classes with validation methods (e.g., RestResponse with validate_status_code, validate_protocol_version, etc.)
  * Standalone assertion functions (e.g., assert_response, validate_response)
  * Extract ALL validation methods with full signatures
  * Extract usage patterns from test files or actual code
  * Use CORRECT import path from file location
  * Examples: RestResponse class with static validation methods, assert_response function, etc.
  
- **Test markers and decorators**: Extract all pytest markers used (@pytest.mark.*)
- **Fixtures**: Identify pytest fixtures and their purposes

2. Test Organization:
- Test grouping strategies (markers, folders, naming patterns)
- Test method signatures with full details
- Data preparation patterns
- Common setup/teardown approaches
- Test markers used in the framework

3. Testing Patterns:
- Request construction patterns with code examples
- Response validation approaches with method signatures
- Error handling strategies
- Custom validation methods with signatures
- Status code checking patterns
- Content validation patterns
- Error checking patterns

4. Framework Standards:
- Naming conventions (test methods, variables, classes)
- File organization and structure
- Documentation formats (docstring patterns)
- Error message patterns
- Validation step formats

5. Import Information:
- For each component, provide the import statement needed to use it
- Include full import paths (e.g., "from {framework_root_name}.api.requests.base_api import RestRequest")

Provide the analysis in the following JSON structure:
"""
        
        # JSON template as regular string (not f-string) to avoid nesting issues
        json_template = """{
    "base_classes": {
        "ClassName": {
            "file": "relative/path/to/file.py (relative to framework root)",
            "description": "Extract FULL docstring from class definition - detailed description of purpose and usage",
            "import_path": "from {FRAMEWORK_ROOT}.module.submodule import ClassName (MUST start with {FRAMEWORK_ROOT}.)",
            "key_methods": [
                {"name": "method_name", "signature": "def method_name(self, param1: str, param2: int) -> bool", "description": "Extract method docstring if available"},
                {"name": "property_name", "signature": "@property def property_name(self) -> return_type", "description": "For properties, extract property name and return type"}
            ],
            "component_type": "api" or "ui" or "common (based on file location: api/ = api, ui/ = ui, core/ or other = common)"
        }
    },
    "NOTE_BASE_CLASSES": "CRITICAL: You MUST extract ALL classes you find in the code. If you see 'class APIConfiguration:', it MUST be in base_classes. If you see 'class RestRequest:', it MUST be in base_classes. If you see 'class BaseActions:', it MUST be in base_classes. Scan through ALL the code and list EVERY class definition you find. Example: If code contains 'class APIConfiguration:' and 'class RestRequest:', then base_classes must have both entries.",
    "utility_functions": {
        "function_name": {
            "file": "relative/path/to/file.py (relative to framework root)",
            "description": "Extract FULL docstring from function definition - what this function does",
            "import_path": "from {FRAMEWORK_ROOT}.module.submodule import function_name (MUST start with {FRAMEWORK_ROOT}.)",
            "signature": "def function_name(param1: str, param2: int) -> dict (include ALL parameters and return type)",
            "usage_pattern": "Example of how it's used in the actual framework code (look at import statements and usage)"
        }
    },
    "NOTE_UTILITIES": "CRITICAL: You MUST extract ALL functions from helper/utility files. If you see 'def build_url(' in the code, it MUST be in utility_functions. If you see 'def validate_params(' in the code, it MUST be in utility_functions. Scan through ALL helper files and list EVERY function definition you find. Example: If code contains 'def build_url(' and 'def validate_params(', then utility_functions must have both entries.",
    "patterns": {
        "test_setup": ["Pattern descriptions with examples"],
        "assertions": ["Assertion patterns with method signatures"],
        "request_patterns": ["How requests are constructed"],
        "response_handling": ["How responses are handled"],
        "status_checks": ["Status code validation patterns"],
        "content_checks": ["Content validation patterns"],
        "error_checks": ["Error handling patterns"]
    },
    "client_class": {
        "name": "RestRequest",
        "file": "api/requests/base_api.py (relative to framework root)",
        "description": "Extract from docstring",
        "import_path": "from {FRAMEWORK_ROOT}.api.requests.base_api import RestRequest (MUST start with {FRAMEWORK_ROOT}.)",
        "key_methods": [
            {"name": "requests_get", "signature": "@staticmethod def requests_get(config: APIConfiguration) -> APIResponse", "description": "Http Get request and returns APIResponse object"},
            {"name": "requests_post", "signature": "@staticmethod def requests_post(config: APIConfiguration, data=None, json_data=None, files=None) -> APIResponse", "description": "Http Post request and returns APIResponse object"},
            {"name": "request_put", "signature": "@staticmethod def request_put(config: APIConfiguration, data=None, json_data=None, *files) -> APIResponse", "description": "Http Put request and returns APIResponse object"},
            {"name": "request_delete", "signature": "@staticmethod def request_delete(config: APIConfiguration, data=None) -> APIResponse", "description": "Http Delete request and returns APIResponse object"}
        ],
        "component_type": "api (based on file location in api/ directory)"
    },
    "response_class": {
        "name": "APIResponse",
        "file": "api/response/response_validator.py (relative to framework root)",
        "description": "Extract from docstring",
        "import_path": "from {FRAMEWORK_ROOT}.api.response.response_validator import APIResponse (MUST start with {FRAMEWORK_ROOT}.)",
        "key_methods": [
            {"name": "status_code", "signature": "@property def status_code(self) -> int", "description": "Returns HTTP status code"},
            {"name": "json_response", "signature": "@property def json_response(self) -> dict", "description": "Returns JSON response as dictionary"},
            {"name": "text", "signature": "@property def text(self) -> str", "description": "Returns response text"},
            {"name": "response", "signature": "@property def response(self) -> requests.Response", "description": "Returns raw response object"}
        ],
        "component_type": "api (based on file location in api/ directory)"
    },
    "assertion_utils": {
        "name": "RestResponse",
        "file": "api/response/response_validator.py (relative to framework root)",
        "description": "Extract from class docstring - validation utility class description",
        "import_path": "from {FRAMEWORK_ROOT}.api.response.response_validator import RestResponse (MUST start with {FRAMEWORK_ROOT}.)",
        "signature": "class RestResponse with static methods like validate_status_code, validate_protocol_version",
        "key_methods": [
            {"name": "validate_status_code", "signature": "@staticmethod def validate_status_code(response, expected_status_code)", "description": "Validates HTTP status code"},
            {"name": "validate_protocol_version", "signature": "@staticmethod def validate_protocol_version(response, expected_version)", "description": "Validates HTTP protocol version"}
        ],
        "usage_pattern": "RestResponse.validate_status_code(response, 200)",
        "component_type": "api (based on file location in api/ directory)"
    },
    "NOTE_ASSERTIONS": "CRITICAL: You MUST identify assertion/validation utilities. If you see a class like 'class RestResponse:' with methods like 'validate_status_code' or 'validate_protocol_version', this IS an assertion utility and MUST be in assertion_utils. If you see 'def assert_response(' or 'def validate_response(', these are assertion utilities. Example: If code contains 'class RestResponse:' with '@staticmethod def validate_status_code(response, expected_status_code):', then assertion_utils must identify RestResponse with its validation methods.",
    "test_organization": {
        "markers": ["@pytest.mark.api", "@pytest.mark.smoke"],
        "grouping": "Tests organized by endpoint or feature",
        "method_signatures": ["def test_name(self):", "def test_name_with_params(self, fixture):"],
        "data_setup": ["Patterns for test data preparation"]
    },
    "conventions": {
        "naming": "CamelCase for classes, snake_case for methods",
        "organization": "Tests in directories by type",
        "structure": "Modular folder structure",
        "documentation": "Docstrings in classes and methods",
        "error_handling": "Error handling patterns",
        "validation": "Validation approach patterns"
    },
    "validation_patterns": {
        "status_checks": ["Check status code equals expected", "Verify status code in range"],
        "content_checks": ["Verify response contains key", "Validate JSON structure"],
        "error_checks": ["Check error message format", "Validate error response structure"],
        "custom_checks": ["Custom validation patterns found"]
    }
}"""
        
        # Replace placeholder in JSON template
        json_template = json_template.replace("{FRAMEWORK_ROOT}", framework_root_name)
        
        # Continue with rest of prompt
        prompt_end = f"""

CRITICAL REQUIREMENTS - MUST FOLLOW (READ CAREFULLY):

1. **BASE CLASSES EXTRACTION (MANDATORY)**:
   - Scan ALL Python files in the framework code
   - For EVERY class definition found (class ClassName:), extract it as a base class
   - Look for classes like: APIConfiguration, RestRequest, RestResponse, APIResponse, BaseActions, BaseVerifications, BasePage, BaseLocator, BaseWait, LoggerFactory, PropFileReader, Browser, etc.
   - DO NOT skip any classes - if you see "class Something" in the code, it MUST be in base_classes
   - Extract the class docstring (triple-quoted string right after class definition)
   - Extract ALL methods from each class with their FULL signatures (including decorators, parameters with types, return types)
   - Determine component_type based on FILE LOCATION:
     * "api" if file is in {framework_root_name}/api/ or any subdirectory
     * "ui" if file is in {framework_root_name}/ui/ or any subdirectory  
     * "common" if file is in {framework_root_name}/core/ or any other location
   - Use the "# Import Path:" comment in each file to get the correct import path
   - Import path MUST start with '{framework_root_name}.'

2. **UTILITY FUNCTIONS EXTRACTION (MANDATORY)**:
   - Scan ALL Python files for function definitions (def function_name:)
   - Look for functions in helper/utility files, especially in "helpers", "utils", "common" directories
   - Extract ALL functions like: build_url, check_json_response, validate_params, rest_response_handle, convert_to_json, files_to_upload, handle_http_error, etc.
   - DO NOT skip any utility functions - if you see "def helper_function" in helper/utils files, it MUST be in utility_functions
   - Extract function docstring (triple-quoted string)
   - Extract FULL function signature with ALL parameters (including types) and return type
   - Use the "# Import Path:" comment in each file or construct from file location
   - Import path MUST start with '{framework_root_name}.'
   - Look at actual import statements in the code to see how these functions are imported

3. **ASSERTION UTILITIES EXTRACTION (MANDATORY)**:
   - Look for classes with validation methods (RestResponse, APIResponse, etc.)
   - Look for standalone assertion functions (assert_response, validate_response, etc.)
   - If you find a class like RestResponse with methods like validate_status_code, validate_protocol_version, validate_reason_phrase, etc. - this IS an assertion utility
   - Extract the class/function docstring
   - Extract ALL validation methods with their FULL signatures (including @staticmethod, @classmethod decorators)
   - Extract usage patterns from test files or actual code usage
   - Use CORRECT import path - check "# Import Path:" comment or construct from file location
   - Import path MUST start with '{framework_root_name}.'

4. **IMPORT PATH CONSTRUCTION (CRITICAL)**:
   - ALWAYS check the "# Import Path:" comment at the top of each file - it shows the correct import path
   - If not available, construct from file location: {framework_root_name}.module.submodule
   - Example: File at {framework_root_name}/api/helpers/helper_api.py → import_path: "from {framework_root_name}.api.helpers.helper_api import function_name"
   - Look at existing import statements in the code files to understand the import pattern
   - ALL import paths MUST start with '{framework_root_name}.' - never use relative imports or just module names

5. **COMPONENT TYPE CATEGORIZATION (CRITICAL)**:
   - Use FILE LOCATION, not class names, to determine component_type
   - Check the "# File:" comment at the top of each file to see the location
   - Files in api/ directory → "api"
   - Files in ui/ directory → "ui"
   - Files in core/ directory → "common"
   - Any other location → "common"
   - DO NOT guess based on class names like "API" or "UI" in the name

6. Extract ALL descriptions from docstrings (triple-quoted strings) - Use class-level and function-level docstrings, not comments.
7. Extract method signatures with FULL type hints - Include all parameters with types and return types. This is CRITICAL for code generation.
   - Example GOOD: "@staticmethod def requests_get(config: APIConfiguration) -> APIResponse"
   - Example GOOD: "@staticmethod def validate_status_code(response: requests.Response, expected_status_code: int) -> bool"
   - Example GOOD: "@property def status_code(self) -> int" - For properties, include property name and return type
   - Example BAD: "def requests_get(config)" - Missing types and return type
   - Example BAD: "def validate_status_code(response, expected)" - Missing types
   - Example BAD: "property" - Missing property name and type
   - For each method, extract:
     * Decorators (@staticmethod, @classmethod, @property)
     * All parameters with type hints (param: type)
     * Default values (param: type = default)
     * Return type (-> ReturnType) - ALWAYS include return type
   - For properties, extract as: "@property def property_name(self) -> return_type"
   - DO NOT just write "property" - extract the actual property name and return type
   - If type hints are missing in code, infer from docstring, usage, or method body
   - This information is ESSENTIAL - without it, generated test code will have errors
8. Extract ALL properties from classes - CRITICAL for response classes:
   - For APIResponse class, extract ALL properties like:
     * "@property def status_code(self) -> int" - Returns HTTP status code
     * "@property def json_response(self) -> dict" - Returns JSON response as dict
     * "@property def text(self) -> str" - Returns response text
     * "@property def response(self) -> requests.Response" - Returns raw response object
   - For any class with @property decorators, extract the property name and return type
   - Properties are accessed as: response.status_code, response.json_response
   - DO NOT just write "property" - extract the actual property name and return type
   - This is CRITICAL for test script generation - test code needs to know how to access response data
9. Extract COMPLETE configuration class details:
   - For APIConfiguration or similar config classes, extract ALL methods:
     * "def __init__(self) -> None" - Initialize configuration
     * "def addHeader(self, key: str, value: str) -> None" - Add header
     * "def addAccept(self, value: str) -> None" - Add Accept header
     * "def addContentType(self, value: str) -> None" - Add Content-Type header
     * "def addBasicAuth(self, username: str, password: str) -> None" - Add authentication
   - Extract ALL attributes/properties that can be set:
     * "base_url: str" - Base URL for API calls
     * "end_point: str" - API endpoint path
     * "headers: dict" - HTTP headers
     * "params: dict" - Query parameters
   - Show how to set these attributes: "config.base_url = 'https://api.example.com'"
   - Include complete setup example in usage_pattern
10. Provide COMPLETE usage examples from the actual code - Show end-to-end usage:
   - Configuration setup example:
     ```python
     config = APIConfiguration()
     config.base_url = "https://api.example.com"
     config.end_point = "/api/v1/users"
     config.addHeader("Authorization", "Bearer token")
     ```
   - Request example:
     ```python
     response = RestRequest.requests_get(config)
     ```
   - Response access example:
     ```python
     status = response.status_code
     json_data = response.json_response
     text = response.text
     ```
   - Validation example:
     ```python
     RestResponse.validate_status_code(response.response, 200)
     assert response.json_response["key"] == "value"
     ```
   - Look for actual test files or example code in the framework
   - Extract these patterns and include in usage_pattern field
   - These patterns will be used to generate correct test code
11. Be thorough and detailed - This will be used to generate test scripts, so completeness is critical.
   - Missing method signatures with return types = cannot generate proper code
   - Missing property names and types = cannot access response data correctly
   - Missing import paths = generated code will have import errors
   - Missing component types = cannot categorize components correctly
   - Missing usage examples = generated code may not follow framework patterns
12. Identify ALL relevant components regardless of type - The framework may support both API and UI testing.
13. EXPLICITLY CHECK FOR CORE AND UI COMPONENTS:
    - Look for core/ directory: Extract LoggerFactory, PropFileReader, ConfigReader, BaseActions, BaseVerifications, and any other common utilities
    - Look for ui/ directory: Extract BasePage, BaseLocator, Browser, WebDriver, PageObject, and any UI-specific utilities
    - If directories exist but are empty, note that in your analysis
    - If you only find API components, explicitly state: "Only API components found. No UI or core components detected."
14. **MODULE ORGANIZATION (CRITICAL FOR TEST GENERATION)**:
    - When extracting components, mentally organize them by module (api/, ui/, core/)
    - This organization will be used by test script generator to select appropriate components
    - For API tests → generator needs: api/ components (RestRequest, APIResponse, RestResponse)
    - For UI tests → generator needs: ui/ components (BasePage, Browser, BaseActions)
    - For all tests → generator needs: core/ components (LoggerFactory, PropFileReader)
    - Ensure component_type is correctly set so components can be filtered by module

EXTRACTION CHECKLIST - Before returning JSON, verify (MANDATORY - Check each item):
- [ ] STEP 1: Did I check the "# DETECTED DIRECTORIES" line in the framework structure information?
- [ ] STEP 2: Did I extract components from EVERY directory listed in DETECTED DIRECTORIES?
  - If "api" was listed → Do I have components with component_type: "api"?
  - If "ui" was listed → Do I have components with component_type: "ui"?
  - If "core" was listed → Do I have components with component_type: "common"?
- [ ] Have I scanned ALL directories (api/, ui/, core/, and any others) in the framework?
- [ ] Have I extracted ALL classes found in the code? (Check: Scan the code - if you see "class Something:", did I add it to base_classes?)
- [ ] Did I check for classes in core/ directory? (Look for: LoggerFactory, PropFileReader, ConfigReader, BaseActions, etc.)
- [ ] Did I check for classes in ui/ directory? (Look for: BasePage, BaseLocator, Browser, WebDriver, etc.)
- [ ] Have I extracted ALL utility functions from helper/utils/common/core files? (Check: Scan ALL helper files in ALL directories - if you see "def helper_function(", did I add it to utility_functions?)
- [ ] Did I check for utility functions in core/ directory? (Look for: read_config, get_logger, file_operations, etc.)
- [ ] Did I check for utility functions in ui/ directory? (Look for: wait_for_element, click_element, etc.)
- [ ] Have I identified assertion utilities? (Check: Did I find RestResponse class with validate methods? Did I add it to assertion_utils?)
- [ ] Did I check for UI assertion utilities? (Look for: assert_element, verify_element, etc.)
- [ ] Did I analyze EVERY Python file in the framework? (Check: Count files in code - did I process all of them?)
- [ ] Did I extract ALL methods from each class? (Check: For each class, did I list ALL methods including __init__, private methods, static methods?)
- [ ] Did I extract method signatures with ALL parameters? (Check: If method has 5 parameters, did I include all 5 with types?)
- [ ] Did I check for configuration classes? (Look for: APIConfiguration, Config, Settings, etc.)
- [ ] Did I check for exception classes? (Look for: Custom exceptions in exceptions/ directories)
- [ ] Do all components have import_path? (Check: Can someone import and use this component?)
- [ ] Do ALL import paths start with '{framework_root_name}.'? (Check: Are they in format "from {framework_root_name}.module import ClassName"?)
- [ ] Did I use the "# Import Path:" comments from files to get correct import paths?
- [ ] Did I determine component_type based on FILE LOCATION (api/, ui/, core/) not class names?
- [ ] Do all components have descriptions? (Check: Did I extract docstrings from triple-quoted strings?)
- [ ] Did I extract ALL methods from classes with FULL signatures (including decorators, parameter types, return types)?
- [ ] Did I extract ALL properties with property names and return types? (Check: For APIResponse, did I extract status_code, json_response, text, response properties with their types?)
- [ ] Did I extract complete configuration class details? (Check: For APIConfiguration, did I extract all methods like addHeader, addAccept, and all attributes like base_url, end_point?)
- [ ] Did I include complete usage examples? (Check: Do I have examples showing config setup → request → response access → validation?)
- [ ] Have I explicitly noted if any directory (api/, ui/, core/) exists but contains no components?
- [ ] FINAL CHECK: Does my JSON response include components from ALL directories that were listed in DETECTED DIRECTORIES?
- [ ] MODULE VERIFICATION: Did I extract from ALL modules that exist?
  - If api/ exists → I have at least 3-5 API components
  - If ui/ exists → I have at least 3-5 UI components  
  - If core/ exists → I have at least 2-3 core components
- [ ] COMPLETENESS CHECK: Can someone generate a working test script using my analysis?
  - Do I have client class with methods? (For API tests)
  - Do I have response class? (For API tests)
  - Do I have assertion utilities? (For both API and UI tests)
  - Do I have configuration classes? (For setup)
  - Do I have complete method signatures? (For code generation)
- [ ] QUALITY CHECK: Is my analysis detailed enough?
  - Every class has description from docstring
  - Every method has full signature with types
  - Every component has correct import path
  - Every component has correct component_type

MODULE-SPECIFIC EXTRACTION REQUIREMENTS:

API MODULE (framework/api/):
- MUST extract: APIConfiguration, RestRequest, APIResponse, RestResponse
- MUST extract: All helper functions (build_url, rest_response_handle, validate_params, etc.)
- MUST extract: All exception classes (ParamsMissing, InvalidURLException, etc.)
- MUST extract: All response parsers (JSONValidator, XMLValidator, CSVValidator)
- component_type: "api" for ALL components in api/ directory

UI MODULE (framework/ui/):
- MUST extract: BasePage, BaseActions, BaseVerifications, BaseLocator, BaseWait
- MUST extract: Browser, WebDriver classes
- MUST extract: All UI helper functions (get_locator_by, etc.)
- MUST extract: All UI exception classes (BrowserException, ElementNotFound, etc.)
- component_type: "ui" for ALL components in ui/ directory

CORE MODULE (framework/core/):
- MUST extract: LoggerFactory, PropFileReader
- MUST extract: All decorators (retry_on_exception, handle_on_exceptions, etc.)
- MUST extract: All common utilities (file operations, data validation, etc.)
- MUST extract: All constants classes (ConfConst, LogConst, etc.)
- component_type: "common" for ALL components in core/ directory

CONCRETE EXAMPLE OF WHAT TO EXTRACT (FROM ALL DIRECTORIES):
If the framework code contains files in api/, ui/, AND core/ directories, you MUST extract from ALL:

```python
# ========== API DIRECTORY EXAMPLES ==========
# File: api/requests/base_api.py
# Import Path: {framework_root_name}.api.requests.base_api

class APIConfiguration:
    \"\"\"Building API configuration object\"\"\"
    def __init__(self): ...
    
class RestRequest:
    \"\"\"A wrapper around Requests\"\"\"
    def request(self, method, url, ...): ...

# File: api/helpers/helper_api.py  
# Import Path: {framework_root_name}.api.helpers.helper_api

def build_url(config): ...
    \"\"\"Build URL from APIConfiguration object\"\"\"
    
def rest_response_handle(response): ...
    \"\"\"Handle HTTP response\"\"\"

# File: api/response/response_validator.py
# Import Path: {framework_root_name}.api.response.response_validator

class RestResponse:
    \"\"\"REST Response Validator\"\"\"
    @staticmethod
    def validate_status_code(response, expected): ...

# ========== UI DIRECTORY EXAMPLES ==========
# File: ui/base/base_page.py
# Import Path: {framework_root_name}.ui.base.base_page

class BasePage:
    \"\"\"Base page object class\"\"\"
    def __init__(self, driver): ...
    def click_element(self, locator): ...

# File: ui/utils/browser.py
# Import Path: {framework_root_name}.ui.utils.browser

class Browser:
    \"\"\"Browser wrapper class\"\"\"
    def open(self, url): ...

# ========== CORE DIRECTORY EXAMPLES ==========
# File: core/utils/logger.py
# Import Path: {framework_root_name}.core.utils.logger

class LoggerFactory:
    \"\"\"Logger factory class\"\"\"
    @staticmethod
    def get_logger(name): ...

# File: core/common/config_reader.py
# Import Path: {framework_root_name}.core.common.config_reader

class PropFileReader:
    \"\"\"Property file reader\"\"\"
    def read_config(self, file_path): ...
```

Then your JSON MUST include components from ALL directories:

- base_classes: {{
    # API components (from api/ directory)
    "APIConfiguration": {{
        "file": "api/requests/base_api.py",
        "import_path": "from {framework_root_name}.api.requests.base_api import APIConfiguration",
        "component_type": "api"
    }},
    "RestRequest": {{
        "file": "api/requests/base_api.py", 
        "import_path": "from {framework_root_name}.api.requests.base_api import RestRequest",
        "component_type": "api"
    }},
    "RestResponse": {{
        "file": "api/response/response_validator.py",
        "import_path": "from {framework_root_name}.api.response.response_validator import RestResponse",
        "component_type": "api"
    }},
    # UI components (from ui/ directory) - MUST include if ui/ exists!
    "BasePage": {{
        "file": "ui/base/base_page.py",
        "import_path": "from {framework_root_name}.ui.base.base_page import BasePage",
        "component_type": "ui"
    }},
    "Browser": {{
        "file": "ui/utils/browser.py",
        "import_path": "from {framework_root_name}.ui.utils.browser import Browser",
        "component_type": "ui"
    }},
    # Core/Common components (from core/ directory) - MUST include if core/ exists!
    "LoggerFactory": {{
        "file": "core/utils/logger.py",
        "import_path": "from {framework_root_name}.core.utils.logger import LoggerFactory",
        "component_type": "common"
    }},
    "PropFileReader": {{
        "file": "core/common/config_reader.py",
        "import_path": "from {framework_root_name}.core.common.config_reader import PropFileReader",
        "component_type": "common"
    }}
  }}
- utility_functions: {{
    # API utilities
    "build_url": {{
        "file": "api/helpers/helper_api.py",
        "import_path": "from {framework_root_name}.api.helpers.helper_api import build_url"
    }},
    "rest_response_handle": {{
        "file": "api/helpers/helper_api.py",
        "import_path": "from {framework_root_name}.api.helpers.helper_api import rest_response_handle"
    }},
    # UI utilities - MUST include if ui/ exists!
    "click_element": {{
        "file": "ui/base/base_page.py",
        "import_path": "from {framework_root_name}.ui.base.base_page import click_element"
    }},
    # Core utilities - MUST include if core/ exists!
    "get_logger": {{
        "file": "core/utils/logger.py",
        "import_path": "from {framework_root_name}.core.utils.logger import get_logger"
    }}
  }}
- assertion_utils: {{
    "name": "RestResponse",
    "file": "api/response/response_validator.py",
    "import_path": "from {framework_root_name}.api.response.response_validator import RestResponse",
    "key_methods": [{{"name": "validate_status_code", ...}}],
    "component_type": "api"
  }}

REMEMBER: 
- The goal is to extract COMPLETE framework information. Missing base classes, utilities, or assertion methods will result in poor test script generation.
- If you see a class or function in the code, it MUST appear in the JSON response.
- DO NOT return empty base_classes or utility_functions if you see classes/functions in the code.
- ALL import paths MUST start with '{framework_root_name}.' - check the "# Import Path:" comments in files.
- Use FILE LOCATION to determine component_type, not class names.
- SCAN ALL DIRECTORIES: You MUST check api/, ui/, core/, and any other directories. Do not assume a framework only has API components.
- If you find components in core/ directory, they are "common" type. If you find components in ui/ directory, they are "ui" type.
- Be thorough: Extract ALL classes, ALL functions, ALL methods with FULL signatures. This information is critical for generating accurate test scripts.
- Include detailed method signatures with parameter types and return types - this is essential for code generation."""

        return prompt_start + json_template + prompt_end
