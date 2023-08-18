from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
import os
import whisper
import time
import librosa
import re
import yt_dlp as youtube_dl

app = Flask(__name__)
socketio = SocketIO(app)


# Ensure the uploads directory exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Load the model
model = whisper.load_model("base")



@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/download_page/<path:filename>', methods=['GET'])
def download_page(filename):
    with open(os.path.join("uploads", filename), "r") as file:
        content = file.read()
    
    print("Sending transcript:", content)  # Debug print
    return jsonify({'transcript': content})


@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    return send_from_directory("uploads", filename, as_attachment=True)

@socketio.on('start_transcription')
def handle_message(message):
    url = message['url']
    get_transcription(url)


def sanitize_filename(filename):
    sanitized = ''.join(e for e in filename if e.isalnum() or e == ' ')
    sanitized = sanitized.replace(' ', '_').replace('!', '_').replace('...', '_').replace('..', '_').replace('.', '_').replace('|', '_')

    return sanitized[:65]

def get_transcription(url):
    # Starting time for download
    download_start_time = time.time()

    # Update progress
    emit('progress', {'data': 25})  # 25% for starting

    # Create a yt-dlp options dictionary
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(title)s.%(ext)s',
    }

    # Download the video and extract the audio
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

        file_path = ydl.prepare_filename(ydl.extract_info(url, download=False)).replace('.webm', '.mp3').replace('.m4a', '.mp3')
        video_info = youtube_dl.YoutubeDL(ydl_opts).extract_info(url, download=False)
        video_title = video_info.get("title", "transcript")

    # # Get the path of the file
    # file_path = ydl.prepare_filename(ydl.extract_info(url, download=False))
    # file_path = file_path.replace('.webm', '.mp3').replace('.m4a', '.mp3')

    # # Extract video info to get the title
    # video_info = youtube_dl.YoutubeDL(ydl_opts).extract_info(url, download=False)
    # video_title = video_info.get("title", "transcript")

    # Sanitize the video title to use as a filename
    sanitized_filename = sanitize_filename(video_title) + ".txt"
    name = os.path.join("uploads", sanitized_filename)

    # End time for download
    download_end_time = time.time()

    # Starting time for transcription
    transcribe_start_time = time.time()

    # Transcribe the audio
    result = model.transcribe(file_path)

    # Split the result and retain the punctuation
    sentences = re.split("([!?.])", result["text"])
    sentences = ["".join(i) for i in zip(sentences[0::2], sentences[1::2])]
    text = "\n\n".join(sentences)

    # Save the transcript using the sanitized video title as the filename
    with open(name, "w") as f:
        f.write(text)

    # End time for transcription
    transcribe_end_time = time.time()

    # Emit timings
    emit('download_time', {'data': download_end_time - download_start_time})
    emit('transcription_time', {'data': transcribe_end_time - transcribe_start_time})

    # Update progress to done
    emit('progress', {'data': 100})  # 100% once done
    emit('done', {'data': sanitized_filename})

    
if __name__ == "__main__":
    socketio.run(app, debug=True)
