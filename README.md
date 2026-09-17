# Retro Photo AI

A college-project-ready Flask website that converts a normal photo into 1970s, 1980s, or 1990s retro style.

## Features

- Upload JPG, PNG or WEBP
- 1970s / 1980s / 1990s presets
- Custom prompt
- Generated AI prompt preview
- Download converted image
- Works without an API key using a local Pillow-based retro filter
- Optional server-side AI image editing integration
- Responsive UI

## 1. Install Python

Use Python 3.10+.

## 2. Create virtual environment

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install packages

```bash
pip install -r requirements.txt
```

## 4. Run the project

```bash
python app.py
```

Open:
http://127.0.0.1:5000

## 5. Optional AI mode

The website works immediately in local demo mode. For real AI image editing:

1. Copy `.env.example` to `.env`.
2. Put your API key in `OPENAI_API_KEY`.
3. Set `USE_AI=true`.
4. Start the app again.

The API key is read by the Flask backend, not exposed in browser JavaScript.

The backend uses the OpenAI Python SDK's image editing interface. The image-edit API accepts an input image and prompt; GPT Image models return base64 image data, which this project saves as a local output file.

## Project flow

Browser
  -> Flask `/api/convert`
  -> prompt generation
  -> local Pillow filter OR AI image edit
  -> `outputs/`
  -> preview + download

## Viva explanation

**Frontend:** HTML, CSS and JavaScript provide upload, decade selection, prompt input, preview and download.

**Backend:** Flask receives the image and selected style.

**Prompt generation:** The selected decade is mapped to a predefined prompt. A custom prompt can be appended.

**AI integration:** If an API key is configured, Flask sends the uploaded image and prompt to an image-editing model.

**Fallback:** Without an API key, Pillow applies a local retro effect, so the project remains demonstrable offline.

## Important

Never publish your API key in `script.js`, HTML, GitHub, or a public frontend. Keep it in the server environment.
