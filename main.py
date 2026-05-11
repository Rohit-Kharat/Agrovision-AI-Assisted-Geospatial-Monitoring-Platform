# from flask import Flask, render_template, send_file
# import os

# app = Flask(__name__)

# # Set correct path for NDVI file
# ndvi_png = os.path.join(os.getcwd(), "ndvi_output.png")

# @app.route("/ndvi")
# def get_ndvi():
#     if not os.path.exists(ndvi_png):
#         return "❌ Error: NDVI image not found. Please process the NDVI first.", 404
#     return send_file(ndvi_png, mimetype="image/png")

# @app.route("/")
# def index():
#     return render_template("index.html")

# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, render_template, send_file, jsonify
import rasterio
from rasterio.warp import transform_bounds
from rasterio.crs import CRS
import os
import glob

app = Flask(__name__)

def get_latest_ndvi_tif():
    """Find the most recent NDVI TIFF file."""
    tif_files = sorted(glob.glob("ndvi_*.tif"), reverse=True)
    return tif_files[0] if tif_files else None

def get_latest_ndvi_png():
    """Find the most recent NDVI PNG file."""
    png_files = sorted(glob.glob("ndvi_*.png"), reverse=True)
    return png_files[0] if png_files else None

ndvi_tif_path = get_latest_ndvi_tif() or "ndvi_20250320_215628.tif"  # Fallback
ndvi_png = get_latest_ndvi_png() or "ndvi_output.png"  # Fallback
smi_overlay = "smi_overlay.png"

def ensure_georeferencing():
    """Check if NDVI TIFF has a CRS; assign one if missing."""
    with rasterio.open(ndvi_tif_path, "r+") as src:
        if src.crs is None:
            print("⚠️ NDVI file is missing CRS. Assigning EPSG:4326.")
            src.crs = CRS.from_epsg(4326)  # Assign WGS 84 (lat/lon)

def get_latlon_bounds():
    """Extract latitude/longitude bounds from NDVI TIFF file."""
    try:
        with rasterio.open(ndvi_tif_path) as src:
            if src.crs is None:
                return None  # No CRS found, image is not georeferenced

            bounds = src.bounds  # (left, bottom, right, top)
            src_crs = src.crs  # Source CRS

            # Convert to lat/lon (EPSG:4326)
            latlon_bounds = transform_bounds(src_crs, "EPSG:4326", *bounds)
            return latlon_bounds  # (min_lon, min_lat, max_lon, max_lat)
    except Exception as e:
        print(f"Error processing NDVI file: {e}")
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ndvi")
def get_ndvi():
    """Serve the NDVI image."""
    if not os.path.exists(ndvi_png):
        return "❌ Error: NDVI image not found.", 404
    return send_file(ndvi_png, mimetype="image/png")

@app.route("/ndvi_bounds")
def ndvi_bounds():
    """Return the NDVI bounding box as JSON."""
    ensure_georeferencing()  # Ensure CRS is set
    bounds = get_latlon_bounds()
    if bounds:
        return jsonify({"min_lon": bounds[0], "min_lat": bounds[1], "max_lon": bounds[2], "max_lat": bounds[3]})
    return jsonify({"error": "NDVI file is missing georeferencing data."}), 400

@app.route("/smi")
def get_smi():
    """Serve the SMI overlay image."""
    if not os.path.exists(smi_overlay):
        return "❌ Error: SMI image not found. Please process SAR data first.", 404
    return send_file(smi_overlay, mimetype="image/png")

@app.route("/smi_bounds")
def smi_bounds():
    """Return the SMI bounding box as JSON."""
    try:
        import rasterio
        vv_path = "sentinel1/S1_VV.tif"
        if os.path.exists(vv_path):
            with rasterio.open(vv_path) as src:
                bounds = src.bounds
                latlon_bounds = transform_bounds(src.crs if src.crs else CRS.from_epsg(4326), "EPSG:4326", *bounds)
                return jsonify({"min_lon": latlon_bounds[0], "min_lat": latlon_bounds[1], "max_lon": latlon_bounds[2], "max_lat": latlon_bounds[3]})
        return jsonify({"error": "SAR data not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
