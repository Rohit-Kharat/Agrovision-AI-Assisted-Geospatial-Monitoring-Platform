
import os
import time
import shutil
import glob

def move_aoi_from_downloads(filename="aoi.geojson", wait_for_file=True, timeout=300000):
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    project_directory = os.getcwd()
    new_aoi_path = os.path.join(project_directory, filename)

    if os.path.exists(new_aoi_path):
        print(f"AOI already exists in project: {new_aoi_path}")
        return new_aoi_path

    # Search for aoi.geojson or variants like aoi (1).geojson
    search_pattern = os.path.join(downloads_folder, "aoi*.geojson")
    
    def get_latest_download():
        files = glob.glob(search_pattern)
        if not files:
            return None
        return max(files, key=os.path.getmtime)

    if wait_for_file:
        print("Waiting for AOI file to appear in Downloads folder...")
        start_time = time.time()
        found_path = get_latest_download()
        while not found_path:
            time.sleep(1)
            found_path = get_latest_download()
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout: No 'aoi*.geojson' found in Downloads within {timeout} seconds.")
    else:
        found_path = get_latest_download()

    if found_path and os.path.exists(found_path):
        shutil.move(found_path, new_aoi_path)
        print(f"Moved '{os.path.basename(found_path)}' from Downloads to {new_aoi_path}")
    else:
        raise FileNotFoundError(f"'{filename}' not found in Downloads or project directory.")

    return new_aoi_path
