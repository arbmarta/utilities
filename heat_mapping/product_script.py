# This script derives LST (*C) from the Landsat 8-9 data you just downloaded.
# User must input specific file path to the ST_B10 file (including the .tif file extension)

import os, rasterio
from rasterio import Affine
from rasterio.enums import Resampling
import numpy as np
import matplotlib.pyplot as plt

# Path to the input GeoTIFF file
input_tif = r"LandsatDownloader/[input TIFF]" specify .tif file

# Check if file exists
if not os.path.exists(input_tif):
    raise FileNotFoundError(f"File not found: {input_tif}")

# Define the output GeoTIFF file path for LST
output_tif = r"LandsatDownloader/LST.tif"

# Open the ST_B10 raster file
with rasterio.open(input_tif) as src:
    # Read the raster data
    band1 = src.read(1)
    profile = src.profile  # Copy profile for writing the output

# Derive Land Surface Temperature (LST)
# Formula: LST = (Raster * Scaling Factor) + Offset - 273.15 (to convert Kelvin to Celsius)
scaling_factor = 0.00341802
offset = 149

lst_array = (band1 * scaling_factor) + offset - 273.15  # LST in Celsius

# Update the profile for the output GeoTIFF
profile.update(dtype=rasterio.float32, count=1, compress='lzw')

# Write the LST to a new GeoTIFF file
with rasterio.open(output_tif, 'w', **profile) as dst:
    dst.write(lst_array.astype(rasterio.float32), 1)

print(f"LST raster saved at: {output_tif}")

# Display the LST raster
plt.figure(figsize=(10, 8))
plt.imshow(lst_array, cmap="viridis", interpolation="none")
plt.colorbar(label="Land Surface Temperature (°C)")
plt.title("Landsat Derived Land Surface Temperature")
plt.axis("off")
plt.show()
