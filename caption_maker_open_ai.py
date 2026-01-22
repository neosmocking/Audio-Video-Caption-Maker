import os
import json
import openai
from datetime import datetime

# -----------------------
# Setup API Key
# -----------------------
openai.api_key = os.getenv("OPENAI_API_KEY")  # atau ganti langsung string "sk-..."
# -----------------------
# Fungsi Utility
# -----------------------
def format_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def write_srt_wordwise(words, srt_path):
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, w in enumerate(words, 1):
            start = format_time(w['start'])
            end = format_time(w['end'])
            text = w['word'].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

# -----------------------
# Pilihan file/folder
# -----------------------
video_extensions = [".mp4", ".mkv", ".mov", ".avi"]
files_to_process = []

mode_choice = input("Pilih mode: 1=file, 2=folder: ").strip()

if mode_choice == "1":
    file_path = input("Masukkan path file video: ").strip()
    if os.path.isfile(file_path) and any(file_path.lower().endswith(ext) for ext in video_extensions):
        files_to_process.append(file_path)
elif mode_choice == "2":
    folder_path = input("Masukkan path folder video: ").strip()
    for f in os.listdir(folder_path):
        full_path = os.path.join(folder_path, f)
        if os.path.isfile(full_path) and any(f.lower().endswith(ext) for ext in video_extensions):
            files_to_process.append(full_path)

if not files_to_process:
    print("Tidak ada video untuk diproses.")
    exit(1)

# -----------------------
# Pilihan bahasa
# -----------------------
lang_choice = input("Pilih bahasa: 1=Indonesia, 2=English: ").strip()
language = "id" if lang_choice=="1" else "en"

# -----------------------
# Folder output
# -----------------------
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# -----------------------
# Proses setiap file
# -----------------------
for file_path in files_to_process:
    base_name = os.path.basename(file_path)
    name_no_ext, _ = os.path.splitext(base_name)
    srt_file = os.path.join(output_dir, f"{name_no_ext}.srt")

    if os.path.exists(srt_file):
        print(f"{srt_file} sudah ada, skip.")
        continue

    try:
        print(f"\nTranscribing {file_path} ... (OpenAI API)")
        audio_file = open(file_path, "rb")

        # API call Whisper
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"  # ini memberi word-level timestamps
        )

        # Ambil semua kata
        words = []
        for seg in transcript["segments"]:
            if "words" in seg:
                words.extend(seg["words"])

        if not words:
            print("Tidak ada kata terdeteksi, menggunakan segment fallback...")
            # fallback: setiap segment jadi satu 'kata'
            for seg in transcript["segments"]:
                words.append({
                    "word": seg["text"],
                    "start": seg["start"],
                    "end": seg["end"]
                })

        # tulis SRT kata-per-kata
        write_srt_wordwise(words, srt_file)
        print(f"SRT kata-per-kata berhasil dibuat: {srt_file}")

    except Exception as e:
        print(f"Error: {e}")
        with open(os.path.join(output_dir, "error_log.txt"), "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} - {base_name}: {e}\n")

print("\nSelesai semua video! Semua SRT ada di folder 'output'.")
