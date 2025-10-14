"""
Azure Blob Storage integration for Word Document Server.
Handles file persistence with TTL (Time To Live) cleanup.
"""
import os
import io
import tempfile
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential

# Set up logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Set log level based on environment variable
    log_level = os.getenv('AZURE_STORAGE_LOG_LEVEL', 'INFO').upper()
    if log_level == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    elif log_level == 'WARNING':
        logger.setLevel(logging.WARNING)
    elif log_level == 'ERROR':
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)


class AzureBlobStorage:
    """Azure Blob Storage client with TTL support."""

    def __init__(self):
        """Initialize Azure Blob Storage client."""
        # Try to get connection string first, fallback to managed identity
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
        container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'word-documents')

        if connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        elif account_name:
            # Use managed identity
            credential = DefaultAzureCredential()
            account_url = f"https://{account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(account_url, credential=credential)
        else:
            # Fallback to local storage if no Azure config
            self.blob_service_client = None

        self.container_name = container_name
        self.ttl_hours = int(os.getenv('DOCUMENT_TTL_HOURS', '24'))

        # Initialize container if using Azure
        if self.blob_service_client:
            self._ensure_container_exists()

    def _ensure_container_exists(self):
        """Ensure the blob container exists - PRIVATE by default for security."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                # SECURITY: Create private container (no public access)
                container_client.create_container()
                logger.info(f"Created PRIVATE container: {self.container_name}")
        except Exception as e:
            logger.error(f"Warning: Could not ensure container exists: {e}")

    def is_enabled(self) -> bool:
        """Check if Azure Blob Storage is enabled."""
        return self.blob_service_client is not None

    def save_file(self, filename: str, file_data: bytes) -> Tuple[bool, str]:
        """
        Save file to Azure Blob Storage with TTL metadata.

        Args:
            filename: Name of the file
            file_data: Binary data of the file

        Returns:
            Tuple of (success, message/error)
        """
        logger.info(f"Attempting to save file: {filename} (size: {len(file_data)} bytes)")

        if not self.is_enabled():
            logger.info("Azure Blob Storage not enabled, falling back to local storage")
            # Fallback to local storage
            return self._save_local(filename, file_data)

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )

            # Set expiry time
            expiry_time = datetime.utcnow() + timedelta(hours=self.ttl_hours)

            metadata = {
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': expiry_time.isoformat(),
                'ttl_hours': str(self.ttl_hours)
            }

            logger.info(f"Uploading blob: {filename} to container: {self.container_name}")
            blob_client.upload_blob(
                file_data,
                overwrite=True,
                metadata=metadata,
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

            logger.info(f"Successfully saved file: {filename}")
            return True, f"File {filename} saved to Azure Blob Storage (expires in {self.ttl_hours}h)"

        except Exception as e:
            logger.error(f"Failed to save file {filename}: {str(e)}")
            return False, f"Failed to save to Azure Blob Storage: {str(e)}"

    def get_file(self, filename: str) -> Tuple[bool, Optional[bytes], str]:
        """
        Retrieve file from Azure Blob Storage with case-insensitive search.

        Args:
            filename: Name of the file to retrieve

        Returns:
            Tuple of (success, file_data, message)
        """
        logger.info(f"Attempting to retrieve file: {filename}")

        if not self.is_enabled():
            logger.info("Azure Blob Storage not enabled, falling back to local storage")
            # Fallback to local storage
            return self._get_local(filename)

        try:
            # First try exact match
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )

            # Check if blob exists and get metadata
            try:
                logger.info(f"Checking for exact match: {filename}")
                properties = blob_client.get_blob_properties()
                metadata = properties.metadata or {}

                # Check if file has expired
                if 'expires_at' in metadata:
                    expires_at = datetime.fromisoformat(metadata['expires_at'])
                    if datetime.utcnow() > expires_at:
                        logger.info(f"File {filename} has expired, deleting")
                        # File has expired, delete it
                        blob_client.delete_blob()
                        return False, None, f"File {filename} has expired and was deleted"

                # File found with exact match
                logger.info(f"Found file with exact match: {filename}")

            except ResourceNotFoundError:
                logger.info(f"Exact match not found for {filename}, trying case-insensitive search")

                # Try case-insensitive search
                container_client = self.blob_service_client.get_container_client(self.container_name)
                filename_lower = filename.lower()
                matching_blob = None

                logger.info(f"Searching for case-insensitive match of: {filename_lower}")
                for blob in container_client.list_blobs():
                    if blob.name.lower() == filename_lower:
                        logger.info(f"Found case-insensitive match: {blob.name} for requested {filename}")
                        matching_blob = blob.name
                        break

                if not matching_blob:
                    logger.warning(f"No case-insensitive match found for: {filename}")
                    # List all blobs for debugging
                    all_blobs = [blob.name for blob in container_client.list_blobs()]
                    logger.info(f"Available blobs: {all_blobs}")
                    return False, None, f"File {filename} not found (searched case-insensitively). Available files: {all_blobs}"

                # Update blob_client to use the found filename
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=matching_blob
                )

                # Re-check metadata for the found file
                properties = blob_client.get_blob_properties()
                metadata = properties.metadata or {}

                # Check if file has expired
                if 'expires_at' in metadata:
                    expires_at = datetime.fromisoformat(metadata['expires_at'])
                    if datetime.utcnow() > expires_at:
                        logger.info(f"Found file {matching_blob} has expired, deleting")
                        blob_client.delete_blob()
                        return False, None, f"File {filename} (found as {matching_blob}) has expired and was deleted"

            # Download the blob
            logger.info(f"Downloading blob data")
            download_stream = blob_client.download_blob()
            file_data = download_stream.readall()
            logger.info(f"Successfully retrieved {len(file_data)} bytes")

            return True, file_data, f"File {filename} retrieved from Azure Blob Storage"

        except Exception as e:
            logger.error(f"Failed to retrieve file {filename}: {str(e)}")
            return False, None, f"Failed to retrieve from Azure Blob Storage: {str(e)}"

    def list_files(self) -> Tuple[bool, list, str]:
        """
        List all files in storage.

        Returns:
            Tuple of (success, file_list, message)
        """
        logger.info("Listing files in storage")

        if not self.is_enabled():
            logger.info("Azure Blob Storage not enabled, listing local files")
            return self._list_local()

        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blob_list = []

            logger.info(f"Listing blobs from container: {self.container_name}")
            for blob in container_client.list_blobs(include=['metadata']):
                metadata = blob.metadata or {}
                logger.debug(f"Found blob: {blob.name} (size: {blob.size}, metadata: {metadata})")

                # Check expiry
                expired = False
                if 'expires_at' in metadata:
                    expires_at = datetime.fromisoformat(metadata['expires_at'])
                    expired = datetime.utcnow() > expires_at

                blob_info = {
                    'name': blob.name,
                    'size': blob.size,
                    'created': metadata.get('created_at', 'Unknown'),
                    'expires': metadata.get('expires_at', 'No expiry'),
                    'expired': expired
                }
                blob_list.append(blob_info)

            logger.info(f"Found {len(blob_list)} files in storage")
            return True, blob_list, f"Found {len(blob_list)} files"

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return False, [], f"Failed to list files: {str(e)}"

    def cleanup_expired_files(self) -> Tuple[bool, int, str]:
        """
        Clean up expired files from storage.

        Returns:
            Tuple of (success, count_deleted, message)
        """
        if not self.is_enabled():
            return True, 0, "Azure Blob Storage not enabled, no cleanup needed"

        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            deleted_count = 0

            for blob in container_client.list_blobs(include=['metadata']):
                metadata = blob.metadata or {}

                if 'expires_at' in metadata:
                    expires_at = datetime.fromisoformat(metadata['expires_at'])
                    if datetime.utcnow() > expires_at:
                        blob_client = self.blob_service_client.get_blob_client(
                            container=self.container_name,
                            blob=blob.name
                        )
                        blob_client.delete_blob()
                        deleted_count += 1

            return True, deleted_count, f"Cleaned up {deleted_count} expired files"

        except Exception as e:
            return False, 0, f"Failed to cleanup files: {str(e)}"

    def get_file_url(self, filename: str, expiry_hours: int = 24) -> Optional[str]:
        """
        Get SAS URL for a file with temporary access if Azure Blob Storage is enabled.

        Args:
            filename: Name of the file
            expiry_hours: Hours until the SAS URL expires (default: 24)

        Returns:
            SAS URL with temporary access or None if not available
        """
        if not self.is_enabled():
            return None

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )

            # Check if blob exists
            if not blob_client.exists():
                return None

            # SECURITY: Always generate SAS token with TTL - no fallback to public URL
            try:
                # Get account key from connection string
                connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                if not connection_string:
                    logger.error("AZURE_STORAGE_CONNECTION_STRING not configured - cannot generate SAS URL")
                    return None

                # Extract account name and key from connection string
                parts = dict(item.split('=', 1) for item in connection_string.split(';') if '=' in item)
                account_name = parts.get('AccountName')
                account_key = parts.get('AccountKey')

                if not account_name or not account_key:
                    logger.error("Could not extract AccountName or AccountKey from connection string")
                    return None

                # Generate SAS token with TTL
                sas_token = generate_blob_sas(
                    account_name=account_name,
                    container_name=self.container_name,
                    blob_name=filename,
                    account_key=account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
                )

                # Return URL with SAS token
                sas_url = f"{blob_client.url}?{sas_token}"
                logger.debug(f"Generated SAS URL for {filename} (expires in {expiry_hours}h)")
                return sas_url

            except Exception as e:
                logger.error(f"Failed to generate SAS token for {filename}: {e}")
                return None

        except Exception as e:
            logger.error(f"Error getting URL for {filename}: {e}")
            return None

    def debug_storage_state(self) -> str:
        """
        Debug function to show the current state of storage.
        Returns detailed information about configuration and available files.
        """
        debug_info = []
        debug_info.append(f"Azure Blob Storage enabled: {self.is_enabled()}")
        debug_info.append(f"Container name: {self.container_name}")
        debug_info.append(f"TTL hours: {self.ttl_hours}")

        # Check environment variables
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
        debug_info.append(f"Connection string configured: {'Yes' if connection_string else 'No'}")
        debug_info.append(f"Account name configured: {account_name if account_name else 'No'}")

        if self.is_enabled():
            try:
                # List all files with detailed info
                success, file_list, message = self.list_files()
                if success:
                    debug_info.append(f"\nFiles in storage ({len(file_list)}):")
                    for file_info in file_list:
                        debug_info.append(f"  - {file_info['name']} ({file_info['size']} bytes)")
                        debug_info.append(f"    Created: {file_info['created']}")
                        debug_info.append(f"    Expires: {file_info['expires']}")
                        debug_info.append(f"    Expired: {file_info['expired']}")
                else:
                    debug_info.append(f"\nFailed to list files: {message}")
            except Exception as e:
                debug_info.append(f"\nError listing files: {str(e)}")
        else:
            debug_info.append("\nAzure Blob Storage not configured - using local storage fallback")

        return "\n".join(debug_info)

    # Fallback methods for local storage
    def _save_local(self, filename: str, file_data: bytes) -> Tuple[bool, str]:
        """Save file locally as fallback."""
        try:
            with open(filename, 'wb') as f:
                f.write(file_data)
            return True, f"File {filename} saved locally (Azure not configured)"
        except Exception as e:
            return False, f"Failed to save locally: {str(e)}"

    def _get_local(self, filename: str) -> Tuple[bool, Optional[bytes], str]:
        """Get file locally as fallback."""
        try:
            if not os.path.exists(filename):
                return False, None, f"File {filename} not found locally"

            with open(filename, 'rb') as f:
                data = f.read()
            return True, data, f"File {filename} retrieved locally"
        except Exception as e:
            return False, None, f"Failed to retrieve locally: {str(e)}"

    def _list_local(self) -> Tuple[bool, list, str]:
        """List files locally as fallback."""
        try:
            files = [f for f in os.listdir('.') if f.endswith('.docx')]
            file_list = []
            for f in files:
                stat = os.stat(f)
                file_list.append({
                    'name': f,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'expires': 'No expiry (local storage)',
                    'expired': False
                })
            return True, file_list, f"Found {len(file_list)} local files"
        except Exception as e:
            return False, [], f"Failed to list local files: {str(e)}"


# Global storage instance
storage = AzureBlobStorage()


def save_document_to_storage(filename: str, doc_data: bytes) -> Tuple[bool, str]:
    """Helper function to save document to storage."""
    return storage.save_file(filename, doc_data)


def get_document_from_storage(filename: str) -> Tuple[bool, Optional[bytes], str]:
    """Helper function to get document from storage."""
    return storage.get_file(filename)


def get_document_url(filename: str) -> Optional[str]:
    """Helper function to get document URL."""
    return storage.get_file_url(filename)


def list_stored_documents():
    """Helper function to list stored documents."""
    return storage.list_files()


def cleanup_expired_documents():
    """Helper function to cleanup expired documents."""
    return storage.cleanup_expired_files()


def debug_storage_state():
    """Helper function to debug storage state."""
    return storage.debug_storage_state()