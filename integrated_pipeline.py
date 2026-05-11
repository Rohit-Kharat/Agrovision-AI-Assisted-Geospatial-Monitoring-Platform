# integrated_pipeline.py

import os
import subprocess
import sys

AOI_PATH = "aoi.geojson"

# --- helpers ---

def _run(script_name):
    """Run a Python script in the same directory as this file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(
        [sys.executable, script_name],
        cwd=base_dir
    )
    if result.returncode != 0:
        raise RuntimeError(f"{script_name} exited with code {result.returncode}")


def update_status(status):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    status_path = os.path.join(base_dir, "status.js")
    with open(status_path, "w") as f:
        f.write(f'window.satelliteProcessingStatus = "{status}";')


# --- pipeline steps ---

def run_generate_map(interactive=True):
    """
    Generate interactive_map.html.
    In interactive mode (CLI) also opens the browser and waits for the user
    to draw & download aoi.geojson.
    In non-interactive mode (web-triggered) the browser is NOT opened and
    we simply check that aoi.geojson already exists.
    """
    print("Step 1: Generating map HTML...")
    _run("generate_map.py")

    aoi_exists = os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), AOI_PATH))

    if interactive:
        import webbrowser
        webbrowser.open("interactive_map.html")
        print("Waiting for 'aoi.geojson' to be created in Downloads...")
        try:
            from moveaoi import move_aoi_from_downloads
            move_aoi_from_downloads()
            print("AOI file moved and ready.")
        except Exception as e:
            print(f"Error handling AOI: {e}")
            sys.exit(1)
    else:
        if not aoi_exists:
            print("aoi.geojson not found in project directory. Checking Downloads...")
            try:
                from moveaoi import move_aoi_from_downloads
                move_aoi_from_downloads(wait_for_file=False) # Don't wait, just check
                print("Found and moved AOI file from Downloads.")
            except Exception:
                raise FileNotFoundError(
                    " 'aoi.geojson' not found in the project directory or Downloads.\n"
                    "   Please draw your AOI on the interactive map and download it first,\n"
                    "   then click 'Run Pipeline' again."
                )
        else:
            print("AOI file already present - skipping map-selector step.")


def run_process_satellite_data():
    print("Step 2: Running satellite data processing for NDVI...")
    _run("process_satellite_data.py")
    print("NDVI .tif file generated.")


def run_imageonmap():
    print("Step 3: Converting NDVI .tif to PNG...")
    _run("imageonmap.py")
    print("NDVI image (PNG) created.")


def run_ndvi_health_predictor():
    print("Step 4: Running NDVI health predictor...")
    _run("ndvi_health_predictor.py")
    print("Health prediction complete.")


def run_download_sentinel1_sar():
    print("Step 5: Downloading Sentinel-1 SAR data...")
    _run("download_sentinel1_sar.py")
    print("S1_VH.tif and S1_VV.tif created.")


def run_smi_processor():
    print("Step 6: Processing SMI from Sentinel-1 data...")
    _run("smi_processor.py")
    print("SMI overlay PNG created.")


# --- entry points ---

def run_pipeline_web():
    """
    Called by app.py (via subprocess) - non-interactive, no browser opening,
    assumes aoi.geojson is already present.
    """
    print("\n=== Integrated Satellite Workflow Starting (web mode) ===\n")
    update_status("processing")

    run_generate_map(interactive=False)
    run_process_satellite_data()
    run_imageonmap()
    run_ndvi_health_predictor()
    run_download_sentinel1_sar()
    run_smi_processor()

    update_status("complete")
    print("\nWorkflow complete. All outputs generated.\n")
    print("Process finished.")


if __name__ == "__main__":
    # --web flag: non-interactive mode (used by app.py)
    # no flag:    interactive CLI mode (user runs manually)
    if "--web" in sys.argv:
        run_pipeline_web()
    else:
        print("\n=== Integrated Satellite Workflow Starting (CLI mode) ===\n")
        update_status("processing")

        run_generate_map(interactive=True)
        run_process_satellite_data()
        run_imageonmap()
        run_ndvi_health_predictor()
        run_download_sentinel1_sar()
        run_smi_processor()

        update_status("complete")
        print("\nWorkflow complete. All outputs generated.\n")
        print("Dashboard updated in-place (if open).")
        print("Process finished.")
