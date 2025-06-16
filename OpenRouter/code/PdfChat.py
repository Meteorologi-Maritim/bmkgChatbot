import requests
import json
import base64
from pathlib import Path

# === Fungsi bantu untuk encode PDF ===
def encode_pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode('utf-8')

# === Konfigurasi awal ===
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {'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'}",  # Ganti dengan API Key Anda
    "Content-Type": "application/json"
}

# === Encode dokumen PDF ===
pdf_path = "D:/#BMKG/ojt/clone_chatbot/bmkgChatbot/bmkgChatbot/doc/gelombang-bmkg.pdf"
base64_pdf = encode_pdf_to_base64(pdf_path)
data_url = f"data:application/pdf;base64,{base64_pdf}"

# === Plugin opsional untuk PDF parsing ===
plugins = [
    {
        "id": "file-parser",
        "pdf": {
            "engine": "pdf-text"  # Bisa juga coba "mistral-ocr"
        }
    }
]

# === Inisialisasi riwayat percakapan ===
chat_history = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Tolong pahami isi dokumen ini terlebih dahulu."
            },
            {
                "type": "file",
                "file": {
                    "filename": "gelombang-bmkg.pdf",
                    "file_data": data_url
                }
            }
        ]
    }
]

# === Fungsi untuk mengirim chat ke OpenRouter ===
def chat_with_openrouter(chat_history):
    payload = {
        "model": "google/gemma-3-27b-it",  # Ganti model sesuai kebutuhan
        "messages": chat_history,
        "plugins": plugins
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        response_json = response.json()
        reply = response_json['choices'][0]['message']['content']
        return reply
    else:
        print("Error:", response.status_code, response.text)
        return "[Gagal mendapatkan respons dari model]"

# === Interaksi Chat ===
def pdf_run():
    print("Chatbot dokumen aktif. Ketik 'exit/quit' untuk keluar.\n")
    
    # Mulai dengan mengirim file ke model
    print("🤖 Assistant sedang memproses dokumen awal...")
    assistant_reply = chat_with_openrouter(chat_history)
    print("Assistant:", assistant_reply)
    chat_history.append({
        "role": "assistant",
        "content": assistant_reply
    })

    # Loop percakapan
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Chatbot dihentikan.")
            break

        chat_history.append({
            "role": "user",
            "content": user_input
        })

        assistant_reply = chat_with_openrouter(chat_history)
        print("Assistant:", assistant_reply)
        
        chat_history.append({
            "role": "assistant",
            "content": assistant_reply
        })

# # === Jalankan program ===
# if __name__ == "__main__":
#     start_chat()