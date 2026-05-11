import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
import glob
import os
import json

def generate_training_data(samples=300):
    np.random.seed(42)
    ndvi = np.random.rand(samples)
    soil_moisture = np.random.rand(samples)
    rainfall = np.random.rand(samples) * 100  # mm

    labels = []
    for i in range(samples):
        if ndvi[i] < 0.2 or soil_moisture[i] < 0.2:
            labels.append("Bad")
        elif 0.2 <= ndvi[i] < 0.5:
            labels.append("Moderate")
        else:
            labels.append("Good")
    
    df = pd.DataFrame({
        'ndvi': ndvi,
        'soil_moisture': soil_moisture,
        'rainfall': rainfall,
        'health': labels
    })
    return df

def train_model():
    df = generate_training_data()
    X = df[['ndvi', 'soil_moisture', 'rainfall']]
    y = df['health']
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def get_suggestions(label):
    if label == "Bad":
        return [
            "Increase irrigation immediately.",
            "Apply NPK fertilizer after soil testing.",
            "Check for pests or diseases."
        ]
    elif label == "Moderate":
        return [
            "Slightly increase watering.",
            "Apply foliar nutrient spray.",
            "Monitor environmental stress closely."
        ]
    elif label == "Good":
        return [
            "Maintain current practices.",
            "Apply precision fertilizer.",
            "Plan harvest based on NDVI trends."
        ]

def load_ndvi_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not load image at {image_path}")
    ndvi = img / 255.0  
    return ndvi

def analyze_zones(ndvi_array, model, zone_size=20):
    h, w = ndvi_array.shape
    results = []

    for y in range(0, h, zone_size):
        for x in range(0, w, zone_size):
            zone = ndvi_array[y:y+zone_size, x:x+zone_size]
            avg_ndvi = np.mean(zone)
            soil_moisture = np.random.uniform(0.3, 0.7) 
            rainfall = np.random.uniform(20, 100)       

            features = pd.DataFrame([{
                'ndvi': avg_ndvi,
                'soil_moisture': soil_moisture,
                'rainfall': rainfall
            }])

            prediction = model.predict(features)[0]
            suggestions = get_suggestions(prediction)

            results.append({
                'zone': f'({x},{y})',
                'avg_ndvi': round(float(avg_ndvi), 3),
                'soil_moisture': round(float(soil_moisture), 2),
                'rainfall': round(float(rainfall), 1),
                'health': prediction,
                'suggestions': suggestions
            })

    return results

def run_pipeline(image_path):
    print("Loading image and training model...")
    model = train_model()
    ndvi = load_ndvi_image(image_path)
    results = analyze_zones(ndvi, model)

    # Save visual plot
    plt.figure(figsize=(6, 4))
    plt.imshow(ndvi, cmap='YlGn')
    plt.title("NDVI Model Visualization")
    plt.colorbar(label="NDVI")
    plt.tight_layout()
    plt.savefig("latest_ndvi_model_plot.png")
    plt.close()
    print("Visualization saved to latest_ndvi_model_plot.png")

    # Save results to JSON for the web dashboard
    with open("health_results.json", "w") as f:
        json.dump(results, f)
    print("Health results saved to health_results.json")

    print("\nCrop Health Prediction complete.")


if __name__ == "__main__":
    tif_files = sorted(glob.glob("ndvi_*.tif"), reverse=True)
    if not tif_files:
        print("No NDVI .tif files found.")
        exit()

    latest_tif = tif_files[0]
    latest_png = os.path.splitext(latest_tif)[0] + ".png"
    if not os.path.exists(latest_png):
        print(f"Warning: PNG not found for {latest_tif}. Running imageonmap.py logic...")
        # Fallback: check if ndvi_output.png exists
        if os.path.exists("ndvi_output.png"):
            latest_png = "ndvi_output.png"
        else:
            print("No PNG found. Please run imageonmap.py first.")
            exit()
    
    run_pipeline(latest_png)
