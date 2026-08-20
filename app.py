import os
import io
import base64
import time
import numpy as np
from PIL import Image
import cv2
from flask import Flask, render_template, request, jsonify
from ultralytics import YOLO

app = Flask(__name__)

# ==========================================
# MODEL MANAGEMENT (CASCADE)
# ==========================================
loaded_models = {}
prediction_history = []

def get_yolo_model(model_name_or_path):
    """Loads or retrieves the specified YOLO model from cache."""
    global loaded_models
    if model_name_or_path in loaded_models:
        return loaded_models[model_name_or_path], None
    try:
        model = YOLO(model_name_or_path)
        loaded_models[model_name_or_path] = model
        return model, None
    except Exception as e:
        return None, str(e)

# Paths to the cascade models
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))
CASCADE_MODELS = {
    "binary": os.path.join(MODELS_DIR, "binary.pt"),
    "benign": os.path.join(MODELS_DIR, "benign.pt"),
    "malignant": os.path.join(MODELS_DIR, "malignant.pt")
}

# ==========================================
# ROUTES
# ==========================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.json or {}
    image_b64 = data.get("image_b64")
    
    if not image_b64 or "," not in image_b64:
        return jsonify({"status": "error", "message": "No valid image provided."}), 400

    # Verify if models exist
    for key, path in CASCADE_MODELS.items():
        if not os.path.exists(path):
             return jsonify({"status": "error", "message": f"Model {key} not found at {path}."}), 500

    img_rgb = None
    try:
        base64_data = image_b64.split(",")[1]
        img_bytes = base64.b64decode(base64_data)
        pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img_rgb = np.array(pil_img)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error decoding base64 image: {str(e)}"}), 400

    try:
        # CASCADE INFERENCE
        # 1. Load binary model and predict
        model_binary, err = get_yolo_model(CASCADE_MODELS["binary"])
        if err: return jsonify({"status": "error", "message": f"Binary model error: {err}"}), 500
        
        results_binary = model_binary.predict(source=img_rgb, verbose=False)
        result_bin = results_binary[0]
        class_bin = result_bin.names[int(result_bin.probs.top1)]
        conf_bin = float(result_bin.probs.top1conf)
        
        subtype_class = "N/A"
        subtype_conf = 0.0
        subtype_probs = {}

        # 2. Route to the corresponding secondary model
        if class_bin.lower() == "benigno" or class_bin.lower() == "benign":
            model_sub, err = get_yolo_model(CASCADE_MODELS["benign"])
            if err: return jsonify({"status": "error", "message": f"Benign model error: {err}"}), 500
        else:
            model_sub, err = get_yolo_model(CASCADE_MODELS["malignant"])
            if err: return jsonify({"status": "error", "message": f"Malignant model error: {err}"}), 500

        # 3. Predict subtype
        results_sub = model_sub.predict(source=img_rgb, verbose=False)
        result_s = results_sub[0]
        subtype_class = result_s.names[int(result_s.probs.top1)]
        subtype_conf = float(result_s.probs.top1conf)
        subtype_probs = {result_s.names[i]: float(result_s.probs.data[i]) for i in range(len(result_s.probs.data))}

        # Construct hierarchical response
        prediction_item = {
            "id": len(prediction_history) + 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "class": class_bin.upper(),
            "confidence": round(conf_bin * 100, 2),
            "subtype_class": subtype_class.upper(),
            "subtype_confidence": round(subtype_conf * 100, 2),
            "subtype_probs": subtype_probs
        }
        
        prediction_history.insert(0, prediction_item)

        return jsonify({
            "status": "success",
            "prediction": prediction_item
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Inference error: {str(e)}"}), 500

if __name__ == "__main__":
    # Try to load the binary model (stage 1) into memory during boot
    binary_model = CASCADE_MODELS.get("binary")
    if binary_model and os.path.exists(binary_model):
        print(f"Pre-loading binary cascade model: {binary_model}")
        get_yolo_model(binary_model)
    print("Starting Mobile-First Inference Web Server on http://0.0.0.0:5001 ...")
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
