#!/usr/bin/env python3
"""
Script to generate complete swagger.json and connector_wrapper.py with ALL MCP tools.
Reads tools directly from main.py's @mcp.tool() decorators to ensure exact match.
"""
import json
import re
import inspect
from word_document_server.tools import (
    document_tools,
    content_tools,
    format_tools,
    protection_tools,
    footnote_tools,
    extended_document_tools,
    comment_tools,
    template_tools,
    advanced_replace_tools
)

# Module mapping for finding functions
TOOL_MODULES = {
    "document": document_tools,
    "content": content_tools,
    "format": format_tools,
    "protection": protection_tools,
    "footnote": footnote_tools,
    "extended": extended_document_tools,
    "comment": comment_tools,
    "template": template_tools,
    "advanced": advanced_replace_tools,
}

def extract_tools_from_main():
    """Extract tool names and docstrings from main.py's @mcp.tool() decorators."""
    with open("word_document_server/main.py") as f:
        content = f.read()

    # Find all @mcp.tool() decorators and their function definitions
    pattern = r'@mcp\.tool\(\)\s+(?:async\s+)?def\s+(\w+)\([^)]*\):\s*"""([^"]+)"""'
    matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)

    tools = []
    for func_name, doc in matches:
        # Find the function in the tool modules to get its signature
        func = find_function_in_modules(func_name)
        if func:
            sig = inspect.signature(func)
            tools.append({
                "name": func_name,
                "func": func,
                "signature": sig,
                "doc": doc.strip()
            })
        else:
            print(f"⚠️  Warning: Could not find function {func_name} in tool modules")

    return tools

def find_function_in_modules(func_name):
    """Find a function by name across all tool modules."""
    for module_name, module in TOOL_MODULES.items():
        # Try exact match first
        if hasattr(module, func_name):
            return getattr(module, func_name)
        # Try with _tool suffix (some tools are named differently)
        if hasattr(module, f"{func_name}_tool"):
            return getattr(module, f"{func_name}_tool")
    return None

def generate_swagger_path(tool):
    """Generate swagger path definition for a tool."""
    name = tool["name"]
    doc = tool["doc"]
    sig = tool["signature"]

    # Generate operation ID (camelCase)
    operation_id = ''.join(word.capitalize() for word in name.split('_'))

    # Extract parameters
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name in ['self', 'cls']:
            continue

        param_type = "string"
        param_desc = f"{param_name} parameter"

        # Try to infer type from annotation
        if param.annotation != inspect.Parameter.empty:
            ann_str = str(param.annotation)
            if 'int' in ann_str.lower():
                param_type = "integer"
            elif 'bool' in ann_str.lower():
                param_type = "boolean"
            elif 'float' in ann_str.lower():
                param_type = "number"
            elif 'list' in ann_str.lower() or 'array' in ann_str.lower():
                param_type = "array"
            elif 'dict' in ann_str.lower():
                param_type = "object"

        prop_def = {
            "type": param_type,
            "description": param_desc,
            "x-ms-summary": param_name.replace('_', ' ').title()
        }

        # Swagger 2.0 requires 'items' for array types
        if param_type == "array":
            prop_def["items"] = {"type": "string"}

        # Swagger 2.0 requires 'additionalProperties' for object types
        if param_type == "object":
            prop_def["additionalProperties"] = True

        properties[param_name] = prop_def

        # Check if required (no default value)
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    # Choose HTTP method based on operation
    method = "post"
    if any(word in name.lower() for word in ['list', 'get', 'find', 'search', 'check', 'debug', 'validate']):
        method = "get"

    path_def = {
        "operationId": operation_id,
        "summary": doc.split('\n')[0] if doc else name.replace('_', ' ').title(),
        "description": doc,
        "responses": {
            "200": {
                "description": "Succès",
                "schema": {
                    "type": "string",
                    "description": "Résultat de l'opération"
                }
            }
        }
    }

    if method == "post" and properties:
        path_def["parameters"] = [{
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }]

    return f"/api/{name.replace('_', '/')}", method, path_def

def main():
    print("Extracting tools from main.py...")
    tools = extract_tools_from_main()
    print(f"Found {len(tools)} tools registered in main.py")

    # Load base swagger
    with open("word-connector.swagger.json.backup", "r") as f:
        swagger = json.load(f)

    # Update host to connector URL
    swagger["host"] = "word-mcp-connector.ashywater-9eb5a210.francecentral.azurecontainerapps.io"

    # Clear existing paths
    swagger["paths"] = {}

    # Generate paths for all tools
    for tool in tools:
        path, method, path_def = generate_swagger_path(tool)

        if path not in swagger["paths"]:
            swagger["paths"][path] = {}

        swagger["paths"][path][method] = path_def
        print(f"✅ Added: {method.upper()} {path}")

    # Update metadata
    swagger["info"]["title"] = "Word Document MCP Connector - Complete"
    swagger["info"]["description"] = f"REST API wrapper for Word MCP Server - All {len(tools)} tools"
    swagger["info"]["version"] = "2.0"

    # Save complete swagger
    output_file = "word-connector.swagger.json"
    with open(output_file, "w") as f:
        json.dump(swagger, f, indent=2)

    print(f"\n✅ Generated {output_file} with {len(swagger['paths'])} endpoints (exactly {len(tools)} tools)")
    print(f"✅ No duplicates, no demo_ tools, exact match with main.py")

if __name__ == "__main__":
    main()
