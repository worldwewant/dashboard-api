'''
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

'''

"""Google Cloud Storage interactions"""

import logging
from datetime import datetime, date
from datetime import timedelta
from typing import Iterator

from google.cloud import storage
from google.cloud.storage import Client, Blob, Bucket
from google.oauth2 import service_account

from app.logginglib import init_custom_logger

logger = logging.getLogger(__name__)
init_custom_logger(logger)

BUCKET_NAME = "wra"
EXPIRE_IN = datetime.today() + timedelta(3)  # after 3 days


def get_storage_client() -> Client:
    """Get storage client"""

    credentials = service_account.Credentials.from_service_account_file(
        filename="credentials.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return storage.Client(credentials=credentials)


def create_bucket():
    """Create bucket"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(BUCKET_NAME)
    bucket.storage_class = "STANDARD"
    storage_client.create_bucket(bucket, location="europe-west1")


def upload_file(source_filename: str, destination_filename: str):
    """Upload file"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(BUCKET_NAME)
    blob: Blob = bucket.blob(destination_filename)
    # blob.metadata = {"upload_date": date.today().strftime("%Y_%m_%d")}
    blob.upload_from_filename(source_filename, timeout=3600)


def get_blob_url(blob_ame: str, expire_in: str = EXPIRE_IN) -> str:
    """Get blob url"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(BUCKET_NAME)
    url = bucket.blob(blob_ame).generate_signed_url(expiration=expire_in)

    return url


def blob_exists(blob_name: str) -> bool:
    """Check if blob exists"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(BUCKET_NAME)
    blob: Blob = bucket.blob(blob_name)

    return blob.exists()


def clear_bucket():
    """Clear bucket"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(BUCKET_NAME)
    blobs: Iterator[Blob] = bucket.list_blobs()
    for blob in blobs:
        try:
            blob.delete()
        except (Exception,):
            pass


def cleanup(limit_gb: int = 5):
    """Cleanup"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(BUCKET_NAME)
    blobs: Iterator[Blob] = bucket.list_blobs()
    # blobs_len = sum(1 for _ in bucket.list_blobs())

    # Get size of all blobs
    size_bytes = 0
    for blob in blobs:
        size_bytes += blob.size

    # Get size in megabytes
    size_megabytes = size_bytes / 1024 / 1024

    # Clear bucket
    if size_megabytes >= (limit_gb * 1024):
        clear_bucket()
