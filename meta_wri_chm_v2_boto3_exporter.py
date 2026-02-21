import boto3
import subprocess
from botocore import UNSIGNED
from botocore.config import Config

s3 = boto3.client(
    "s3",
    config=Config(signature_version=UNSIGNED)
)

bucket_name = "dataforgood-fb-data"


def print_tree(prefix, indent=""):
    response = s3.list_objects_v2(
        Bucket=bucket_name,
        Prefix=prefix,
        Delimiter="/"
    )

    if "CommonPrefixes" in response:
        for folder in response["CommonPrefixes"]:
            folder_name = folder["Prefix"]
            print(f"{indent}{folder_name}")
            print_tree(folder_name, indent + "    ")


print("\n=== Printing S3 Directory Structure (Folders Only) ===\n")
print_tree("forests/v2/")

s3 = boto3.client(
    "s3",
    config=Config(signature_version=UNSIGNED)
)

bucket_name = "dataforgood-fb-data"
prefix = "forests/v2/global/dinov3_global_chm_v2_ml3/chm/"

response = s3.list_objects_v2(
    Bucket=bucket_name,
    Prefix=prefix,
    MaxKeys=100
)

print(f"\n=== First 100 files in {prefix} ===\n")

for i, obj in enumerate(response.get("Contents", []), 1):
    print(f"{i:3d}. {obj['Key']}  ({obj['Size']} bytes)")

print(f"\n=== Listed {i} files ===\n")

bucket_name = "dataforgood-fb-data"
prefix = "forests/v2/global/dinov3_global_chm_v2_ml3/"

paginator = s3.get_paginator("list_objects_v2")

print(f"\n=== Searching for .geojson files in {prefix} ===\n")

found = []
for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
    for obj in page.get("Contents", []):
        if obj["Key"].lower().endswith(".geojson"):
            found.append(obj["Key"])
            print(f"Found: {obj['Key']}  (Size: {obj['Size']} bytes)")

if not found:
    print("No .geojson files found.")
else:
    print(f"\nTotal found: {len(found)}")

print("\n=== Finished searching ===\n")
