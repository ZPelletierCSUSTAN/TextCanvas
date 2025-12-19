import os
import requests
import random
import zipfile
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'textcanvas_key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

CHAR_SETS = {
    'standard': "@%#*+=-:. ",
    'simple': "#@. ",
    'blocks': "█▓▒░ ",
    'binary': "10 ",
    'dots': "⣿⣧⣤⣦⣄⣀⠐⠄ ", 
    'line': "/\|()[]{}?-_+~<>!;:,. " 
}

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Referer': 'https://www.google.com/'
}

def process_image(img, width, contrast, brightness, mode, charset_key, color_hex, dither):
    # 1. Resize & Aspect
    try:
        w_percent = (width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        # Visual block modes need less squishing than text modes
        if mode not in ['subpixel', 'solid']:
            h_size = int(h_size * 0.55) 
        img = img.resize((width, h_size), Image.Resampling.LANCZOS)
    except: return "Error resizing", ""

    # 2. Filters
    try:
        if mode == 'line':
            img = img.convert('L')
            img = img.filter(ImageFilter.FIND_EDGES)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            img = ImageOps.invert(img)
        else:
            if img.mode != 'RGB': img = img.convert('RGB')
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(float(contrast))
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(float(brightness))
    except: pass

    # 3. Dither Logic
    is_dithered = (dither == 'true')
    # Don't dither if we want True Color (ascii_color or subpixel) unless explicitly handled
    if is_dithered and mode not in ['subpixel', 'solid', 'ascii_color']:
        img = img.convert('1')
        img = img.convert('RGB')
    else:
        img = img.convert('RGB')

    width, height = img.size
    html_output = ""
    raw_text_output = ""

    # --- MODES ---
    if mode == 'subpixel':
        # LCD Half Block (High Detail)
        for y in range(0, height - 1, 2):
            line_html = ""
            for x in range(width):
                r1, g1, b1 = img.getpixel((x, y))
                r2, g2, b2 = img.getpixel((x, y + 1))
                
                # If color override is used in Subpixel, we Tint/Force it
                # But typically Subpixel implies True Color. 
                # We will only override if HEX is provided AND it's not the default white/black
                # For now, let's keep subpixel as True Color unless dithered
                style = f"color:rgb({r1},{g1},{b1});background-color:rgb({r2},{g2},{b2});"
                line_html += f'<span style="{style}">▀</span>'
            html_output += line_html + "<br>"

    elif mode == 'solid':
        for y in range(height):
            line_html = ""
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                # Solid mode respects color override if specific single color desired
                style = f"color:{color_hex};" if color_hex and color_hex != "#ffffff" else f"color:rgb({r},{g},{b});"
                line_html += f'<span style="{style}">█</span>'
            html_output += line_html + "<br>"

    elif mode == 'matrix':
        img_gray = img.convert('L')
        pixels = img_gray.getdata()
        matrix_chars = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ10"
        for i, val in enumerate(pixels):
            if i % width == 0 and i != 0: html_output += "<br>"
            if val > 30:
                char = random.choice(matrix_chars)
                alpha = round(val / 255, 2)
                # Use custom hex if provided, else green
                base_color = color_hex if (color_hex and color_hex != "#ffffff") else "rgba(0, 255, 70, 1)"
                if "rgba" not in base_color and "#" in base_color:
                    # Simple hex application with opacity shim (css handles hex opacity poorly without rgba conversion, 
                    # so we just apply hex and use opacity property)
                    style = f"color:{base_color}; opacity:{alpha};"
                else:
                    style = f"color:rgba(0, 255, 70, {alpha});"
                
                html_output += f'<span style="{style}">{char}</span>'
            else:
                html_output += '<span style="color:black">&nbsp;</span>'
    
    else:
        # Standard Text Modes (ASCII, Dots, Line, etc.)
        if mode == 'dots': chars = CHAR_SETS['dots']
        elif mode == 'line': chars = CHAR_SETS['line']
        elif mode == 'binary': chars = CHAR_SETS['binary']
        else: chars = CHAR_SETS.get(charset_key, CHAR_SETS['standard'])

        img_gray = img.convert('L')
        gray_pixels = img_gray.getdata()
        rgb_pixels = img.getdata()

        for i, val in enumerate(gray_pixels):
            if i % width == 0 and i != 0:
                html_output += "<br>"
                raw_text_output += "\n"
            
            char = chars[int((val / 255) * (len(chars) - 1))]

            # --- COLOR LOGIC FIX ---
            if mode == 'ascii_color':
                # ALWAYS use image pixel color for Colored ASCII
                r, g, b = rgb_pixels[i]
                style = f"color:rgb({r},{g},{b});"
            elif color_hex and color_hex != "#ffffff":
                # For Grayscale/Binary/Dots, use the override if set
                style = f"color:{color_hex};"
            else:
                # Default text color (usually white/grey in CSS)
                style = "" 
            
            # HTML Safe
            if char == "<": char = "&lt;"
            if char == ">": char = "&gt;"
            
            html_output += f'<span style="{style}">{char}</span>'
            raw_text_output += char

    return html_output, raw_text_output

# --- ROUTES ---
@app.route('/')
def index(): return render_template('index.html', title="Home")

@app.route('/page3')
def page3(): return render_template('page3.html', title="Generator")

@app.route('/page4')
def page4(): return render_template('page4.html', title="Batch")

@app.route('/page1')
def page1(): return render_template('page1.html', title="Instructions")

@app.route('/page2')
def page2(): return render_template('page2.html', title="About")

@app.route('/api/process', methods=['POST'])
def api_process():
    try:
        img = None
        image_url = request.form.get('image_url')
        if image_url and len(image_url.strip()) > 5:
            try:
                response = requests.get(image_url.strip(), headers=REQUEST_HEADERS, timeout=8)
                img = Image.open(BytesIO(response.content))
            except: return jsonify({'error': "URL Error"}), 400
        elif 'image_file' in request.files:
            img = Image.open(request.files['image_file'].stream)

        if not img: return jsonify({'error': 'No Image'}), 400

        try:
            width = int(request.form.get('width', 100))
            contrast = float(request.form.get('contrast', 1.0))
            brightness = float(request.form.get('brightness', 1.0))
            mode = request.form.get('mode', 'subpixel')
            charset = request.form.get('charset', 'standard')
            color = request.form.get('color', '')
            dither = request.form.get('dither', 'false')
        except: return jsonify({'error': 'Bad Settings'}), 400

        html, raw = process_image(img, width, contrast, brightness, mode, charset, color, dither)
        return jsonify({'html': html, 'raw': raw})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/batch/download', methods=['POST'])
def batch_download():
    return "Use individual download buttons.", 200

if __name__ == '__main__':
    app.run(debug=True)