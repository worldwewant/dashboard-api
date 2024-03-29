"""
MIT License

Copyright (c) 2023 World We Want. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

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

"""

import logging
from datetime import timedelta
from typing import Iterator

from google.cloud.storage import Client, Blob, Bucket
from google.oauth2 import service_account

from app.core.settings import get_settings
from app.logginglib import init_custom_logger

settings = get_settings()
logger = logging.getLogger(__name__)
init_custom_logger(logger)


def get_storage_client() -> Client:
    """Get storage client"""

    credentials = service_account.Credentials.from_service_account_info(
        info=settings.GOOGLE_CREDENTIALS,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return Client(credentials=credentials)


def upload_file(bucket_name: str, source_filename: str, destination_filename: str):
    """Upload file"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(bucket_name)
    blob: Blob = bucket.blob(destination_filename)
    # blob.metadata = {"upload_date": date.today().strftime("%Y_%m_%d")}
    blob.upload_from_filename(source_filename, timeout=3600)


def get_blob_url(bucket_name: str, blob_name: str) -> str:
    """Get blob url"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(bucket_name)
    url = bucket.blob(blob_name).generate_signed_url(expiration=timedelta(hours=1))

    return url


def get_blob(bucket_name: str, blob_name: str) -> Blob:
    """Get blob"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(bucket_name)

    return bucket.blob(blob_name)


def blob_exists(bucket_name: str, blob_name: str) -> bool:
    """Check if blob exists"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(bucket_name)
    blob: Blob = bucket.blob(blob_name)

    return blob.exists()


def clear_bucket(bucket_name: str, skip_blobs: list[str]):
    """
    Clear bucket.

    :param bucket_name: The bucket name.
    :param skip_blobs: A list of blob names to skip from deleting.
    """

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(bucket_name)
    blobs: Iterator[Blob] = bucket.list_blobs()
    for blob in blobs:
        if blob.name in skip_blobs:
            continue
        try:
            blob.delete()
        except (Exception,):
            pass


def cleanup(bucket_name: str, limit_gb: int = 5):
    """Cleanup"""

    storage_client = get_storage_client()
    bucket: Bucket = storage_client.bucket(bucket_name)
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
        clear_bucket(bucket_name=bucket_name, skip_blobs=[])
