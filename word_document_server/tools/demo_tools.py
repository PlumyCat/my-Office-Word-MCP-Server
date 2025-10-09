"""
Demo tools with NO required parameters for Copilot Studio testing.
These tools have sensible defaults for everything.
"""
import json
from datetime import datetime
from word_document_server.tools import document_tools, template_tools


async def demo_list_all_templates() -> str:
    """
    List ALL document templates available. No parameters needed.
    This is a demo tool that shows all templates in the system.

    Returns:
        JSON list of all templates
    """
    return await template_tools.list_document_templates(category="")


async def demo_list_all_documents() -> str:
    """
    List ALL Word documents in storage. No parameters needed.
    This is a demo tool that shows all documents currently stored.

    Returns:
        List of all documents
    """
    return await document_tools.list_available_documents(directory=".")


async def demo_create_test_document() -> str:
    """
    Create a simple test document with current timestamp. No parameters needed.
    Creates a document named 'test_YYYYMMDD_HHMMSS.docx' automatically.

    Returns:
        Success message with document name
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{timestamp}.docx"
    return await document_tools.create_document(filename=filename)


async def demo_get_storage_info() -> str:
    """
    Get information about Azure Storage configuration. No parameters needed.
    Shows connection status and container names.

    Returns:
        JSON with storage configuration info
    """
    return await document_tools.debug_storage()


async def demo_create_business_letter() -> str:
    """
    Create a business letter from template. No parameters needed.
    Uses the 'business_letter' template from the 'business' category.

    Returns:
        Success message with document URL
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_doc_name = f"business_letter_{timestamp}.docx"

    try:
        result = await template_tools.create_document_from_template(
            template_name="business_letter",
            new_document_name=new_doc_name,
            category="business",
            variables={}
        )
        return result
    except Exception as e:
        return f"Could not create business letter. Error: {str(e)}\nMake sure the 'business_letter.docx' template exists in the 'business' category."


async def simple_get_document_info(filename: str) -> str:
    """
    Get information about a specific document by filename.

    Args:
        filename: The name of the Word document (e.g., 'report.docx')

    Returns:
        Document information including size, creation date, etc.
    """
    from word_document_server.tools import document_tools
    return await document_tools.get_document_info(filename=filename)


async def simple_find_document(search_term: str) -> str:
    """
    Find documents containing a search term in their filename.

    Args:
        search_term: Text to search for in document names (e.g., 'report', 'invoice')

    Returns:
        List of documents matching the search term
    """
    from word_document_server.tools import document_tools

    # Get all documents
    all_docs_result = await document_tools.list_available_documents(directory=".")

    # Simple search in the result string
    if search_term.lower() in all_docs_result.lower():
        # Extract matching lines
        lines = all_docs_result.split('\n')
        matching = [line for line in lines if search_term.lower() in line.lower()]
        if matching:
            return f"Documents matching '{search_term}':\n" + '\n'.join(matching)

    return f"No documents found matching '{search_term}'"


async def simple_create_document_with_title(filename: str, title: str) -> str:
    """
    Create a new Word document with a specific filename and title.

    Args:
        filename: Name for the document (e.g., 'monthly_report.docx')
        title: Title to add to the document (e.g., 'Monthly Sales Report')

    Returns:
        Success message with download URL
    """
    from word_document_server.tools import document_tools

    # Ensure .docx extension
    if not filename.endswith('.docx'):
        filename = filename + '.docx'

    return await document_tools.create_document(
        filename=filename,
        title=title,
        author="Copilot Studio"
    )


async def simple_create_from_template(template_name: str, new_filename: str) -> str:
    """
    Create a document from a template with simple parameters.

    Args:
        template_name: Name of template to use (e.g., 'business_letter', 'invoice')
        new_filename: Name for the new document (e.g., 'letter_client_martin.docx')

    Returns:
        Success message with download URL
    """
    from word_document_server.tools import template_tools

    # Ensure .docx extension
    if not new_filename.endswith('.docx'):
        new_filename = new_filename + '.docx'

    # Try different categories
    for category in ['business', 'personal', 'academic', 'general']:
        result = await template_tools.create_document_from_template(
            template_name=template_name,
            new_document_name=new_filename,
            category=category,
            variables={}
        )

        # If successful, return result
        if "created from template" in result.lower():
            return result

    return f"Template '{template_name}' not found in any category. Use demo_list_all_templates to see available templates."


async def simple_add_paragraph(filename: str, text: str) -> str:
    """
    Add a paragraph to an existing document.

    Args:
        filename: Document name (e.g., 'report.docx')
        text: Paragraph text to add

    Returns:
        Success message
    """
    from word_document_server.tools import content_tools

    return await content_tools.add_paragraph(
        filename=filename,
        text=text,
        style=None
    )


async def demo_hello_world() -> str:
    """
    Simple hello world test. No parameters needed.
    This is the simplest possible tool to verify MCP connection works.

    Returns:
        Hello world message with server info
    """
    info = {
        "message": "Hello from Word MCP Server!",
        "status": "Server is running correctly",
        "timestamp": datetime.now().isoformat(),
        "tools_available": "31 Word document tools",
        "templates_supported": True,
        "azure_storage": True
    }
    return json.dumps(info, indent=2)
