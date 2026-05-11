import numpy as np
import rasterio
import matplotlib.pyplot as plt
import os
import re

def calculate_smi(vv_path, vh_path, output_path):
    with rasterio.open(vv_path) as vv_src, rasterio.open(vh_path) as vh_src:
        vv = vv_src.read(1).astype(np.float32)
        vh = vh_src.read(1).astype(np.float32)
        bounds = vv_src.bounds

    # NDPI (Normalized Difference Polarization Index)
    ndpi = (vv - vh) / (vv + vh + 1e-6)

    # Normalize as Soil Moisture Index
    smi = (ndpi - np.nanmin(ndpi)) / (np.nanmax(ndpi) - np.nanmin(ndpi))

    # Save as PNG
    plt.imsave(output_path, smi, cmap="Blues")
    print(f"Soil Moisture Index saved to {output_path}")

    # Inject into interactive_map.html
    inject_smi_into_map(output_path, bounds)

def inject_smi_into_map(png_path, bounds, map_path="interactive_map.html"):
    """Inject SMI overlay into the Folium interactive map."""
    print(f"Injecting SMI overlay into {map_path}...")
    
    if not os.path.exists(map_path):
        print(f"Warning: {map_path} not found. Skipping injection.")
        return

    overlay_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
    
    # Convert to relative path for HTML
    png_rel_path = os.path.relpath(png_path).replace("\\", "/")
    
    with open(map_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Create SMI layer injection script
    smi_script = f"""
    <script>
        // Add SMI Layer to Folium map
        var smiimageBounds = {overlay_bounds};
        var smiImage = L.imageOverlay('{png_rel_path}', smiimageBounds, {{opacity: 0.6, interactive: false}});
        
        // Function to add SMI layer
        function addSMILayer() {{
            // Find the Folium map (variable names have random suffixes)
            var map = null;
            for (var key in window) {{
                if (key.startsWith('map_') && window[key] && typeof window[key].addLayer === 'function') {{
                    map = window[key];
                    break;
                }}
            }}
            
            if (map) {{
                // Add SMI layer directly to the map
                smiImage.addTo(map);
                console.log('SMI layer added to map');
            }} else {{
                console.log('Map not found');
            }}
        }}
        
        // Wait for page to load
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', addSMILayer);
        }} else {{
            addSMILayer();
        }}
    </script>
    """

    # Check if SMI layer already exists (avoid duplicates)
    if "SMI Layer" in content or "smiimageBounds" in content:
        print("Warning: SMI layer already injected. Removing old injection to update...")
        # Remove old SMI script
        content = re.sub(r'<script>[\s\S]*?SMI Layer[\s\S]*?</script>', '', content, flags=re.DOTALL)

    # Inject before closing body tag
    if "</body>" in content:
        new_content = content.replace("</body>", smi_script + "\n</body>")
        with open(map_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"SMI Layer successfully injected into {map_path}")
    else:
        print("Warning: Could not find </body> tag in HTML.")

# 🔽 This block runs when you execute the file directly
if __name__ == "__main__":
    vv_path = "sentinel1/S1_VV.tif"
    vh_path = "sentinel1/S1_VH.tif"
    output_path = "smi_overlay.png"

    # Ensure output folder exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    calculate_smi(vv_path, vh_path, output_path)
