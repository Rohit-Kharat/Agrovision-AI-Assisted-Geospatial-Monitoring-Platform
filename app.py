from flask import Flask, render_template, send_file, jsonify, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from models import db, User
from auth import auth_bp
import rasterio
from rasterio.warp import transform_bounds
from rasterio.crs import CRS
import os
import glob
import subprocess
import threading
import sys
import json
from dotenv import load_dotenv
from datetime import timedelta

# -- Load .env variables ---
load_dotenv()

app = Flask(__name__)

# -- Core configuration ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///satellite.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# -- Session persistence configuration ---
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Remember-me cookie configuration
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = False   # Set True when using HTTPS in production

# -- Initialize extensions ---
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    """Reload the user object from the DB using the ID stored in the session."""
    return User.query.get(int(user_id))

# -- Register blueprints ---
app.register_blueprint(auth_bp)

# -- Ensure DB tables exist on startup ---
with app.app_context():
    db.create_all()

# -- Helper functions ---
def get_latest_ndvi_tif():
    """Find the most recent NDVI TIFF file."""
    tif_files = sorted(glob.glob("ndvi_*.tif"), reverse=True)
    return tif_files[0] if tif_files else None

def get_latest_ndvi_png():
    """Find the most recent NDVI PNG file."""
    png_files = sorted(glob.glob("ndvi_*.png"), reverse=True)
    return png_files[0] if png_files else None

def ensure_georeferencing(tif_path):
    """Check if NDVI TIFF has a CRS; assign one if missing."""
    if not tif_path or not os.path.exists(tif_path):
        return
    try:
        with rasterio.open(tif_path, "r+") as src:
            if src.crs is None:
                src.crs = CRS.from_epsg(4326)
    except Exception:
        pass

def get_latlon_bounds(tif_path):
    """Extract latitude/longitude bounds from NDVI TIFF file."""
    if not tif_path or not os.path.exists(tif_path):
        return None
    try:
        with rasterio.open(tif_path) as src:
            if src.crs is None:
                return None
            bounds = src.bounds
            latlon_bounds = transform_bounds(src.crs, "EPSG:4326", *bounds)
            return latlon_bounds  # (min_lon, min_lat, max_lon, max_lat)
    except Exception as e:
        return None

# -- Routes ---
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/ndvi")
@login_required
def get_ndvi():
    """Serve the latest NDVI image."""
    path = get_latest_ndvi_png()
    if not path or not os.path.exists(path):
        return "Error: NDVI image not found.", 404
    return send_file(path, mimetype="image/png")

@app.route("/ndvi_bounds")
@login_required
def ndvi_bounds():
    """Return the latest NDVI bounding box as JSON."""
    tif_path = get_latest_ndvi_tif()
    if not tif_path:
        return jsonify({"error": "No NDVI files found."}), 404
        
    ensure_georeferencing(tif_path)
    bounds = get_latlon_bounds(tif_path)
    if bounds:
        return jsonify({"min_lon": bounds[0], "min_lat": bounds[1],
                        "max_lon": bounds[2], "max_lat": bounds[3]})
    return jsonify({"error": "NDVI file is missing georeferencing data."}), 400

@app.route("/health_data")
@login_required
def health_data():
    """Serve the latest crop health JSON data."""
    if os.path.exists("health_results.json"):
        with open("health_results.json", "r") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "No health data available"}), 404

@app.route("/health_plot")
@login_required
def health_plot():
    """Serve the latest crop health visualization plot."""
    path = "latest_ndvi_model_plot.png"
    if os.path.exists(path):
        return send_file(path, mimetype="image/png")
    return "Error: Plot not found.", 404

@app.route("/smi")
@login_required
def get_smi():
    """Serve the SMI overlay image."""
    path = "smi_overlay.png"
    if not os.path.exists(path):
        return "Error: SMI image not found.", 404
    return send_file(path, mimetype="image/png")

@app.route("/smi_bounds")
@login_required
def smi_bounds():
    """Return the SMI bounding box as JSON."""
    try:
        vv_path = "sentinel1/S1_VV.tif"
        if os.path.exists(vv_path):
            with rasterio.open(vv_path) as src:
                bounds = src.bounds
                latlon_bounds = transform_bounds(
                    src.crs if src.crs else CRS.from_epsg(4326),
                    "EPSG:4326", *bounds
                )
                return jsonify({"min_lon": latlon_bounds[0], "min_lat": latlon_bounds[1],
                                "max_lon": latlon_bounds[2], "max_lat": latlon_bounds[3]})
        return jsonify({"error": "SAR data not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# -- Pipeline state ---
_pipeline_state = {"status": "idle", "message": ""}

def _run_pipeline_bg():
    """Run integrated_pipeline.py in a background thread."""
    global _pipeline_state
    _pipeline_state = {"status": "running", "message": "Pipeline started..."}
    try:
        result = subprocess.run(
            [sys.executable, "integrated_pipeline.py", "--web"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            encoding='utf-8', errors='replace'
        )
        if result.returncode == 0:
            _pipeline_state = {"status": "complete", "message": "Pipeline finished successfully!"}
        else:
            _pipeline_state = {"status": "error",
                               "message": f"Pipeline failed:\n{result.stderr[-800:] if result.stderr else result.stdout[-800:] or 'unknown error'}"}
    except Exception as e:
        _pipeline_state = {"status": "error", "message": str(e)}

@app.route("/run_pipeline", methods=["POST"])
@login_required
def run_pipeline():
    """Kick off the integrated pipeline in a background thread."""
    global _pipeline_state
    if _pipeline_state["status"] == "running":
        return jsonify({"status": "running", "message": "Pipeline is already running."}), 409
    t = threading.Thread(target=_run_pipeline_bg, daemon=True)
    t.start()
    return jsonify({"status": "running", "message": "Pipeline started!"})

@app.route("/pipeline_status")
@login_required
def pipeline_status():
    """Return the current pipeline status."""
    return jsonify(_pipeline_state)

if __name__ == "__main__":
    app.run(debug=True)
