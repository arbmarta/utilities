import os
import rasterio
from rasterio.mask import mask
from shapely.geometry import box, mapping
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Paths
input_tif = r"LandsatDownloader/LST.tif"  # Use the output from the previous script
output_dir = r"LandsatDownloader"
output_clipped_tif = os.path.join(output_dir, "LST_Clipped.tif")

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Step 1: Define the bounding box using lat-long coordinates
# Replace these coordinates with your area of interest (AOI)
max_lat = MAX LATITUDE
max_lon = MAX LONGITUDE
min_lat = MIN LATITUDE
min_lon = MIN LONGITUDE

# Open the raster file
with rasterio.open(input_tif) as src:
    # Ensure the bounding box is transformed to the raster's CRS
    bbox = box(min_lon, min_lat, max_lon, max_lat)  # Shapely box using lon/lat
    bbox = rasterio.warp.transform_geom(
        "EPSG:4326", src.crs, mapping(bbox)  # Transform bbox from WGS84 to raster CRS
    )

    # Step 2: Mask (clip) the raster using the bounding box
    out_image, out_transform = mask(src, [bbox], crop=True)

    # Update the metadata for the output file
    out_meta = src.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform,
        "compress": "lzw"
    })

# Step 3: Save the clipped raster
with rasterio.open(output_clipped_tif, "w", **out_meta) as dest:
    dest.write(out_image)

print(f"Clipped raster saved at: {output_clipped_tif}")


# Step 4: Display the clipped raster with a specified color palette
def display_raster(raster_array, color_palette="viridis"):
    """
    Displays a raster array with a specified color palette.

    Parameters:
        raster_array (numpy.ndarray): The raster data to display.
        color_palette (str): The color palette to use (any valid matplotlib colormap).
    """
    plt.figure(figsize=(10, 8))
    plt.imshow(raster_array, cmap=color_palette, interpolation="none")
    plt.colorbar(label="Land Surface Temperature (°C)")
    plt.title("Clipped Land Surface Temperature")
    plt.axis("off")
    plt.show()


# Load and display the clipped raster
with rasterio.open(output_clipped_tif) as clipped_src:
    clipped_array = clipped_src.read(1)

# Specify your color palette here (e.g., 'viridis', 'plasma', 'cividis', etc.)
chosen_palette = "plasma"  # Replace with your desired colormap
display_raster(clipped_array, color_palette=chosen_palette)


# Step 5: Display the raster with custom color intervals
def display_custom_colormap(raster_array, bounds, colors):
    """
    Displays a raster array with a custom colormap and specified intervals.

    Parameters:
        raster_array (numpy.ndarray): The raster data to display.
        bounds (list): Boundaries for the intervals.
        colors (list): Colors corresponding to each interval.
    """
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    plt.figure(figsize=(10, 8))
    img = plt.imshow(raster_array, cmap=cmap, norm=norm, interpolation="none")
    cbar = plt.colorbar(img, ticks=bounds[:-1])  # Exclude the last boundary for consistent labeling
    cbar.ax.set_yticklabels(
        [f"<{bounds[1]}"] + [f"{bounds[i]}-{bounds[i + 1]}" for i in range(1, len(bounds) - 2)] + [f">{bounds[-2]}"]
    )
    cbar.set_label("Land Surface Temperature (°C)")
    plt.title("Clipped Land Surface Temperature (Custom Intervals)")
    plt.axis("off")
    plt.show()


# Define custom intervals and colors
bounds = [0, 27, 30, 33, 36, 50]
colors = ['white', 'green', 'yellow', 'orange', 'red']  # Adjust as needed

# Display map with custom intervals
display_custom_colormap(clipped_array, bounds, colors)
