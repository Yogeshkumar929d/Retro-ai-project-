import os
import uuid
import base64
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageEnhance, ImageFilter
import requests

app = Flask(__name__)

UPLOAD_FOLDER = Path("outputs")
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

HF_TOKEN = os.environ.get("HF_TOKEN")
# Free fast text-to-image / diffusion model on Hugging Face
HF_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

def apply_local_retro_filter(image: Image.Image, era: str) -> Image.Image:
    img = image.convert("RGB")
    r, g, b = img.split()
    if era == "1970s":
        r = r.point(lambda i: min(255, int(i * 1.15)))
        b = b.point(lambda i: int(i * 0.85))
    elif era == "1990s":
        b = b.point(lambda i: min(255, int(i * 1.15)))
    else:  # 1980s
        r = r.point(lambda i: min(255, int(i * 1.20)))
        g = g.point(lambda i: int(i * 1.05))
        b = b.point(lambda i: int(i * 0.90))
    img = Image.merge("RGB", (r, g, b))
    img = ImageEnhance.Color(img).enhance(1.3)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    return img

def generate_with_huggingface(prompt: str):
    if not HF_TOKEN:
        return None
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {"num_inference_steps": 4}
    }
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=40)
        if response.status_code == 200:
            return Image.open(requests.compat.BytesIO(response.content))
    except Exception as e:
        print(f"HF Error: {e}")
    return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/outputs/<filename>")
def serve_output(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

def process_image():
    file = request.files.get("image") or request.files.get("photo")
    if not file or file.filename == "":
        return jsonify({"error": "No image uploaded"}), 400

    era = request.form.get("era", "1980s")
    custom_prompt = request.form.get("prompt", "")

    # 1985 Retro Styling Prompt
    base_prompt = (
        f"A real vintage authentic {era} photograph, 1985 fashion style, retro clothing, "
        f"voluminous retro hairstyle, analog film grain, polaroid warm color palette, direct camera flash."
    )
    if custom_prompt:
        full_prompt = f"{base_prompt}, {custom_prompt}"
    else:
        full_prompt = base_prompt

    output_name = f"retro_{era.lower()}_{uuid.uuid4().hex[:8]}.jpg"
    output_path = app.config["UPLOAD_FOLDER"] / output_name

    # Try Hugging Face Free AI generation first
    generated_img = generate_with_huggingface(full_prompt)

    if generated_img:
        generated_img.save(output_path, format="JPEG", quality=92)
        status_note = f"Generated using Hugging Face AI ({era} vintage style)."
    else:
        # Fallback to local filter if API is loading or token missing
        raw_img = Image.open(file.stream)
        converted = apply_local_retro_filter(raw_img, era)
        converted.save(output_path, format="JPEG", quality=90)
        status_note = f"Applied {era} retro analog filter."

    return jsonify({
        "imageUrl": f"/outputs/{output_name}",
        "downloadUrl": f"/outputs/{output_name}",
        "prompt": f"{full_prompt} ({status_note})"
    })

@app.route("/api/convert", methods=["POST"])
def api_convert():
    return process_image()

@app.route("/convert", methods=["POST"])
def normal_convert():
    return process_image()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
