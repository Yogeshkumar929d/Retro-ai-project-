import os
import base64
from io import BytesIO
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageEnhance, ImageFilter

app = Flask(__name__)

UPLOAD_FOLDER = Path("outputs")
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def apply_retro_filter(image: Image.Image, era: str) -> Image.Image:
    img = image.convert("RGB")
    r, g, b = img.split()

    if era == "1970s":
        # Warm sepia / golden retro look
        r = r.point(lambda i: min(255, int(i * 1.3)))
        g = g.point(lambda i: int(i * 1.05))
        b = b.point(lambda i: int(i * 0.65))
        img = Image.merge("RGB", (r, g, b))
        img = ImageEnhance.Contrast(img).enhance(1.1)
        img = ImageEnhance.Color(img).enhance(0.9)

    elif era == "1990s":
        # Cooler VHS disposable camera look
        r = r.point(lambda i: int(i * 0.95))
        g = g.point(lambda i: int(i * 1.05))
        b = b.point(lambda i: min(255, int(i * 1.25)))
        img = Image.merge("RGB", (r, g, b))
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Color(img).enhance(1.2)

    else:
        # 1980s: Vibrant neon/analog VHS look
        r = r.point(lambda i: min(255, int(i * 1.25)))
        g = g.point(lambda i: int(i * 0.95))
        b = b.point(lambda i: int(i * 0.75))
        img = Image.merge("RGB", (r, g, b))
        img = ImageEnhance.Color(img).enhance(1.45)
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = img.filter(ImageFilter.SMOOTH_MORE)

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

    file = request.files["photo"]
    era = request.form.get("era", "1980s")
    custom_prompt = request.form.get("prompt", "")

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        raw_img = Image.open(file.stream)
        converted = apply_retro_filter(raw_img, era)

        output_name = f"retro_{era.lower()}.jpg"
        output_path = app.config["UPLOAD_FOLDER"] / output_name
        converted.save(output_path, format="JPEG", quality=90)

        prompt_text = f"Authentic {era} retro style photo filter applied. Tone: Warm analog VHS."
        if custom_prompt:
            prompt_text += f" Custom note: {custom_prompt}"

        return jsonify({
            "imageUrl": f"/outputs/{output_name}",
            "downloadUrl": f"/outputs/{output_name}",
            "prompt": prompt_text
        })
    except Exception as exc:
        return jsonify({"error": f"Could not process image: {exc}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
        
