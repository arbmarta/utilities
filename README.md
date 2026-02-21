## citations/
**merge-ris.py**: Merges multiple .ris files into a combined file for use in Covidence.


## meta_wri_chm/
**v1_gee_exporter.js**: This code provides an export for the Tolan et al. (2024) canopy height model dataset for use in Google Earth Engine. It is a simple addition to their own code (https://gee-community-catalog.org/projects/meta_trees/). Limit the export area using an area drawn in Google Earth Engine and labeled "geometry"

**v2_boto3_explorer.py**: This code helps you explore the forests/v1 directory that houses the version 1 canopy height model dataset from Meta and WRI (Tolan et al., 2024).

**v2_boto3_explorer.py**: This code helps you explore the forests/v2 directory that houses the version 2 canopy height model dataset from Meta and WRI (Tolan et al., 2024).

## heat_mapping/

**identify_script.py**: This script searches the USGS EarthExplorer API for Landsat Collection 2 Level 2 scenes based on user-defined location, date range, and cloud cover, then automatically downloads and extracts the most recent scene for further Land Surface Temperature (LST) processing.

**process_script.py**: This script converts the downloaded Landsat 8–9 ST_B10 thermal band GeoTIFF into Land Surface Temperature (°C) using the official scaling factor and offset, saves the result as a new LST GeoTIFF, and displays it as a map.

**output_script.py**: This script clips the derived LST raster to a user-defined latitude/longitude bounding box, saves the clipped GeoTIFF, and visualizes it using both standard and custom temperature-based color classifications.
