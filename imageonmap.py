import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import folium
from branca.element import Element

tif_files = sorted(glob.glob("ndvi_*.tif"), reverse=True)

if not tif_files:
    raise FileNotFoundError("No NDVI .tif files found in the directory.")

# Use the latest file based on filename
ndvi_tif = tif_files[0]
ndvi_png = os.path.splitext(ndvi_tif)[0] + ".png"  # Same base name for output PNG

# Open NDVI file
with rasterio.open(ndvi_tif) as src:
    ndvi_data = src.read(1).astype(np.float32)
    profile = src.profile
    bounds = src.bounds  # Get bounding box for Folium overlay

# Normalize NDVI for visualization (-1 to 1 mapped to 0-255)
ndvi_normalized = ((ndvi_data - np.nanmin(ndvi_data)) /
                   (np.nanmax(ndvi_data) - np.nanmin(ndvi_data)) * 255).astype(np.uint8)

# Save as PNG in the correct project directory
plt.imsave(ndvi_png, ndvi_normalized, cmap="RdYlGn")
print(f"NDVI Image converted to PNG: {ndvi_png}")

# --- Update Existing Interactive Map with PNG Overlay ---
print("Injecting NDVI overlay into interactive_map.html...")

# Folium expects [[south, west], [north, east]]
overlay_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]

# Create a map centered at AOI
m = folium.Map(
    location=[(bounds.bottom + bounds.top) / 2, (bounds.left + bounds.right) / 2],
    zoom_start=14,
    tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    attr="Google Hybrid"
)

# Automatically zoom to the area
m.fit_bounds(overlay_bounds)

# Add AOI Selection Area for visibility
aoi_path = "aoi.geojson"
if os.path.exists(aoi_path):
    folium.GeoJson(
        aoi_path,
        name="Selection Area",
        style_function=lambda x: {
            "fillColor": "none",
            "color": "red",
            "weight": 2,
        },
    ).add_to(m)

# Re-add Search Bar logic
geocoder_css = Element('<link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />')
geocoder_js = Element('<script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>')
m.get_root().header.add_child(geocoder_css)
m.get_root().header.add_child(geocoder_js)

geocoder_init = Element("""
<script>
    document.addEventListener("DOMContentLoaded", function() {
        var mapEl = document.querySelector('.folium-map');
        var mapId = mapEl.id;
        var checkMap = setInterval(function() {
            if (window[mapId] || window['map_' + mapId]) {
                clearInterval(checkMap);
                var theMap = window[mapId] || window['map_' + mapId];
                L.Control.geocoder({
                    defaultMarkGeocode: false,
                    position: 'topright',
                    placeholder: 'Search city or place...',
                    collapsed: false,
                }).on('markgeocode', function(e) {
                    var bbox = e.geocode.bbox;
                    theMap.fitBounds(bbox);
                    L.marker(e.geocode.center).addTo(theMap).bindPopup(e.geocode.name).openPopup();
                }).addTo(theMap);
            }
        }, 100);
    });
</script>
""")
m.get_root().html.add_child(geocoder_init)

# Add PNG as an overlay so we can see it on map
folium.raster_layers.ImageOverlay(
    image=ndvi_png,
    bounds=overlay_bounds,
    opacity=0.7,
    name="NDVI Layer",
    interactive=True
).add_to(m)

# Add Layer Control
folium.LayerControl().add_to(m)

# Save/Overwrite the original interactive_map.html
map_filename = "interactive_map.html"
m.save(map_filename)

print(f"interactive_map.html updated with NDVI overlay and fit to bounds.")
print(f"Bounding Box: {bounds}")
