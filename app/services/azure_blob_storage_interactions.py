"""
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

"""

"""Azure Blob Storage interactions"""

import os
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
from azure.storage.blob import (
    ContainerClient,
    BlobSasPermissions,
    BlobClient,
    generate_blob_sas,
)

from app.enums.campaign_code import CampaignCode
from app.types import AzureBlobStorageContainerName
from app import env

EXPIRE_IN = datetime.today() + timedelta(3)  # after 3 days


def get_container_client(
    container_name: AzureBlobStorageContainerName,
) -> ContainerClient:
    """Get container client"""

    if container_name == "csv":
        return ContainerClient.from_connection_string(
            conn_str=env.AZURE_STORAGE_CONNECTION_STRING,
            container_name=container_name,
        )
    elif container_name == "main":
        return ContainerClient.from_connection_string(
            conn_str=env.AZURE_STORAGE_CONNECTION_STRING,
            container_name=container_name,
        )


def cleanup(container_name: AzureBlobStorageContainerName, limit_gb: int = 5):
    """Cleanup"""

    # Get container client
    container_client = get_container_client(container_name=container_name)

    # Get size of all files
    size_bytes = 0
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        size_bytes += blob.size

    # Get size in megabytes
    size_megabytes = size_bytes / 1024 / 1024

    # Clear bucket
    if size_megabytes >= (limit_gb * 1024):
        clear_container(container_name=container_name)


def clear_container(container_name: AzureBlobStorageContainerName):
    """Clear container"""

    # Get container client
    container_client = get_container_client(container_name=container_name)

    # Get list
    blob_list = container_client.list_blobs()

    # Delete blobs
    for blob in blob_list:
        container_client.delete_blob(blob.name)


def upload_df_as_csv(
    container_name: AzureBlobStorageContainerName, df: pd.DataFrame, csv_filename: str
):
    """Upload dataframe as CSV"""

    # Save to buffer
    buffer = StringIO()
    df.to_csv(path_or_buf=buffer, index=False, header=True)

    # Get blob client
    blob_client = BlobClient.from_connection_string(
        conn_str=env.AZURE_STORAGE_CONNECTION_STRING,
        container_name=container_name,
        blob_name=csv_filename,
        max_block_size=4 * 1024 * 1024,  # 4mb
        max_single_put_size=16 * 1024 * 1024,  # 16mb
    )

    # Upload
    blob_client.upload_blob(
        data=buffer.getvalue(),
        connection_timeout=10 * 60,  # 10 minutes
    )


def blob_exists(container_name: AzureBlobStorageContainerName, blob_name: str) -> bool:
    """Check if blob exists"""

    # Get blob
    blob = BlobClient.from_connection_string(
        conn_str=env.AZURE_STORAGE_CONNECTION_STRING,
        container_name=container_name,
        blob_name=blob_name,
    )

    return blob.exists()


def get_blob_url(container_name: AzureBlobStorageContainerName, blob_name: str) -> str:
    """Get blob url"""

    sas_blob = generate_blob_sas(
        account_name=env.AZURE_STORAGE_ACCOUNT_NAME,
        container_name=container_name,
        blob_name=blob_name,
        account_key=env.AZURE_STORAGE_ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=EXPIRE_IN,
    )

    return f"https://{env.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{container_name}/{blob_name}?{sas_blob}"


def upload_pmnch_pkl():
    """Upload PMNCH Pickle file"""

    filename = f"{CampaignCode.what_young_people_want.value}.pkl"

    # Get blob client
    blob_client = BlobClient.from_connection_string(
        conn_str=env.AZURE_STORAGE_CONNECTION_STRING,
        container_name="main",
        blob_name=filename,
        max_block_size=4 * 1024 * 1024,  # 4mb
        max_single_put_size=16 * 1024 * 1024,  # 16mb
    )

    # Upload
    with open(file=os.path.join(filename), mode="rb") as data:
        blob_client.upload_blob(
            data=data,
            connection_timeout=10 * 60,  # 10 minutes
        )