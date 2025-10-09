"""
Template management tools for Word Document Server.
Provides MCP tools for creating, listing, and using document templates.
"""
import io
import json
from typing import Optional, Dict, Any
from docx import Document

from word_document_server.utils.file_utils import ensure_docx_extension
from word_document_server.utils.template_storage import list_templates, get_template, save_template, get_template_url
from word_document_server.utils.azure_storage import get_document_from_storage, save_document_to_storage, get_document_url


async def list_document_templates(category: str = "") -> str:
    """
    List all available document templates.

    Args:
        category: Category filter (e.g., "business", "academic", "personal"). Leave empty to list all templates.

    Returns:
        JSON string with list of templates
    """
    try:
        # Convert empty string to None for the storage function
        category_filter = category if category else None
        success, templates, message = list_templates(category_filter)

        if not success:
            return f"Failed to list templates: {message}"

        if not templates:
            category_msg = f" in category '{category}'" if category else ""
            return f"No templates found{category_msg}"

        # Format response
        result = {
            "total_templates": len(templates),
            "category_filter": category,
            "templates": []
        }

        for template in templates:
            template_info = {
                "name": template['name'],
                "category": template['category'],
                "description": template['description'],
                "author": template['author'],
                "created": template['created'],
                "size_kb": round(template['size'] / 1024, 2) if template['size'] else 0
            }

            # Add download URL if available
            url = get_template_url(template['name'], template['category'])
            if url:
                template_info['download_url'] = url

            result["templates"].append(template_info)

        return json.dumps(result, indent=2)

    except Exception as e:
        return f"Error listing templates: {str(e)}"


async def add_document_template(source_document: str, template_name: str,
                               category: str = "general", description: str = "",
                               author: str = "Unknown") -> str:
    """
    Add a document as a template to the template library.

    Args:
        source_document: Path to the source Word document to use as template
        template_name: Name for the new template (without .docx extension)
        category: Template category (default: "general")
        description: Description of the template
        author: Author of the template

    Returns:
        Success message or error description
    """
    source_document = ensure_docx_extension(source_document)

    # Clean template name (remove .docx if provided)
    if template_name.endswith('.docx'):
        template_name = template_name[:-5]

    try:
        # Get the source document from storage
        success, doc_data, message = get_document_from_storage(source_document)

        if not success:
            return f"Source document '{source_document}' not found: {message}"

        # Validate it's a proper Word document by trying to open it
        try:
            doc = Document(io.BytesIO(doc_data))
            # Basic validation - check if we can access paragraphs
            _ = len(doc.paragraphs)
        except Exception as e:
            return f"Source document '{source_document}' is not a valid Word document: {str(e)}"

        # Save as template
        success, save_message = save_template(
            template_name=template_name,
            template_data=doc_data,
            category=category,
            description=description,
            author=author
        )

        if success:
            # Try to get template URL
            url = get_template_url(template_name, category)
            if url:
                return f"{save_message}\nTemplate URL: {url}"
            else:
                return save_message
        else:
            return f"Failed to save template: {save_message}"

    except Exception as e:
        return f"Error adding template: {str(e)}"


async def create_document_from_template(template_name: str, new_document_name: str,
                                      category: str = "general",
                                      variables: Dict[str, str] = {}) -> str:
    """
    Create a new document from an existing template.

    Args:
        template_name: Name of the template to use
        new_document_name: Name for the new document
        category: Template category (default: "general")
        variables: Optional dictionary of variables to replace in the document
                  (format: {"{{variable_name}}": "replacement_value"})

    Returns:
        Success message with document URL or error description
    """
    new_document_name = ensure_docx_extension(new_document_name)

    # Clean template name (remove .docx if provided)
    if template_name.endswith('.docx'):
        template_name = template_name[:-5]

    try:
        # Get the template from storage
        success, template_data, message = get_template(template_name, category)

        if not success:
            return f"Template '{template_name}' in category '{category}' not found: {message}"

        # Load the template as a Document
        doc = Document(io.BytesIO(template_data))

        # Apply variable substitutions if provided
        if variables:
            # Replace variables in paragraphs
            for paragraph in doc.paragraphs:
                for var_name, var_value in variables.items():
                    if var_name in paragraph.text:
                        # Replace in all runs to preserve formatting
                        for run in paragraph.runs:
                            if var_name in run.text:
                                run.text = run.text.replace(var_name, var_value)

            # Replace variables in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            for var_name, var_value in variables.items():
                                if var_name in paragraph.text:
                                    for run in paragraph.runs:
                                        if var_name in run.text:
                                            run.text = run.text.replace(var_name, var_value)

            # Replace variables in headers and footers
            for section in doc.sections:
                # Headers
                if section.header:
                    for paragraph in section.header.paragraphs:
                        for var_name, var_value in variables.items():
                            if var_name in paragraph.text:
                                for run in paragraph.runs:
                                    if var_name in run.text:
                                        run.text = run.text.replace(var_name, var_value)

                # Footers
                if section.footer:
                    for paragraph in section.footer.paragraphs:
                        for var_name, var_value in variables.items():
                            if var_name in paragraph.text:
                                for run in paragraph.runs:
                                    if var_name in run.text:
                                        run.text = run.text.replace(var_name, var_value)

        # Save the new document
        doc_buffer = io.BytesIO()
        doc.save(doc_buffer)
        doc_data = doc_buffer.getvalue()
        doc_buffer.close()

        # Save to document storage
        success, save_message = save_document_to_storage(new_document_name, doc_data)

        if success:
            # Get document URL if available
            url = get_document_url(new_document_name)

            variables_info = ""
            if variables:
                variables_info = f"\nApplied {len(variables)} variable substitution(s): {', '.join(variables.keys())}"

            if url:
                return f"Document '{new_document_name}' created from template '{template_name}' in category '{category}'{variables_info}\nDocument URL: {url}"
            else:
                return f"Document '{new_document_name}' created from template '{template_name}' in category '{category}'{variables_info}"
        else:
            return f"Failed to save new document: {save_message}"

    except Exception as e:
        return f"Error creating document from template: {str(e)}"


async def get_template_info(template_name: str, category: str = "general") -> str:
    """
    Get detailed information about a specific template.

    Args:
        template_name: Name of the template
        category: Template category (default: "general")

    Returns:
        JSON string with template information
    """
    # Clean template name (remove .docx if provided)
    if template_name.endswith('.docx'):
        template_name = template_name[:-5]

    try:
        # Get template data to analyze
        success, template_data, message = get_template(template_name, category)

        if not success:
            return f"Template '{template_name}' in category '{category}' not found: {message}"

        # Load template to analyze structure
        doc = Document(io.BytesIO(template_data))

        # Analyze template content
        info = {
            "name": template_name,
            "category": category,
            "statistics": {
                "paragraphs": len(doc.paragraphs),
                "tables": len(doc.tables),
                "sections": len(doc.sections)
            },
            "structure": [],
            "variables_found": []
        }

        # Analyze structure and find variables
        variables_found = set()

        for i, paragraph in enumerate(doc.paragraphs):
            if paragraph.text.strip():
                para_info = {
                    "type": "paragraph",
                    "index": i,
                    "text": paragraph.text[:100] + "..." if len(paragraph.text) > 100 else paragraph.text
                }

                # Look for style information
                if paragraph.style and paragraph.style.name != 'Normal':
                    para_info["style"] = paragraph.style.name

                info["structure"].append(para_info)

                # Find variables in format {{variable_name}}
                import re
                vars_in_text = re.findall(r'\{\{([^}]+)\}\}', paragraph.text)
                variables_found.update(vars_in_text)

        # Add table information
        for i, table in enumerate(doc.tables):
            table_info = {
                "type": "table",
                "index": i,
                "rows": len(table.rows),
                "columns": len(table.columns) if table.rows else 0
            }
            info["structure"].append(table_info)

        info["variables_found"] = sorted(list(variables_found))

        # Add download URL if available
        url = get_template_url(template_name, category)
        if url:
            info["download_url"] = url

        return json.dumps(info, indent=2)

    except Exception as e:
        return f"Error getting template info: {str(e)}"


async def delete_document_template(template_name: str, category: str = "general") -> str:
    """
    Delete a template from the template library.

    Args:
        template_name: Name of the template to delete
        category: Template category (default: "general")

    Returns:
        Success message or error description
    """
    # Clean template name (remove .docx if provided)
    if template_name.endswith('.docx'):
        template_name = template_name[:-5]

    try:
        from word_document_server.utils.template_storage import delete_template

        success, message = delete_template(template_name, category)
        return message

    except Exception as e:
        return f"Error deleting template: {str(e)}"