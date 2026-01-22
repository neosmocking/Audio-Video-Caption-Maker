import os
import whisper
import torch
from datetime import datetime

# -----------------------
# Fungsi Utility
# -----------------------
def format_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def write_srt_word_timestamps(words, srt_path):
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, word in enumerate(words, 1):
            start = format_time(word['start'])
            end = format_time(word['end'])
            f.write(f"{i}\n{start} --> {end}\n{word['text']}\n\n")

# -----------------------
# Pilihan bahasa
# -----------------------
print("Pilih bahasa transkripsi:")
print("1. Indonesia")
print("2. Inggris")
lang_choice = input("Masukkan pilihan (1/2): ").strip()
language = "id" if lang_choice == "1" else "en"

# -----------------------
# Pilihan model Whisper
# -----------------------
print("\nPilih model Whisper:")
print("1. tiny")
print("2. base")
print("3. small")
print("4. medium")
print("5. large")
model_choice = input("Masukkan pilihan (1-5): ").strip()
model_dict = {"1":"tiny", "2":"base", "3":"small", "4":"medium", "5":"large"}
model_name = model_dict.get(model_choice, "base")

# -----------------------
# Pilihan file/folder
# -----------------------
print("\nPilih mode:")
print("1. Satu file video")
print("2. Satu folder video")
mode_choice = input("Masukkan pilihan (1/2): ").strip()

video_extensions = [".mp4", ".mkv", ".mov", ".avi"]
files_to_process = []

if mode_choice == "1":
    file_path = input("Masukkan path file video: ").strip()
    if os.path.isfile(file_path) and any(file_path.lower().endswith(ext) for ext in video_extensions):
        files_to_process.append(file_path)
    else:
        print("File tidak valid atau bukan video.")
        exit(1)

elif mode_choice == "2":
    folder_path = input("Masukkan path folder video: ").strip()
    if not os.path.isdir(folder_path):
        print("Folder tidak valid.")
        exit(1)
    for f in os.listdir(folder_path):
        full_path = os.path.join(folder_path, f)
        if os.path.isfile(full_path) and any(f.lower().endswith(ext) for ext in video_extensions):
            files_to_process.append(full_path)
else:
    print("Pilihan mode tidak valid.")
    exit(1)

if not files_to_process:
    print("Tidak ada video untuk diproses.")
    exit(1)

# -----------------------
# Device GPU/CPU
# -----------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"\nDevice: {device}")

# -----------------------
# Load model Whisper
# -----------------------
print(f"Loading Whisper model '{model_name}'...")
model = whisper.load_model(model_name, device=device)

# -----------------------
# Folder output
# -----------------------
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# -----------------------
# Proses setiap video
# -----------------------
for file_path in files_to_process:
    try:
        base_name = os.path.basename(file_path)
        name_no_ext, _ = os.path.splitext(base_name)
        
        # cek apakah SRT sudah ada
        srt_file = os.path.join(output_dir, f"{name_no_ext}.srt")
        if os.path.exists(srt_file):
            print(f"{srt_file} sudah ada, skip.")
            continue
        
        # transkrip dengan word timestamps
        print(f"\nTranskrip video: {file_path}")
        result = model.transcribe(file_path, language=language, word_timestamps=True)
        words = result.get("words", [])
        
        if not words:
            print(f"Tidak ada kata yang terdeteksi di {base_name}")
            continue
        
        # tulis SRT
        write_srt_word_timestamps(words, srt_file)
        print(f"SRT kata-per-kata berhasil dibuat: {srt_file}")
    
    except Exception as e:
        print(f"Error pada file {base_name}: {e}")
        with open(os.path.join(output_dir, "error_log.txt"), "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} - {base_name}: {e}\n")

print("\nSelesai semua video! Semua SRT ada di folder 'output'.")
