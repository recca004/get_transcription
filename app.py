from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
import os
import whisper
import time
import re
import yt_dlp as youtube_dl

app = Flask(__name__)
socketio = SocketIO(app)

# Ensure the uploads directory exists
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load the whisper model
model = whisper.load_model("base")


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/download_page/<path:filename>', methods=['GET'])
def download_page(filename):
    with open(os.path.join(UPLOAD_FOLDER, filename), "r") as file:
        content = file.read()
    return jsonify({'transcript': content})


@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@socketio.on('start_transcription')
def handle_message(message):
    url = message['url']
    get_transcription(url)


def sanitize_filename(filename):
    # Replace all non-alphanumeric characters (except spaces) with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9 ]', '_', filename)
    return sanitized[:65]


def get_transcription(url):
    # Initial progress
    emit('progress', {'data': 10})
    
    # Define download options
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(title)s.%(ext)s',
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        emit('progress', {'data': 50})

        file_path = ydl.prepare_filename(ydl.extract_info(url, download=False)).replace('.webm', '.mp3').replace('.m4a', '.mp3')
        video_title = ydl.extract_info(url, download=False).get("title", "transcript")

    sanitized_filename = sanitize_filename(video_title) + ".txt"
    name = os.path.join(UPLOAD_FOLDER, sanitized_filename)

    # Transcribe the audio
    result = model.transcribe(file_path)
    emit('progress', {'data': 75})

    sentences = re.split("([!?.])", result["text"])
    text = "\n\n".join("".join(i) for i in zip(sentences[0::2], sentences[1::2]))

    with open(name, "w") as f:
        f.write(text)

    # Final progress and emit done
    emit('progress', {'data': 100})
    emit('done', {'data': sanitized_filename})


if __name__ == "__main__":
    socketio.run(app, debug=True)
