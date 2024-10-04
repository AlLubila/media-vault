from google.cloud import storage
from google.oauth2 import service_account
import os
import json

# Initialize the Google Cloud Storage client
credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
if credentials_json:
    try:
        credentials_dict = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        client = storage.Client(credentials=credentials)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON")
        client = None
else:
    client = storage.Client()

BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'your-bucket-name')
bucket = client.bucket(BUCKET_NAME) if client else None

def upload_file(file_path, destination_blob_name):
    """Uploads a file to the bucket."""
    if not bucket:
        raise Exception("Google Cloud Storage client not initialized")
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    return blob.public_url

def download_file(source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    if not bucket:
        raise Exception("Google Cloud Storage client not initialized")
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

def delete_file(blob_name):
    """Deletes a blob from the bucket."""
    if not bucket:
        raise Exception("Google Cloud Storage client not initialized")
    blob = bucket.blob(blob_name)
    blob.delete()

def get_storage_usage():
    """Gets the total storage usage for the bucket."""
    if not bucket:
        raise Exception("Google Cloud Storage client not initialized")
    total_size = sum(blob.size for blob in bucket.list_blobs())
    return total_size