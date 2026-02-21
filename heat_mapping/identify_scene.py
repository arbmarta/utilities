# Automated EarthExplorer Landsat Scene to Land Surface Temperature (LST)

## User must input:
# USGS Credentials
# Scene Variables (Replace Placeholders)

# Part 1: Searching for Scenes
import os, tarfile
import pandas as pd
from landsatxplore.api import API
from landsatxplore.earthexplorer import EarthExplorer
from IPython.display import display

# Helper function to search for Landsat scenes
def search_landsat_scenes(username, password, dataset, latitude, longitude, start_date, end_date, max_cloud_cover):
    """
    Search for Landsat scenes using EarthExplorer API.
    """
    api = API(username, password)
    try:
        scenes = api.search(
            dataset=dataset,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=max_cloud_cover
        )
        return scenes
    except Exception as e:
        print(f"Error searching for scenes: {e}")
        return []
    finally:
        api.logout()

# Your USGS credentials
username = "USERNAME" # Fill in USGS credential
password = "PASSWORD" # Fill in USGS credential

# Input parameters
dataset = 'landsat_ot_c2_l2'  # Landsat Collection 2 Level 2 dataset
latitude = LATITUDE
longitude = LONGITUDE
start_date = 'yyyy-mm-dd'
end_date = 'yyyy-mm-dd'
max_cloud_cover = 5  # Maximum cloud cover percentage

if not username or not password:
    print("USGS credentials not provided.")
else:
    # Search for scenes
    scenes = search_landsat_scenes(username, password, dataset, latitude, longitude, start_date, end_date, max_cloud_cover)

    if scenes:
        # Convert scenes to a DataFrame for better visualization
        df_scenes = pd.DataFrame(scenes)
        df_scenes = df_scenes[['display_id', 'wrs_path', 'wrs_row', 'satellite', 'cloud_cover', 'acquisition_date']]
        df_scenes.sort_values('acquisition_date', ascending=False, inplace=True)

        # Display the DataFrame as an interactive table
        display(df_scenes)
    else:
        print("No scenes found.")

# Part 2: Downloading & Extracting Most Recent Scene
if scenes:
    ee = EarthExplorer(username, password)
    ID = df_scenes.iloc[0]['display_id'] if not df_scenes.empty else None

    output_dir = './LandsatDownloader'  # Set to a suitable path
    os.makedirs(output_dir, exist_ok=True)

    if ID:
        try:
            print(f"Downloading scene: {ID}")
            ee.download(ID, output_dir=output_dir)
            print(f"{ID} successfully downloaded.")
        except Exception as e:
            print(f"Error downloading {ID}: {e}")
        finally:
            ee.logout()

        # Extract the downloaded tar file
        archive_path = os.path.join(output_dir, f'{ID}.tar')
        extraction_path = os.path.join(output_dir, ID)

        try:
            with tarfile.open(archive_path) as tar:
                tar.extractall(extraction_path)
                print(f"Files extracted successfully for {ID}.")
        except Exception as e:
            print(f"Error extracting files for {ID}: {e}")
    else:
        print("No scenes available for download.")
