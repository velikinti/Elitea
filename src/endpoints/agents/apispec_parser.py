import re
import json
import yaml
import requests
 
class APISpecParser:

    def parse(self, input_type, content):
        if input_type == "curl":
            return self._parse_curl(content)
        elif input_type == "swagger":
            return self._parse_swagger(content)
        else:
            raise ValueError("Unsupported input type")
 
    def _parse_curl(self, curl_command):
        # Basic curl parser (expand as needed)
        method = "GET"
        url = ""
        headers = {}
        body = None
 
        # Extract method
        method_match = re.search(r"-X\s+(\w+)", curl_command)
        if method_match:
            method = method_match.group(1)
 
        # Extract URL
        url_match = re.search(r"(https?://[^\s]+)", curl_command)
        if url_match:
            url = url_match.group(1)
 
        # Extract headers
        header_matches = re.findall(r"-H\s+\"([^\"]+)\"", curl_command)
        for header in header_matches:
            key, value = header.split(":", 1)
            headers[key.strip()] = value.strip()
 
        # Extract body
        data_match = re.search(r"-d\s+'([^']+)'", curl_command)
        if data_match:
            try:
                body = json.loads(data_match.group(1))
            except Exception:
                body = data_match.group(1)
 
        # Build API spec structure
        api_spec = {
            "method": method,
            "url": url,
            "headers": headers,
            "body": body,
            "query_params": {}
        }
        return api_spec
    
    def _parse_swagger(self, content):
        # Track original URL for relative server URLs in OpenAPI 3.x
        original_url = None
        
        # If content is a URI, fetch it
        if isinstance(content, str) and content.strip().startswith(("http://", "https://")):
            original_url = content.strip()
            response = requests.get(original_url)
            response.raise_for_status()
            try:
                swagger_spec = response.json()
            except Exception:
                # Try YAML if JSON fails
                swagger_spec = yaml.safe_load(response.text)
        else:
            # Try JSON first
            try:
                swagger_spec = json.loads(content)
            except Exception:
                # Try YAML if JSON fails
                swagger_spec = yaml.safe_load(content)

        # Detect spec version (backwards compatible)
        is_openapi3 = "openapi" in swagger_spec and swagger_spec.get("openapi", "").startswith("3.")
        is_swagger2 = "swagger" in swagger_spec

        # Transform swagger spec to list of API specs
        api_specs = []
        base_url = ""
        
        # Construct base URL based on version (backwards compatible)
        if is_openapi3:
            # OpenAPI 3.x uses "servers" array
            servers = swagger_spec.get("servers", [])
            if servers:
                # Use first server URL
                server_url = servers[0].get("url", "") if isinstance(servers[0], dict) else servers[0]
                
                # Handle relative URLs
                if server_url.startswith("http://") or server_url.startswith("https://"):
                    base_url = server_url.rstrip("/")
                elif server_url.startswith("/") and original_url:
                    # Relative URL - construct from original URL
                    from urllib.parse import urlparse
                    parsed = urlparse(original_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}{server_url}".rstrip("/")
                else:
                    base_url = server_url.rstrip("/")
            else:
                # Fallback: try to extract from original URL
                if original_url:
                    from urllib.parse import urlparse
                    parsed = urlparse(original_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rsplit('/', 1)[0]}".rstrip("/")
                else:
                    base_url = ""
        elif is_swagger2:
            # Swagger 2.0 uses "schemes", "host", and "basePath" (original logic)
            if "schemes" in swagger_spec and "host" in swagger_spec:
                scheme = swagger_spec["schemes"][0]
                host = swagger_spec["host"]
                base_path = swagger_spec.get("basePath", "")
                base_url = f"{scheme}://{host}{base_path}"
        
        # Process each path and method
        paths = swagger_spec.get("paths", {})
        for path, path_spec in paths.items():
            for method, operation in path_spec.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue
                
                # Build full URL
                if base_url:
                    full_url = f"{base_url}{path}"
                else:
                    full_url = path
                
                # Initialize request spec
                api_spec = {
                    "method": method.upper(),
                    "url": full_url,
                    "headers": {},
                    "body": None,
                    "query_params": {}
                }
                
                if is_openapi3:
                    # OpenAPI 3.x: Handle requestBody and parameters separately
                    # Process requestBody
                    request_body = operation.get("requestBody", {})
                    if request_body:
                        content = request_body.get("content", {})
                        # Try to get application/json schema
                        json_content = content.get("application/json", {})
                        if json_content:
                            schema = json_content.get("schema", {})
                            if "$ref" in schema:
                                schema = self._resolve_ref_openapi3(swagger_spec, schema["$ref"])
                            api_spec["body"] = self._generate_example_from_schema(schema)
                    
                    # Process parameters (query, header, path)
                    for param in operation.get("parameters", []):
                        param_in = param.get("in")
                        
                        if param_in == "header":
                            api_spec["headers"][param["name"]] = self._get_example_value_openapi3(param)
                        
                        elif param_in == "query":
                            api_spec["query_params"][param["name"]] = self._get_example_value_openapi3(param)
                        
                        # path parameters are in URL, skip
                
                else:
                    # Swagger 2.0: Handle parameters (original logic)
                    for param in operation.get("parameters", []):
                        param_in = param.get("in")
                        
                        if param_in == "header":
                            api_spec["headers"][param["name"]] = self._get_example_value(param)
                        
                        elif param_in == "body":
                            schema = param.get("schema", {})
                            if "$ref" in schema:
                                ref_path = schema["$ref"].split("/")[1:]  # Skip initial '#'
                                schema = self._resolve_ref(swagger_spec, ref_path)
                            api_spec["body"] = self._generate_example_from_schema(schema)
                        
                        elif param_in == "query":
                            api_spec["query_params"][param["name"]] = self._get_example_value(param)
                        
                        elif param_in == "formData":
                            if api_spec["body"] is None:
                                api_spec["body"] = {}
                            api_spec["body"][param["name"]] = self._get_example_value(param)
                
                api_specs.append(api_spec)
        
        return api_specs
    
    def _get_example_value(self, param):
        """Get an example value for a parameter based on its type."""
        if "example" in param:
            return param["example"]
        
        param_type = param.get("type", "string")
        if param_type == "string":
            return "example_value"
        elif param_type == "integer":
            return 1
        elif param_type == "number":
            return 1.0
        elif param_type == "boolean":
            return True
        elif param_type == "array":
            items = param.get("items", {})
            return [self._get_example_value({"type": items.get("type", "string")})]
        return None
    
    def _resolve_ref(self, swagger_spec, ref_path):
        """Resolve a JSON reference in Swagger 2.0 spec."""
        current = swagger_spec
        for path_part in ref_path:
            current = current.get(path_part, {})
        return current
    
    def _resolve_ref_openapi3(self, swagger_spec, ref_string):
        """Resolve a JSON reference in OpenAPI 3.x spec."""
        # OpenAPI 3.x refs are like "#/components/schemas/Pet"
        if not ref_string.startswith("#/"):
            return {}
        
        ref_path = ref_string[2:].split("/")  # Remove "#/" and split
        current = swagger_spec
        for path_part in ref_path:
            current = current.get(path_part, {})
        return current
    
    def _get_example_value_openapi3(self, param):
        """Get an example value for OpenAPI 3.x parameter."""
        if "example" in param:
            return param["example"]
        
        schema = param.get("schema", {})
        if "$ref" in schema:
            # This would need the full spec to resolve, but for now use default
            return "example_value"
        
        param_type = schema.get("type", "string")
        if param_type == "string":
            return "example_value"
        elif param_type == "integer":
            return 1
        elif param_type == "number":
            return 1.0
        elif param_type == "boolean":
            return True
        elif param_type == "array":
            items = schema.get("items", {})
            return [self._get_example_value_openapi3({"schema": items})]
        return None
    
    def _generate_example_from_schema(self, schema):
        """Generate an example object from a JSON Schema."""
        if "example" in schema:
            return schema["example"]
            
        schema_type = schema.get("type", "object")
        
        if schema_type == "object":
            result = {}
            for prop_name, prop_schema in schema.get("properties", {}).items():
                result[prop_name] = self._generate_example_from_schema(prop_schema)
            return result
            
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            if isinstance(items_schema, dict):
                return [self._generate_example_from_schema(items_schema)]
            return []
            
        elif schema_type == "string":
            return "example_string"
        elif schema_type == "integer":
            return 1
        elif schema_type == "number":
            return 1.0
        elif schema_type == "boolean":
            return True
        
        return None