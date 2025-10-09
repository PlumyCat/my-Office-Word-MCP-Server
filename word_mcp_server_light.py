"""
Lightweight Word Document MCP Server for Copilot Studio.
MAXIMUM 40 tools to stay well under the 70 tool limit.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
print("Loading configuration from .env file...")
load_dotenv()
os.environ.setdefault('FASTMCP_LOG_LEVEL', 'INFO')

from fastmcp import FastMCP
from word_document_server.tools import (
    document_tools,
    content_tools,
    template_tools,
    demo_tools
)

def get_transport_config():
    """Get transport configuration from environment variables."""
    config = {
        'transport': 'stdio',
        'host': '0.0.0.0',
        'port': 8000,
        'path': '/mcp',
    }

    transport = os.getenv('MCP_TRANSPORT', 'stdio').lower()
    print(f"Transport: {transport}")

    valid_transports = ['stdio', 'streamable-http', 'http', 'sse']
    if transport not in valid_transports:
        print(f"Invalid transport '{transport}', falling back to stdio")
        transport = 'stdio'

    config['transport'] = transport

    if transport in ['streamable-http', 'http', 'sse']:
        config['host'] = os.getenv('MCP_HOST', '0.0.0.0')
        config['port'] = int(os.getenv('MCP_PORT', '8000'))
        if transport != 'sse':
            config['path'] = os.getenv('MCP_PATH', '/mcp')

    return config

# Initialize FastMCP server
mcp = FastMCP("Word Document Server - Light Edition")

def register_tools():
    """Register ONLY essential tools for Copilot Studio (max 40 tools)."""

    # ========== QUICK START TOOLS (NO PARAMETERS) - 6 tools ==========

    @mcp.tool()
    def hello_world():
        """Test MCP connection. No parameters needed."""
        return demo_tools.demo_hello_world()

    @mcp.tool()
    def list_all_templates():
        """List all templates. No parameters needed."""
        return demo_tools.demo_list_all_templates()

    @mcp.tool()
    def list_all_documents():
        """List all documents. No parameters needed."""
        return demo_tools.demo_list_all_documents()

    @mcp.tool()
    def get_storage_info():
        """Get storage info. No parameters needed."""
        return demo_tools.demo_get_storage_info()

    @mcp.tool()
    def create_test_document():
        """Create test document. No parameters needed."""
        return demo_tools.demo_create_test_document()

    @mcp.tool()
    def create_business_letter():
        """Create business letter from template. No parameters needed."""
        return demo_tools.demo_create_business_letter()

    # ========== ESSENTIAL DOCUMENT TOOLS - 11 tools ==========

    @mcp.tool()
    def create_document(filename: str):
        """Create new Word document. 1 parameter: filename."""
        return document_tools.create_document(filename, None, None)

    @mcp.tool()
    def create_document_with_title(filename: str, title: str):
        """Create Word document with title. 2 parameters: filename, title."""
        return document_tools.create_document(filename, title, None)

    @mcp.tool()
    def get_document_info(filename: str):
        """Get document information (size, dates, etc). 1 parameter: filename."""
        return document_tools.get_document_info(filename)

    @mcp.tool()
    def get_document_text(filename: str):
        """Extract all text from document. 1 parameter: filename."""
        return document_tools.get_document_text(filename)

    @mcp.tool()
    def list_available_documents():
        """List all documents in storage. No parameters."""
        return document_tools.list_available_documents(".")

    @mcp.tool()
    def copy_document(source_filename: str, destination_filename: str):
        """Copy document to new name. 2 parameters: source_filename, destination_filename."""
        return document_tools.copy_document(source_filename, destination_filename)

    @mcp.tool()
    def check_document_exists(filename: str):
        """Check if document exists in storage. 1 parameter: filename."""
        return document_tools.check_document_exists(filename)

    @mcp.tool()
    def download_document(filename: str):
        """Get download URL with SAS token for document. 1 parameter: filename."""
        return document_tools.download_document(filename)

    @mcp.tool()
    def debug_storage():
        """Show Azure Storage configuration and status. No parameters needed."""
        return document_tools.debug_storage()

    @mcp.tool()
    def cleanup_expired_documents():
        """Clean up expired documents (older than TTL). No parameters needed."""
        return document_tools.cleanup_expired_documents()

    @mcp.tool()
    def get_document_outline(filename: str):
        """Get document structure (headings, sections). 1 parameter: filename."""
        return document_tools.get_document_outline(filename)

    # ========== CONTENT TOOLS - 8 tools ==========

    @mcp.tool()
    def add_paragraph(filename: str, text: str):
        """Add paragraph to document. 2 parameters: filename, text."""
        return content_tools.add_paragraph(filename, text, None)

    @mcp.tool()
    def add_heading(filename: str, text: str):
        """Add heading level 1 to document. 2 parameters: filename, text."""
        return content_tools.add_heading(filename, text, 1)

    @mcp.tool()
    def add_heading_level_2(filename: str, text: str):
        """Add heading level 2 to document. 2 parameters: filename, text."""
        return content_tools.add_heading(filename, text, 2)

    @mcp.tool()
    def add_table(filename: str, rows: int, cols: int):
        """Add empty table to document. Parameters: filename, rows (number), cols (number)."""
        return content_tools.add_table(filename, rows, cols, None)

    @mcp.tool()
    def add_page_break(filename: str):
        """Add page break to document. 1 parameter: filename."""
        return content_tools.add_page_break(filename)

    @mcp.tool()
    def delete_paragraph(filename: str, paragraph_index: int):
        """Delete paragraph by index (0-based). Parameters: filename, paragraph_index (number)."""
        return content_tools.delete_paragraph(filename, paragraph_index)

    @mcp.tool()
    def search_and_replace(filename: str, find_text: str, replace_text: str):
        """Search and replace text in document. Parameters: filename, find_text, replace_text."""
        return content_tools.search_and_replace(filename, find_text, replace_text)

    @mcp.tool()
    def get_paragraph_text(filename: str, paragraph_index: int):
        """Get text from specific paragraph by index. Parameters: filename, paragraph_index (number)."""
        from word_document_server.tools import extended_document_tools
        return extended_document_tools.get_paragraph_text_from_document(filename, paragraph_index)

    @mcp.tool()
    def find_text_in_document(filename: str, text_to_find: str):
        """Find text in document (case sensitive). 2 parameters: filename, text_to_find."""
        from word_document_server.tools import extended_document_tools
        return extended_document_tools.find_text_in_document(filename, text_to_find, True)

    # ========== TEMPLATE TOOLS - 5 tools ==========

    @mcp.tool()
    def list_document_templates():
        """List all templates in storage. No parameters."""
        return template_tools.list_document_templates(None)

    @mcp.tool()
    def get_template_info(template_name: str):
        """Get template details from general category. 1 parameter: template_name."""
        return template_tools.get_template_info(template_name, "general")

    @mcp.tool()
    def create_document_from_template(template_name: str, new_document_name: str):
        """Create document from template in general category. 2 parameters: template_name, new_document_name."""
        return template_tools.create_document_from_template(
            template_name, new_document_name, "general", None
        )

    @mcp.tool()
    def add_document_template(source_document: str, template_name: str):
        """Save document as template in general category. 2 parameters: source_document, template_name."""
        return template_tools.add_document_template(
            source_document, template_name, "general", "", "Copilot Studio"
        )

    @mcp.tool()
    def delete_document_template(template_name: str):
        """Delete template from general category. 1 parameter: template_name."""
        return template_tools.delete_document_template(template_name, "general")

    # Total: 6 quick start + 11 document + 9 content + 5 template = 31 tools (NO OPTIONAL PARAMETERS!)

    print(f"✅ Registered 31 essential tools for Copilot Studio (NO optional parameters)")

# Register all tools
register_tools()

def main():
    """Main entry point with transport configuration."""
    config = get_transport_config()
    transport = config['transport']

    print(f"Starting Word Document MCP Server LIGHT with {transport} transport...")

    if transport == 'stdio':
        print("Server running on stdio transport")
        mcp.run(transport='stdio')
    elif transport in ['streamable-http', 'http']:
        host = config['host']
        port = config['port']
        path = config['path']
        print(f"Server running on {transport} transport at http://{host}:{port}{path}")
        mcp.run(transport='streamable-http', host=host, port=port, path=path)
    elif transport == 'sse':
        host = config['host']
        port = config['port']
        print(f"Server running on SSE transport at http://{host}:{port}/sse")
        mcp.run(transport='sse', host=host, port=port)

if __name__ == "__main__":
    main()
