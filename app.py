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
    try:
        w_percent = (width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        if mode not in ['subpixel', 'solid']:
            h_size = int(h_size * 0.55) 
        img = img.resize((width, h_size), Image.Resampling.LANCZOS)
    except: return "Error", ""

    try:
        if mode == 'line':
            img = img.convert('L')
            img = img.filter(ImageFilter.FIND_EDGES)
            img = ImageOps.invert(img)
        else:
            if img.mode != 'RGB': img = img.convert('RGB')
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(float(contrast))
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(float(brightness))
    except: pass

    if dither == 'true' and mode not in ['subpixel', 'solid']:
        img = img.convert('1')
        img = img.convert('RGB')
    else:
        img = img.convert('RGB')

    width, height = img.size
    html_output = ""
    raw_text_output = ""

    if mode == 'subpixel':
        for y in range(0, height - 1, 2):
            line_html = ""
            for x in range(width):
                r1, g1, b1 = img.getpixel((x, y))
                r2, g2, b2 = img.getpixel((x, y + 1))
                style = f"color:rgb({r1},{g1},{b1});background-color:rgb({r2},{g2},{b2});"
                line_html += f'<span style="{style}">▀</span>'
            html_output += line_html + "<br>"
    elif mode == 'solid':
        for y in range(height):
            line_html = ""
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                style = f"color:rgb({r},{g},{b});"
                line_html += f'<span style="{style}">█</span>'
            html_output += line_html + "<br>"
    elif mode == 'matrix':
        img_gray = img.convert('L')
        pixels = img_gray.getdata()
        matrix_chars = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ10"
        for i, val in enumerate(pixels):
            if i % width == 0 and i != 0: html_output += "<br>"
            if val > 40:
                html_output += f'<span style="color:rgba(0, 255, 70, {val/255})">{random.choice(matrix_chars)}</span>'
            else:
                html_output += '<span style="color:black">&nbsp;</span>'
    else:
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
            if mode == 'ascii_color':
                r, g, b = rgb_pixels[i]
                style = f"color:rgb({r},{g},{b});"
            elif color_hex:
                style = f"color:{color_hex};"
            else:
                style = ""
            html_output += f'<span style="{style}">{char}</span>'
            raw_text_output += char

    return html_output, raw_text_output

@app.route('/')
def index(): return render_template('index.html', title="Home")

@app.route('/generator')
def generator(): return render_template('generator.html', title="Generator")

@app.route('/batch')
def batch(): return render_template('batch.html', title="Batch Generator")

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
                response = requests.get(image_url.strip(), headers=REQUEST_HEADERS, timeout=10)
                img = Image.open(BytesIO(response.content))
            except Exception as e: return jsonify({'error': "Could not load URL"}), 400
        elif 'image_file' in request.files:
            img = Image.open(request.files['image_file'].stream)

        if not img: return jsonify({'error': 'No image source'}), 400

        try:
            width = int(request.form.get('width', 100))
            contrast = float(request.form.get('contrast', 1.0))
            brightness = float(request.form.get('brightness', 1.0))
            mode = request.form.get('mode', 'subpixel')
            charset = request.form.get('charset', 'standard')
            color = request.form.get('color', '')
            dither = request.form.get('dither', 'false')
        except: return jsonify({'error': 'Invalid settings'}), 400

        html, raw = process_image(img, width, contrast, brightness, mode, charset, color, dither)
        return jsonify({'html': html, 'raw': raw})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/batch/download', methods=['POST'])
def batch_download():
    files = request.files.getlist('images')
    urls = request.form.get('image_urls', '').splitlines()
    
    valid_files = [f for f in files if f.filename != '']
    valid_urls = [u for u in urls if len(u.strip()) > 5]

    if (len(valid_files) + len(valid_urls)) > 10: return "Error: Limit 10", 400

    width = int(request.form.get('width', 100))
    contrast = float(request.form.get('contrast', 1.0))
    brightness = float(request.form.get('brightness', 1.0))
    mode = request.form.get('mode', 'subpixel')
    charset = request.form.get('charset', 'standard')
    color = request.form.get('color', '')
    dither = request.form.get('dither', 'false')

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for i, file in enumerate(valid_files):
            try:
                img = Image.open(file.stream)
                html, raw = process_image(img, width, contrast, brightness, mode, charset, color, dither)
                ext = "html" if mode in ['subpixel','solid','ascii_color','matrix'] else "txt"
                content = f"<html><body style='background:white; font-family:monospace; line-height:1; white-space:pre;'>{html}</body></html>" if ext == "html" else raw
                zf.writestr(f"img_{i}_{file.filename}.{ext}", content)
            except: pass
        for i, url in enumerate(valid_urls):
            try:
                img = Image.open(BytesIO(requests.get(url.strip(), headers=REQUEST_HEADERS, timeout=10).content))
                html, raw = process_image(img, width, contrast, brightness, mode, charset, color, dither)
                ext = "html" if mode in ['subpixel','solid','ascii_color','matrix'] else "txt"
                content = f"<html><body style='background:white; font-family:monospace; line-height:1; white-space:pre;'>{html}</body></html>" if ext == "html" else raw
                zf.writestr(f"url_{i}.{ext}", content)
            except: pass

    memory_file.seek(0)
    return send_file(memory_file, download_name='textcanvas_batch.zip', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)