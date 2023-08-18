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
    # Remove special characters
    sanitized = ''.join(e for e in filename if e.isalnum() or e == ' ')
    
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    sanitized = sanitized.replace('!', '_')
    sanitized = sanitized.replace('...', '_')
    sanitized = sanitized.replace('..', '_')
    sanitized = sanitized.replace('.', '_')
    sanitized = sanitized.replace('|', '_')
    
    # Limit length to 65 characters
    sanitized = sanitized[:65]
    
    return sanitized

def get_transcription(url):
    # # Update progress
    # emit('progress', {'data': 25})  # 25% for starting

    # # Create a yt-dlp options dictionary
    # ydl_opts = {
    #     'format': 'bestaudio/best',
    #     'postprocessors': [{
    #         'key': 'FFmpegExtractAudio',
    #         'preferredcodec': 'mp3',
    #         'preferredquality': '192',
    #     }],
    #     'outtmpl': '%(title)s.%(ext)s',
    # }

    # # Download the video and extract the audio
    # with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    #     ydl.download([url])

    # # Get the path of the file
    # file_path = ydl.prepare_filename(ydl.extract_info(url, download=False))
    # file_path = file_path.replace('.webm', '.mp3')
    # file_path = file_path.replace('.m4a', '.mp3')

    # # Update progress
    # emit('progress', {'data': 50})  # 50% after download

    # # Transcribe the audio
    # result = model.transcribe(file_path)

    # emit('progress', {'data': 75})  # 75% after transcription

    # # Split the result and retain the punctuation
    # sentences = re.split("([!?.])", result["text"])
    # sentences = ["".join(i) for i in zip(sentences[0::2], sentences[1::2])]
    # text = "\n\n".join(sentences)

    # # Save the transcript in the 'uploads' directory
    # save_directory = "uploads"
    # if not os.path.exists(save_directory):
    #     os.makedirs(save_directory)

    # # Create a sanitized filename by removing special characters and limiting length
    # base_filename = os.path.basename(file_path).split('.')[0]  # Extract name without extension
    # sanitized_filename = sanitize_filename(base_filename) + ".txt"
    # name = os.path.join("uploads", sanitized_filename)
    
    # with open(name, "w") as f:
    #     f.write(text)

    # # Update progress to done
    # emit('progress', {'data': 100})  # 100% once done
    # emit('done', {'data': name})


    # ***************************************************** #
    # ***************************************************** #
    # ***************************************************** #

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

    # Get the path of the file
    file_path = ydl.prepare_filename(ydl.extract_info(url, download=False))
    file_path = file_path.replace('.webm', '.mp3')
    file_path = file_path.replace('.m4a', '.mp3')

    # Extract video info to get the title
    video_info = youtube_dl.YoutubeDL(ydl_opts).extract_info(url, download=False)
    video_title = video_info.get("title", "transcript")

    # Sanitize the video title to use as a filename
    sanitized_filename = sanitize_filename(video_title) + ".txt"
    name = os.path.join("uploads", sanitized_filename)

    # # Update progress
    # emit('progress', {'data': 50})  # 50% after download
    # Update progress to done
    emit('progress', {'data': 100})  # 100% once done
    print(f"Attempting to read from: {name}")
    with open(name, "r") as file:
        transcript_content = file.read()

    emit('done', {'filename': sanitized_filename, 'transcript': transcript_content})


    # Transcribe the audio
    result = model.transcribe(file_path)

    emit('progress', {'data': 75})  # 75% after transcription

    # Split the result and retain the punctuation
    sentences = re.split("([!?.])", result["text"])
    sentences = ["".join(i) for i in zip(sentences[0::2], sentences[1::2])]
    text = "\n\n".join(sentences)

    # Save the transcript using the sanitized video title as the filename
    with open(name, "w") as f:
        f.write(text)

    # Update progress to done
    emit('progress', {'data': 100})  # 100% once done
    emit('done', {'data': sanitized_filename})

    # ***************************************************** #
    # ***************************************************** #
    # ***************************************************** #
    
if __name__ == "__main__":
    socketio.run(app, debug=True)
