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
# Lightweight aur fast model: Stable Diffusion v1.5
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

def generate_huggingface_image(prompt: str) -> Image.Image:
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=50)
    
    if response.status_code == 200:
        return Image.open(io.BytesIO(response.content))
    else:
        raise Exception(f"HF Error ({response.status_code}): {response.text[:150]}")

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

    era_styles = {
        "1970s": "vintage 1970s polaroid photo, film grain, retro warm colors, realistic",
        "1980s": "1980s retro portrait, VHS camera look, authentic 80s lighting, vintage photo",
        "1990s": "1990s 35mm flash camera photograph, grunge aesthetic, authentic 90s look"
    }

    style = era_styles.get(era, era_styles["1980s"])
    full_prompt = f"Portrait photo of a person, {style}."
    if custom_prompt:
        full_prompt += f" {custom_prompt}"

    try:
        if not HF_TOKEN:
            return jsonify({"error": "HF_TOKEN not found in Environment Variables"}), 400

        result_img = generate_huggingface_image(full_prompt)
        output_name = f"retro_{int(time.time())}.jpg"
        output_path = app.config["UPLOAD_FOLDER"] / output_name
        result_img.save(output_path, format="JPEG")

        return jsonify({
            "imageUrl": f"/outputs/{output_name}",
            "downloadUrl": f"/outputs/{output_name}",
            "prompt": full_prompt
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
