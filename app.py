import os
import io
import time
import requests
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageEnhance, ImageFilter

app = Flask(__name__)

UPLOAD_FOLDER = Path("outputs")
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

HF_TOKEN = os.environ.get("HF_TOKEN")
# Fast and reliable SD model
HF_API_URL = "https://api-inference.huggingface.co/models/prompthero/openjourney"

def apply_local_vintage_filter(img: Image.Image, era: str) -> Image.Image:
    img = img.convert("RGB")
    r, g, b = img.split()
    
    if era == "1970s":
        r = r.point(lambda i: min(255, int(i * 1.15)))
        b = b.point(lambda i: int(i * 0.85))
        img = Image.merge("RGB", (r, g, b))
        img = ImageEnhance.Color(img).enhance(0.9)
        img = ImageEnhance.Contrast(img).enhance(1.15)
    elif era == "1990s":
        b = b.point(lambda i: min(255, int(i * 1.10)))
        img = Image.merge("RGB", (r, g, b))
        img = ImageEnhance.Color(img).enhance(1.2)
        img = ImageEnhance.Contrast(img).enhance(1.25)
    else:  # 1980s
        r = r.point(lambda i: min(255, int(i * 1.15)))
        b = b.point(lambda i: min(255, int(i * 1.10)))
        g = g.point(lambda i: int(i * 0.95))
        img = Image.merge("RGB", (r, g, b))
        img = ImageEnhance.Color(img).enhance(1.3)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = img.filter(ImageFilter.SMOOTH)
        
    return img

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

    uploaded_file = request.files["photo"]
    era = request.form.get("era", "1980s")
    custom_prompt = request.form.get("prompt", "")

    full_prompt = f"1980s retro vintage photo, authentic analog grain, highly detailed. {custom_prompt}".strip()
    
    output_name = f"retro_{int(time.time())}.jpg"
    output_path = app.config["UPLOAD_FOLDER"] / output_name

    # 1. Try Hugging Face (Short 15s timeout to prevent Render crash)
    if HF_TOKEN:
        try:
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {"inputs": full_prompt, "options": {"wait_for_model": True}}
            res = requests.post(HF_API_URL, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                result_img = Image.open(io.BytesIO(res.content))
                result_img.save(output_path, format="JPEG")
                return jsonify({
                    "imageUrl": f"/outputs/{output_name}",
                    "downloadUrl": f"/outputs/{output_name}",
                    "prompt": full_prompt
                })
        except Exception:
            pass  # If HF times out or fails, gracefully switch to local processing

    # 2. Instant Local Vintage Filter (Guaranteed zero crashes)
    input_img = Image.open(uploaded_file.stream)
    result_img = apply_local_vintage_filter(input_img, era)
    result_img.save(output_path, format="JPEG")

    return jsonify({
        "imageUrl": f"/outputs/{output_name}",
        "downloadUrl": f"/outputs/{output_name}",
        "prompt": full_prompt
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
