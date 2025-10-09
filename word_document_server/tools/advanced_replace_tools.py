"""
Tools for advanced search and replace in Word documents.
Works with all types of content: text, tables, headers, footers.
"""

import io
import tempfile
from docx import Document
from word_document_server.core import advanced_replace
from word_document_server.utils.file_utils import ensure_docx_extension
from word_document_server.utils.azure_storage import get_document_from_storage, save_document_to_storage


async def replace_text_universal(filename: str, find_text: str, replace_text: str) -> str:
    """
    Universal text replacement that works everywhere in the document.
    Searches and replaces in: paragraphs, tables, headers, and footers.

    Args:
        filename: Name of the Word document
        find_text: Text to find (can be in normal text or placeholders)
        replace_text: Text to replace with

    Returns:
        Success message with replacement details
    """
    filename = ensure_docx_extension(filename)

    try:
        # Get document from Azure Blob Storage
        success, doc_data, message = get_document_from_storage(filename)
        if not success:
            return f"Document {filename} does not exist: {message}"

        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp.write(doc_data)
            tmp_path = tmp.name

        # Perform replacement
        result = advanced_replace.replace_text_everywhere(tmp_path, find_text, replace_text)

        # Save back to Azure Storage
        with open(tmp_path, 'rb') as f:
            doc_data = f.read()

        save_success, save_message = save_document_to_storage(filename, doc_data)

        # Clean up temp file
        import os
        os.unlink(tmp_path)

        if not save_success:
            return f"Failed to save document: {save_message}"

        if result["total_replacements"] == 0:
            return f"No occurrences of '{find_text}' found in {filename}"

        # Get document URL
        from word_document_server.utils.azure_storage import get_document_url
        url = get_document_url(filename)

        locations_str = "\n  - ".join(result["locations"])
        return (
            f"Replaced '{find_text}' with '{replace_text}' in {filename}\n"
            f"Total replacements: {result['total_replacements']}\n"
            f"Locations:\n  - {locations_str}\n"
            f"Document URL: {url}"
        )

    except Exception as e:
        return f"Error: {str(e)}"


async def list_content_controls(filename: str) -> str:
    """
    List all ContentControls (structured fields) in the document.
    Note: ContentControls support coming soon.

    Args:
        filename: Name of the Word document

    Returns:
        List of ContentControls with their tags and current values
    """
    filename = ensure_docx_extension(filename)
    return "ContentControls listing coming soon. Use regular text placeholders for now."
