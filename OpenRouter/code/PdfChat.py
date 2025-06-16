import requests
import os
import re
from dotenv import load_dotenv
from PyPDF2 import PdfReader

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def get_response_from_openrouter(chat_history):
    payload = {
        "model": "google/gemma-2-27b-it",  # Ganti jika perlu
        "messages": chat_history
    }
    try:
        response = requests.post(URL, headers=HEADERS, json=payload)
        response.raise_for_status()

        response_json = response.json()
        reply = response_json['choices'][0]['message']['content']
        return reply
    except requests.exceptions.RequestException as e:
        print(f"Error saat request ke OpenRouter: {e}")
        return f"[Gagal terhubung ke layanan AI. Detail: {e}]"
    except KeyError:
        error_details = response.text if 'response' in locals() else "Tidak ada respons"
        print(f"Error: struktur respons tidak terduga dari API. Respons: {error_details}")
        return "[Gagal memproses balasan dari AI karena format respons tidak sesuai]"

<<<<<<< Updated upstream
# === Interaksi Chat ===
def pdf_run():
    print("Chatbot dokumen aktif. Ketik 'exit/quit' untuk keluar.\n")
    
    # Mulai dengan mengirim file ke model
    print("🤖 Assistant sedang memproses dokumen awal...")
    assistant_reply = chat_with_openrouter(chat_history)
    print("Assistant:", assistant_reply)
    chat_history.append({
=======
def extract_clean_text_from_pdf(file_obj):
    try:
        reader = PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        # Bersihkan bullet: *, -, • di awal baris
        clean_lines = []
        for line in text.splitlines():
            line = re.sub(r"^\s*[\*\-•]\s*", "", line)
            line = line.strip()
            if line:
                clean_lines.append(line)

        return "\n".join(clean_lines)
    except Exception as e:
        print(f"Error membaca PDF: {e}")
        raise ValueError("Gagal membaca atau memproses file PDF.")

def process_uploaded_pdf(file_obj):
    try:
        cleaned_text = extract_clean_text_from_pdf(file_obj)
    except Exception as e:
        return [{"role": "assistant", "content": f"Gagal membaca PDF: {e}"}]

    prompt = (
        "Anda adalah asisten yang ahli dalam menganalisis dokumen. "
        "Berikut isi dokumen:\n\n"
        f"{cleaned_text}\n\n"
        "Berikan ringkasan dalam 3 poin utama tanpa menggunakan simbol bullet (*, -, •)."
    )

    initial_message = {
        "role": "user",
        "content": prompt
    }

    initial_history = [initial_message]

    assistant_first_reply = get_response_from_openrouter(initial_history)

    initial_history.append({
>>>>>>> Stashed changes
        "role": "assistant",
        "content": assistant_first_reply
    })

    return initial_history

<<<<<<< Updated upstream
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
=======
def continue_pdf_chat(chat_history, user_prompt):
    new_history = chat_history + [{"role": "user", "content": user_prompt}]
    assistant_reply = get_response_from_openrouter(new_history)
    return assistant_reply
>>>>>>> Stashed changes
