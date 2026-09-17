import os
import base64
from io import BytesIO
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

STYLE_PROMPTS = {
    "1970s": (
        "Transform this photo into an authentic 1970s analog photograph. "
        "Preserve the person's identity, face, pose and overall composition. "
        "Use warm slightly faded colors, soft natural contrast, subtle film grain, "
        "gentle halation, realistic film texture, period-appropriate styling and "
        "a believable 1970s camera/lens character. Avoid changing facial identity."
    ),
    "1980s": (
        "Transform this photo into an authentic 1980s retro photograph. "
        "Preserve the person's identity, face, pose and overall composition. "
        "Use vivid but slightly aged colors, analog film grain, subtle VHS-era "
        "nostalgia, soft flash, realistic photographic texture and an unmistakable "
        "1980s camera look. Avoid changing facial identity."
    ),
    "1990s": (
        "Transform this photo into an authentic 1990s photograph. "
        "Preserve the person's identity, face, pose and overall composition. "
        "Use slightly faded consumer-film colors, natural flash, moderate grain, "
        "soft sharpness, realistic disposable/compact-camera texture and a believable "
        "1990s photo aesthetic. Avoid changing facial identity."
    ),
}

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def build_prompt(style, custom_prompt):
    base = STYLE_PROMPTS.get(style, STYLE_PROMPTS["1970s"])
    custom_prompt = (custom_prompt or "").strip()
    if custom_prompt:
        return base + " Additional user direction: " + custom_prompt
    return base

def apply_retro_filter(image, style):
    # No-API fallback: this makes the project work locally without an AI key.
    img = image.convert("RGB")

    if style == "1970s":
        img = ImageEnhance.Color(img).enhance(0.78)
        img = ImageEnhance.Contrast(img).enhance(0.92)
        img = ImageEnhance.Brightness(img).enhance(1.04)
        warm = Image.new("RGB", img.size, (245, 205, 145))
        img = Image.blend(img, warm, 0.10)

    elif style == "1980s":
        img = ImageEnhance.Color(img).enhance(1.15)
        img = ImageEnhance.Contrast(img).enhance(1.06)
        img = ImageEnhance.Sharpness(img).enhance(0.82)
        warm = Image.new("RGB", img.size, (245, 185, 120))
        img = Image.blend(img, warm, 0.05)

    else:  # 1990s
        img = ImageEnhance.Color(img).enhance(0.90)
        img = ImageEnhance.Contrast(img).enhance(0.96)
        img = ImageEnhance.Sharpness(img).enhance(0.78)

    # Add subtle monochrome grain.
    import random
    grain = Image.new("L", img.size)
    pixels = [random.randint(105, 150) for _ in range(img.width * img.height)]
    grain.putdata(pixels)
    grain_rgb = Image.merge("RGB", (grain, grain, grain))
    img = Image.blend(img, grain_rgb, 0.035)

    # Slightly soften edges like older consumer film.
    img = img.filter(ImageFilter.GaussianBlur(radius=0.25))
    return img

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/outputs/<path:filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=False)

@app.post("/api/prompt")
def prompt_api():
    data = request.get_json(silent=True) or {}
    style = data.get("style", "1970s")
    custom = data.get("customPrompt", "")
    return jsonify({"prompt": build_prompt(style, custom)})

@app.post("/api/convert")
def convert():
    if "photo" not in request.files:
        return jsonify({"error": "Please upload a photo."}), 400

    photo = request.files["photo"]
    if not photo.filename or not allowed(photo.filename):
        return jsonify({"error": "Use JPG, JPEG, PNG or WEBP."}), 400

    style = request.form.get("style", "1970s")
    custom_prompt = request.form.get("customPrompt", "")
    prompt = build_prompt(style, custom_prompt)

    # Optional real AI path.
    # Keep the API key on the server; never put it in frontend JavaScript.
    use_ai = os.getenv("USE_AI", "false").lower() == "true"
    api_key = os.getenv("OPENAI_API_KEY")

    if use_ai and api_key and OpenAI:
        try:
            client = OpenAI(api_key=api_key)
            photo.stream.seek(0)
            result = client.images.edit(
                model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5"),
                image=photo.stream,
                prompt=prompt,
                input_fidelity="high",
                size="auto",
                quality="medium",
                output_format="png",
            )
            b64 = result.data[0].b64_json
            if not b64:
                raise RuntimeError("AI returned no image data.")

            output_name = f"ai_{os.urandom(8).hex()}.png"
            (OUTPUT_DIR / output_name).write_bytes(base64.b64decode(b64))
            return jsonify({
                "success": True,
                "mode": "ai",
                "imageUrl": f"/outputs/{output_name}",
                "downloadUrl": f"/outputs/{output_name}",
                "prompt": prompt
            })
        except Exception as exc:
            # Fall back to local filter so the demo remains usable.
            print("AI conversion failed, using local fallback:", exc)

    try:
        photo.stream.seek(0)
        img = Image.open(photo.stream)
        result = apply_retro_filter(img, style)
        output_name = f"retro_{os.urandom(8).hex()}.jpg"
        result.save(OUTPUT_DIR / output_name, "JPEG", quality=92)
        return jsonify({
            "success": True,
            "mode": "local",
            "imageUrl": f"/outputs/{output_name}",
            "downloadUrl": f"/outputs/{output_name}",
            "prompt": prompt
        })
    except Exception as exc:
        return jsonify({"error": f"Could not process image: {exc}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
