import os
import subprocess

URL = "s3://dataforgood-fb-data/forests/v2/global/dinov3_global_chm_v2_ml3/tiles.geojson"
DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiles.geojson")

subprocess.run(["aws", "s3", "cp", URL, DEST, "--no-sign-request"], check=True)