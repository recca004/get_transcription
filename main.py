import whisper
import time
import librosa
import re
import yt_dlp as youtube_dl  # Importing yt-dlp

# Load the model
model = whisper.load_model("base.en")

def get_transcription():
    # Prompt user for a YouTube video URL
    url = input("Enter a YouTube video URL: ")

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

    # Get the duration of the video
    duration = librosa.get_duration(filename=file_path)
    start = time.time()
    result = model.transcribe(file_path)
    end = time.time()
    seconds = end - start

    print("Video length:", duration, "seconds")
    print("Transcription time:", seconds)

    # Split the result and retain the punctuation
    sentences = re.split("([!?.])", result["text"])
    sentences = ["".join(i) for i in zip(sentences[0::2], sentences[1::2])]
    text = "\n\n".join(sentences)
    for s in sentences:
        print(s)

    # Save the transcript as a .txt file
    name = "".join(file_path) + ".txt"
    with open(name, "w") as f:
        f.write(text)

    print("\n\n", "-"*100, "\n\nYour transcript is here:", name)

if __name__ == "__main__":
    get_transcription()
