import os
import geopandas as gpd
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, bbox_to_dimensions, BBox, MimeType
from moveaoi import move_aoi_from_downloads  # ✅ Import the AOI move function

# 1️⃣ Configure Sentinel Hub API
config = SHConfig()
config.instance_id = "d4635618-2ded-4bb0-9e0c-558f64872075"
config.sh_client_id = "9fe82092-6dc3-4ba2-86e6-9b1c6385f68f"
config.sh_client_secret = "6gnjIgvnVCPgzbw7c97fNk4mhzMyXKcC"

if not config.instance_id or not config.sh_client_id or not config.sh_client_secret:
    print("❌ Error: Sentinel Hub credentials are missing! Set them correctly.")
    exit()
print("✅ Sentinel Hub API is configured successfully!")

# 2️⃣ Move AOI from Downloads to Project Folder (if needed)
try:
    new_aoi_path = move_aoi_from_downloads()
except Exception as e:
    print(str(e))
    exit()

# 3️⃣ Load AOI
try:
    aoi = gpd.read_file(new_aoi_path)
    print("✅ AOI loaded successfully!")
except Exception as e:
    print(f"❌ Error loading AOI: {e}")
    exit()

if aoi.empty:
    print("❌ Error: AOI file is empty! Please ensure you've drawn and saved a polygon.")
    exit()

if not any(aoi.geometry.geom_type.isin(["Polygon", "MultiPolygon"])):
    print("❌ Error: AOI is not a valid polygon! Please draw a polygon instead of points.")
    exit()

# 4️⃣ Extract Bounding Box
bounds = aoi.total_bounds
if len(bounds) != 4:
    print("❌ Error: AOI bounds are not in the correct format!")
    exit()

bbox = BBox(bbox=(bounds[0], bounds[1], bounds[2], bounds[3]), crs="EPSG:4326")
print(f"✅ Bounding Box Set: {bbox}")

# 5️⃣ NDVI Calculation Setup
max_size = 2500
width, height = bbox_to_dimensions(bbox, resolution=10)
width = min(width, max_size)
height = min(height, max_size)

request = SentinelHubRequest(
    evalscript="""
    function setup() {
        return {
            input: ["B04", "B08"],
            output: { bands: 1, sampleType: "FLOAT32" }
        };
    }
    function evaluatePixel(sample) {
        return [(sample.B08 - sample.B04) / (sample.B08 + sample.B04)];
    }
    """,
    input_data=[
        SentinelHubRequest.input_data(DataCollection.SENTINEL2_L2A, time_interval=("2024-01-01", "2024-03-01"))
    ],
    bbox=bbox,
    size=(width, height),
    responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
    config=config
)

# 6️⃣ Fetch & Plot NDVI
try:
    image = request.get_data()[0]
    if image is None:
        print("❌ Error: No NDVI data returned! Check your AOI or API limits.")
        exit()
    plt.imshow(image, cmap="RdYlGn")
    plt.colorbar(label="NDVI")
    plt.title("NDVI from Sentinel-2")
    plt.show()
except Exception as e:
    print(f"❌ Error fetching NDVI data: {e}")
    exit()

# 7️⃣ Save NDVI as GeoTIFF
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
ndvi_filename = f"ndvi_{timestamp}.tif"

# Define transform and CRS for georeferencing
from rasterio.transform import from_bounds
transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], image.shape[1], image.shape[0])

with rasterio.open(ndvi_filename, "w", driver="GTiff",
                   height=image.shape[0], width=image.shape[1],
                   count=1, dtype=np.float32,
                   crs="EPSG:4326", transform=transform) as dst:
    dst.write(image, 1)

print(f"✅ NDVI saved as {ndvi_filename} (Georeferenced)")

