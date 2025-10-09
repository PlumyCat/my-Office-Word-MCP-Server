"""
Template storage utilities for Word Document Server.
Handles storage and retrieval of document templates in Azure Blob Storage.
"""
import os
import io
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential

# Set up logging
logger = logging.getLogger(__name__)

class TemplateStorage:
    """Azure Blob Storage client for template management."""

    def __init__(self):
        """Initialize Azure Blob Storage client for templates."""
        # Try to get connection string first, fallback to managed identity
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
        self.templates_container = os.getenv('AZURE_TEMPLATES_CONTAINER_NAME', 'word-templates')

        if connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        elif account_name:
            # Use managed identity
            credential = DefaultAzureCredential()
            account_url = f"https://{account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(account_url, credential=credential)
        else:
            self.blob_service_client = None
            logger.warning("No Azure Storage configuration found")

        # Ensure templates container exists
        if self.blob_service_client:
            try:
                container_client = self.blob_service_client.get_container_client(self.templates_container)
                if not container_client.exists():
                    container_client.create_container()
                    logger.info(f"Created templates container: {self.templates_container}")
            except Exception as e:
                logger.error(f"Failed to create templates container: {str(e)}")

    def _get_template_blob_name(self, template_name: str, category: str = "general") -> str:
        """Generate blob name for template."""
        # Ensure .docx extension
        if not template_name.endswith('.docx'):
            template_name += '.docx'
        # Use the direct category structure: category/template_name.docx
        return f"{category}/{template_name}"

    def list_templates(self, category: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        List all available templates.

        Args:
            category: Optional category filter

        Returns:
            Tuple of (success, templates_list, message)
        """
        if not self.blob_service_client:
            return False, [], "Azure Storage not configured"

        try:
            container_client = self.blob_service_client.get_container_client(self.templates_container)

            # Determine prefix for filtering
            # Support both structures: templates/category/ and category/ directly
            prefix = ""
            if category:
                prefix = f"{category}/"

            templates = []
            blobs = container_client.list_blobs(name_starts_with=prefix)

            for blob in blobs:
                if blob.name.endswith('.docx'):
                    # Parse template info from blob name and metadata
                    path_parts = blob.name.split('/')

                    # Support both structures:
                    # Structure 1: templates/category/name.docx
                    # Structure 2: category/name.docx (current user structure)
                    if len(path_parts) >= 3 and path_parts[0] == "templates":
                        template_category = path_parts[1]
                        template_name = path_parts[2]
                    elif len(path_parts) >= 2:  # category/name.docx
                        template_category = path_parts[0]
                        template_name = path_parts[1]
                    else:
                        continue  # Skip files not following expected structure

                    # Get blob metadata
                    blob_client = container_client.get_blob_client(blob.name)
                    properties = blob_client.get_blob_properties()

                    template_info = {
                        'name': template_name.replace('.docx', ''),
                        'category': template_category,
                        'size': blob.size,
                        'created': properties.creation_time.isoformat() if properties.creation_time else None,
                        'modified': properties.last_modified.isoformat() if properties.last_modified else None,
                        'description': properties.metadata.get('description', 'No description'),
                        'author': properties.metadata.get('author', 'Unknown'),
                        'blob_name': blob.name
                    }
                    templates.append(template_info)

            return True, templates, f"Found {len(templates)} template(s)"

        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            return False, [], f"Failed to list templates: {str(e)}"

    def get_template(self, template_name: str, category: str = "general") -> Tuple[bool, bytes, str]:
        """
        Retrieve a template from storage.

        Args:
            template_name: Name of the template
            category: Template category

        Returns:
            Tuple of (success, template_data, message)
        """
        if not self.blob_service_client:
            return False, b'', "Azure Storage not configured"

        try:
            blob_name = self._get_template_blob_name(template_name, category)
            container_client = self.blob_service_client.get_container_client(self.templates_container)
            blob_client = container_client.get_blob_client(blob_name)

            if not blob_client.exists():
                return False, b'', f"Template '{template_name}' in category '{category}' not found"

            # Download template data
            template_data = blob_client.download_blob().readall()
            return True, template_data, "Template retrieved successfully"

        except ResourceNotFoundError:
            return False, b'', f"Template '{template_name}' in category '{category}' not found"
        except Exception as e:
            logger.error(f"Failed to get template: {str(e)}")
            return False, b'', f"Failed to retrieve template: {str(e)}"

    def save_template(self, template_name: str, template_data: bytes, category: str = "general",
                     description: str = "", author: str = "") -> Tuple[bool, str]:
        """
        Save a template to storage.

        Args:
            template_name: Name of the template
            template_data: Template file data
            category: Template category
            description: Template description
            author: Template author

        Returns:
            Tuple of (success, message)
        """
        if not self.blob_service_client:
            return False, "Azure Storage not configured"

        try:
            blob_name = self._get_template_blob_name(template_name, category)
            container_client = self.blob_service_client.get_container_client(self.templates_container)
            blob_client = container_client.get_blob_client(blob_name)

            # Set metadata
            metadata = {
                'description': description,
                'author': author,
                'created': datetime.utcnow().isoformat(),
                'category': category
            }

            # Set content settings for Word documents
            content_settings = ContentSettings(
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

            # Upload the template
            blob_client.upload_blob(
                template_data,
                overwrite=True,
                metadata=metadata,
                content_settings=content_settings
            )

            logger.info(f"Template '{template_name}' saved to category '{category}'")
            return True, f"Template '{template_name}' saved successfully in category '{category}'"

        except Exception as e:
            logger.error(f"Failed to save template: {str(e)}")
            return False, f"Failed to save template: {str(e)}"

    def delete_template(self, template_name: str, category: str = "general") -> Tuple[bool, str]:
        """
        Delete a template from storage.

        Args:
            template_name: Name of the template
            category: Template category

        Returns:
            Tuple of (success, message)
        """
        if not self.blob_service_client:
            return False, "Azure Storage not configured"

        try:
            blob_name = self._get_template_blob_name(template_name, category)
            container_client = self.blob_service_client.get_container_client(self.templates_container)
            blob_client = container_client.get_blob_client(blob_name)

            if not blob_client.exists():
                return False, f"Template '{template_name}' in category '{category}' not found"

            blob_client.delete_blob()
            logger.info(f"Template '{template_name}' deleted from category '{category}'")
            return True, f"Template '{template_name}' deleted successfully"

        except ResourceNotFoundError:
            return False, f"Template '{template_name}' in category '{category}' not found"
        except Exception as e:
            logger.error(f"Failed to delete template: {str(e)}")
            return False, f"Failed to delete template: {str(e)}"

    def get_template_url(self, template_name: str, category: str = "general",
                        expires_hours: int = 24) -> Optional[str]:
        """
        Get a temporary download URL for a template.

        Args:
            template_name: Name of the template
            category: Template category
            expires_hours: URL expiration time in hours

        Returns:
            Download URL or None if not available
        """
        if not self.blob_service_client:
            return None

        try:
            blob_name = self._get_template_blob_name(template_name, category)
            container_client = self.blob_service_client.get_container_client(self.templates_container)
            blob_client = container_client.get_blob_client(blob_name)

            if not blob_client.exists():
                return None

            # Generate SAS URL for download
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions

            # Try to get account key from connection string or separate env var
            account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
            account_name = blob_client.account_name

            if not account_key:
                # Try extracting from connection string
                connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                if connection_string:
                    parts = dict(item.split('=', 1) for item in connection_string.split(';') if '=' in item)
                    account_key = parts.get('AccountKey')
                    if not account_name:
                        account_name = parts.get('AccountName')

            if not account_key or not account_name:
                logger.warning("No account key/name available for SAS URL generation")
                return blob_client.url  # Fallback to regular URL

            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.templates_container,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expires_hours)
            )

            return f"{blob_client.url}?{sas_token}"

        except Exception as e:
            logger.error(f"Failed to generate template URL: {str(e)}")
            return None


# Global instance
_template_storage = None

def get_template_storage() -> TemplateStorage:
    """Get the global template storage instance."""
    global _template_storage
    if _template_storage is None:
        _template_storage = TemplateStorage()
    return _template_storage

# Convenience functions
def list_templates(category: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]], str]:
    """List all available templates."""
    return get_template_storage().list_templates(category)

def get_template(template_name: str, category: str = "general") -> Tuple[bool, bytes, str]:
    """Retrieve a template from storage."""
    return get_template_storage().get_template(template_name, category)

def save_template(template_name: str, template_data: bytes, category: str = "general",
                 description: str = "", author: str = "") -> Tuple[bool, str]:
    """Save a template to storage."""
    return get_template_storage().save_template(template_name, template_data, category, description, author)

def delete_template(template_name: str, category: str = "general") -> Tuple[bool, str]:
    """Delete a template from storage."""
    return get_template_storage().delete_template(template_name, category)

def get_template_url(template_name: str, category: str = "general", expires_hours: int = 24) -> Optional[str]:
    """Get a temporary download URL for a template."""
    return get_template_storage().get_template_url(template_name, category, expires_hours)