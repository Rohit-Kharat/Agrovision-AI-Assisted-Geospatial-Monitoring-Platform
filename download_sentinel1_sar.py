import os
import geopandas as gpd
import numpy as np
import rasterio
from datetime import datetime
from sentinelhub import (
    SHConfig, BBox, CRS, MimeType, bbox_to_dimensions,
    SentinelHubRequest, DataCollection
)

# CONFIGURE YOUR SENTINEL HUB ACCESS
config = SHConfig()
config.instance_id = "044330f3-4b65-4bd5-8e5e-3bd361662a03"
config.sh_client_id = "411fec2f-d2a9-48d9-9a6b-3d83f92e553f"
config.sh_client_secret = "cGUTJUBBsNorhitkI7QzQzbEdTuzfl8I"
# PATHS
aoi_path = "aoi.geojson"
vv_path = "sentinel1/S1_VV.tif"
vh_path = "sentinel1/S1_VH.tif"
os.makedirs("sentinel1", exist_ok=True)

# LOAD AOI
aoi = gpd.read_file(aoi_path)
bounds = aoi.total_bounds  # minx, miny, maxx, maxy
bbox = BBox(bbox=tuple(bounds), crs=CRS.WGS84)
resolution = 10
width, height = bbox_to_dimensions(bbox, resolution=resolution)

# DATE RANGE
time_range = ("2024-12-01", "2025-03-01")

# FUNCTION TO DOWNLOAD A POLARIZATION
def download_sar_band(polarization, out_path):
    evalscript = f"""
    function setup() {{
        return {{
            input: ["{polarization}"],
            output: {{
                bands: 1,
                sampleType: "FLOAT32"
            }}
        }};
    }}

    function evaluatePixel(sample) {{
        return [sample.{polarization}];
    }}
    """

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL1_IW,
                time_interval=time_range,
                mosaicking_order='mostRecent'
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=(width, height),
        config=config
    )

    # Get SAR band image in memory
    data = request.get_data()[0]

    # Manually set transform and metadata
    transform = rasterio.transform.from_bounds(*bbox, width=width, height=height)
    crs = "EPSG:4326"

    # Save to GeoTIFF
    with rasterio.open(out_path, "w", driver="GTiff",
                       height=data.shape[0], width=data.shape[1],
                       count=1, dtype=np.float32,
                       crs=crs, transform=transform) as dst:
        dst.write(data, 1)

    print(f"✅ Saved {polarization} to {out_path}")



# Download both bands
download_sar_band("VV", vv_path)
download_sar_band("VH", vh_path)

print("✅ Sentinel-1 VV/VH bands downloaded successfully.")
