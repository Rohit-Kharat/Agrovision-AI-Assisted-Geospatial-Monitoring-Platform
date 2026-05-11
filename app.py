from flask import Flask, render_template, send_file, jsonify, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from models import db, User
from auth import auth_bp
import rasterio
from rasterio.warp import transform_bounds
from rasterio.crs import CRS
import os
import glob
from dotenv import load_dotenv
from datetime import timedelta

# ── Load .env variables ────────────────────────────────────────────────────────
load_dotenv()

app = Flask(__name__)

# ── Core configuration ─────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///satellite.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Session persistence configuration ─────────────────────────────────────────
# Makes the session survive even when the browser is closed
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Remember-me cookie configuration
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = False   # Set True when using HTTPS in production

# ── Initialize extensions ──────────────────────────────────────────────────────
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

# ── Register blueprints ────────────────────────────────────────────────────────
app.register_blueprint(auth_bp)

# ── Ensure DB tables exist on startup ─────────────────────────────────────────
with app.app_context():
    db.create_all()

# ── Helper functions ───────────────────────────────────────────────────────────
def get_latest_ndvi_tif():
    """Find the most recent NDVI TIFF file."""
    tif_files = sorted(glob.glob("ndvi_*.tif"), reverse=True)
    return tif_files[0] if tif_files else None

def get_latest_ndvi_png():
    """Find the most recent NDVI PNG file."""
    png_files = sorted(glob.glob("ndvi_*.png"), reverse=True)
    return png_files[0] if png_files else None

ndvi_tif_path = get_latest_ndvi_tif() or "ndvi_20250320_215628.tif"
ndvi_png      = get_latest_ndvi_png() or "ndvi_output.png"
smi_overlay   = "smi_overlay.png"

def ensure_georeferencing():
    """Check if NDVI TIFF has a CRS; assign one if missing."""
    if not os.path.exists(ndvi_tif_path):
        return
    with rasterio.open(ndvi_tif_path, "r+") as src:
        if src.crs is None:
            print("⚠️  NDVI file is missing CRS. Assigning EPSG:4326.")
            src.crs = CRS.from_epsg(4326)

def get_latlon_bounds():
    """Extract latitude/longitude bounds from NDVI TIFF file."""
    try:
        with rasterio.open(ndvi_tif_path) as src:
            if src.crs is None:
                return None
            bounds = src.bounds
            latlon_bounds = transform_bounds(src.crs, "EPSG:4326", *bounds)
            return latlon_bounds  # (min_lon, min_lat, max_lon, max_lat)
    except Exception as e:
        print(f"Error processing NDVI file: {e}")
        return None

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/ndvi")
@login_required
def get_ndvi():
    """Serve the NDVI image."""
    if not os.path.exists(ndvi_png):
        return "❌ Error: NDVI image not found.", 404
    return send_file(ndvi_png, mimetype="image/png")

@app.route("/ndvi_bounds")
@login_required
def ndvi_bounds():
    """Return the NDVI bounding box as JSON."""
    ensure_georeferencing()
    bounds = get_latlon_bounds()
    if bounds:
        return jsonify({"min_lon": bounds[0], "min_lat": bounds[1],
                        "max_lon": bounds[2], "max_lat": bounds[3]})
    return jsonify({"error": "NDVI file is missing georeferencing data."}), 400

@app.route("/smi")
@login_required
def get_smi():
    """Serve the SMI overlay image."""
    if not os.path.exists(smi_overlay):
        return "❌ Error: SMI image not found. Please process SAR data first.", 404
    return send_file(smi_overlay, mimetype="image/png")

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

if __name__ == "__main__":
    app.run(debug=True)
