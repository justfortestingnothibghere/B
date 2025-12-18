from flask import Flask, request, send_from_directory, render_template, abort, Response
import os
import uuid
import time
import threading

app = Flask(__name__, template_folder='templates')

# Directories
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Limits and secrets
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB
BOT_AUTH_SECRET = 'your-super-secret-key'

# Auto-cleanup old files (every hour, delete >24h old)
def cleanup_downloads():
    while True:
        now = time.time()
        for filename in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.getmtime(file_path) < now - 86400:  # 24 hours
                os.remove(file_path)
        time.sleep(3600)  # 1 hour

threading.Thread(target=cleanup_downloads, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    key = request.args.get('key')
    if key != 'teamdev':
        return abort(403, 'Invalid key')

    auth_header = request.headers.get('X-Bot-Auth')
    if auth_header != BOT_AUTH_SECRET:
        return abort(403, 'Unauthorized')

    if 'file' not in request.files:
        return abort(400, 'No file uploaded')
    
    file = request.files['file']
    if not file.filename.endswith('.zip'):
        return abort(400, 'Must be a zip file')

    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}.zip"
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    file.save(file_path)

    download_url = f"https://hostaitelegrambot.onrender.com/get/{filename}"
    return {'url': download_url}, 200

@app.route('/downloads/<filename>', methods=['GET'])
def download(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

@app.route('/get/<filename>')
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return abort(404, 'File not found')
    
    # Detect if Chrome for auto-download
    user_agent = request.headers.get('User-Agent', '').lower()
    is_chrome = 'chrome' in user_agent
    
    return render_template('get.html', filename=filename, is_chrome=is_chrome)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
