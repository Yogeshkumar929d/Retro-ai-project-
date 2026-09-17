import os
import io
import time
import requests
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = Path("outputs")
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

HF_TOKEN = os.environ.get("HF_TOKEN")
# Stable Diffusion model on Hugging Face
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

def generate_huggingface_image(prompt: str) -> Image.Image:
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt}
    
    # Retry logic if model is loading
    for _ in range(5):
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        elif "estimated_time" in response.text:
            time.sleep(10)
        else:
            break
            
    raise Exception(f"HF API Error ({response.status_code}): {response.text}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/outputs/<filename>")
def serve_output(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/convert", methods=["POST"])
def convert():
    if "photo" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    era = request.form.get("era", "1980s")
    custom_prompt = request.form.get("prompt", "")

    # Retro era prompts
    era_styles = {
        "1970s": "vintage 1970s Polaroid photo, warm muted colors, film grain, retro clothing and hairstyle, authentic 70s aesthetics",
        "1980s": "1980s vintage photo, retro synthwave mood, VHS grain, neon warm lighting, authentic 80s aesthetics",
        "1990s": "1990s disposable camera 35mm photograph, flash portrait, grunge retro aesthetics, 90s vibes"
    }

    style = era_styles.get(era, era_styles["1980s"])
    full_prompt = f"Portrait of a person, {style}."
    if custom_prompt:
        full_prompt += f" Details: {custom_prompt}"

    try:
        if HF_TOKEN:
            result_img = generate_huggingface_image(full_prompt)
            output_name = f"retro_{int(time.time())}.jpg"
            output_path = app.config["UPLOAD_FOLDER"] / output_name
            result_img.save(output_path, format="JPEG")

            return jsonify({
                "imageUrl": f"/outputs/{output_name}",
                "downloadUrl": f"/outputs/{output_name}",
                "prompt": full_prompt
            })
        else:
            return jsonify({"error": "HF_TOKEN not configured"}), 400

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
    
