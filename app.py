import os
import uuid
from io import BytesIO
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageEnhance, ImageFilter

app = Flask(__name__)

UPLOAD_FOLDER = Path("outputs")
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def apply_local_retro_filter(image: Image.Image, era: str) -> Image.Image:
    img = image.convert("RGB")
    r, g, b = img.split()

    if era == "1970s":
        # 70s Warm / Golden Film
        r = r.point(lambda i: min(255, int(i * 1.30)))
        g = g.point(lambda i: int(i * 1.05))
        b = b.point(lambda i: int(i * 0.65))
        img = Image.merge("RGB", (r, g, b))
        img = ImageEnhance.Color(img).enhance(0.9)
        img = ImageEnhance.Contrast(img).enhance(1.15)
    elif era == "1990s":
        # 90s Cool Disposable Flash
        r = r.point(lambda i: int(i * 0.95))
        g = g.point(lambda i: int(i * 1.05))
        b = b.point(lambda i: min(255, int(i * 1.25)))
        img = Image.merge("RGB", (r, g, b))
        img = ImageEnhance.Color(img).enhance(1.25)
        img = ImageEnhance.Contrast(img).enhance(1.3)
    else:
        # 1980s Neon Warm Vintage
        r = r.point(lambda i: min(255, int(i * 1.35)))
        g = g.point(lambda i: int(i * 0.95))
        b = b.point(lambda i: int(i * 0.70))
        img = Image.merge("RGB", (r, g, b))
        img = ImageEnhance.Color(img).enhance(1.5)
        img = ImageEnhance.Contrast(img).enhance(1.35)
        img = img.filter(ImageFilter.SMOOTH_MORE)

    return img

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/outputs/<filename>")
def serve_output(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

def process_image():
    # Supports both field names ("image" or "photo")
    file = request.files.get("image") or request.files.get("photo")
    if not file or file.filename == "":
        return jsonify({"error": "No image uploaded"}), 400

    era = request.form.get("era", "1980s")
    custom_prompt = request.form.get("prompt", "")

    try:
        raw_img = Image.open(file.stream)
        converted = apply_local_retro_filter(raw_img, era)

        output_name = f"retro_{era.lower()}_{uuid.uuid4().hex[:8]}.jpg"
        output_path = app.config["UPLOAD_FOLDER"] / output_name
        converted.save(output_path, format="JPEG", quality=90)

        prompt_text = f"Authentic {era} retro film look applied with warm analog vintage tones."
        if custom_prompt:
            prompt_text += f" Note: {custom_prompt}"

        return jsonify({
            "imageUrl": f"/outputs/{output_name}",
            "downloadUrl": f"/outputs/{output_name}",
            "prompt": prompt_text
        })
    except Exception as exc:
        return jsonify({"error": f"Could not process image: {exc}"}), 500

# Support both common endpoints
@app.route("/api/convert", methods=["POST"])
def api_convert():
    return process_image()

@app.route("/convert", methods=["POST"])
def normal_convert():
    return process_image()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
        
