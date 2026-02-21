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
print_tree("forests/v1/")

print("\n=== Downloading the CHM index (tiles.geojson) ===\n")
# Download tiles.geojson
subprocess.run(
    [
        "aws", "s3", "cp", "--no-sign-request",
        "s3://dataforgood-fb-data/forests/v1/alsgedi_global_v6_float/tiles.geojson",
        "tiles_v1.geojson",
    ]
)
