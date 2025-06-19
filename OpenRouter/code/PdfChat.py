import os
import requests
import base64
from pathlib import Path
from dotenv import load_dotenv
from io import BytesIO
from werkzeug.utils import secure_filename  # Penting untuk Flask
os.makedirs("temp_uploads", exist_ok=True)  # Buat folder jika belum ada

# === Load API key dari environment ===
def load_api_key():
    load_dotenv(override=True)
    return os.getenv("OPENROUTER_API_KEY")


# === Encode PDF ke Base64 ===
def encode_pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode("utf-8")


# === Bangun data_url dari file PDF ===
def build_pdf_data_url(pdf_path):
    base64_pdf = encode_pdf_to_base64(pdf_path)
    return f"data:application/pdf;base64,{base64_pdf}"


# === Bangun chat awal dengan file PDF (mode terminal/manual) ===
def build_initial_chat(pdf_path, prompt_text="Tolong pahami isi dokumen ini terlebih dahulu."):
    filename = Path(pdf_path).name
    data_url = build_pdf_data_url(pdf_path)

    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {
                    "type": "file",
                    "file": {
                        "filename": filename,
                        "file_data": data_url
                    }
                }
            ]
        }
    ]


# === Plugin konfigurasi untuk file PDF ===
def get_pdf_plugins():
    return [
        {
            "id": "file-parser",
            "pdf": {"engine": "pdf-text"}
        }
    ]


# === Kirim permintaan ke OpenRouter ===
def chat_with_openrouter(chat_history, api_key, model="google/gemma-3-27b-it"):
    print(f"🔁 Kirim permintaan ke model: {model}")
    print(f"🔑 API Key (3 digit terakhir): ...{api_key[-3:]}" if api_key else "❌ API Key kosong!")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": chat_history,
        "plugins": get_pdf_plugins()
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        print("❌ Error:", response.status_code, response.text)
        return "[Gagal mendapatkan respons dari model]"

# === Fungsi CLI: Jalankan interaktif PDF Chat di Terminal ===
def run_pdf_chat():
    api_key = load_api_key()
    if not api_key:
        print("❌ API key tidak ditemukan. Pastikan .env berisi OPENROUTER_API_KEY.")
        return

    # === Minta path file PDF dari user ===
    pdf_path = input("Masukkan path file PDF kamu: ").strip()

    if not os.path.exists(pdf_path):
        print("❌ File tidak ditemukan. Periksa kembali path-nya.")
        return

    print("\n🤖 Chatbot dokumen aktif. Ketik 'exit', 'quit', atau 'q' untuk keluar.")
    chat_history = build_initial_chat(pdf_path)
    print("🤖 Assistant sedang memproses dokumen awal...\n")

    assistant_reply = chat_with_openrouter(chat_history, api_key)
    print("Assistant:", assistant_reply)
    chat_history.append({"role": "assistant", "content": assistant_reply})

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("👋 Chatbot dihentikan.")
            break

        chat_history.append({"role": "user", "content": user_input})
        assistant_reply = chat_with_openrouter(chat_history, api_key)
        print("Assistant:", assistant_reply)
        chat_history.append({"role": "assistant", "content": assistant_reply})


# === Fungsi untuk Flask: Proses PDF dari file unggahan ===
def process_uploaded_pdf(file_storage):
    file_bytes = file_storage.read()
    base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
    filename = secure_filename(file_storage.filename)

    chat_history = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Tolong pahami isi dokumen ini terlebih dahulu."},
                {
                    "type": "file",
                    "file": {
                        "filename": filename,
                        "file_data": f"data:application/pdf;base64,{base64_pdf}"
                    }
                }
            ]
        }
    ]
    return chat_history


# === Fungsi untuk melanjutkan chat PDF dari frontend ===
def continue_pdf_chat(chat_history, user_prompt):
    api_key = load_api_key()
    chat_history.append({"role": "user", "content": user_prompt})
    assistant_reply = chat_with_openrouter(chat_history, api_key)
    return assistant_reply


# === Entry point ===
if __name__ == "__main__":
    run_pdf_chat()
