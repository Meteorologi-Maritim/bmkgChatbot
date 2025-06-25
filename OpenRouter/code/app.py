import os
import requests
from flask import Flask, request, render_template, jsonify, session
from werkzeug.utils import secure_filename
from flask_session import Session
from dotenv import load_dotenv

# === Impor fungsi eksternal ===
from GlobalChat import global_run
from PdfChat import process_multiple_pdfs, continue_pdf_chat
from webSearch import chat_with_websearch
from CsvChat import csv_chat  # Optional

# === Load API key dari environment ===
def load_api_key():
    load_dotenv(override=True)
    return os.getenv("OPENROUTER_API_KEY")

# === Inisialisasi Flask ===
app = Flask(__name__, static_folder="static", template_folder="templates")

# Secret key untuk session
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-default-secret-key')

# === Konfigurasi Flask-Session ===
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)

# === Konfigurasi folder upload ===
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# === Halaman utama ===
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# === Endpoint Chat Umum / CSV / Web ===
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("input")
        source = data.get("source")

        if not user_input:
            return jsonify({"error": "Input tidak boleh kosong."}), 400

        response_text = ""

        if source == "global":
            response_text = global_run(user_input)

        elif source == "csv":
            file_path = session.get("csv_file_path")
            if not file_path:
                return jsonify({"error": "Path file CSV tidak ditemukan di session."}), 400
            response_text = csv_chat(user_input, file_path)

        elif source == "web":
            api_key = load_api_key()
            if not api_key:
                return jsonify({"error": "API key untuk OpenRouter tidak ditemukan."}), 500

            chat_history = [
                {
                    "role": "system",
                    "content": "Anda adalah asisten BMKG yang hanya menjawab berdasarkan informasi dari https://maritim.bmkg.go.id/. Sertakan URL sumber jika ada."
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]

            response_text = chat_with_websearch(chat_history, api_key)

        else:
            response_text = f"Mode sumber '{source}' belum tersedia."

        return jsonify({"response": response_text})

    except Exception as e:
        print(f"Error di endpoint /chat: {e}")
        return jsonify({"error": "Terjadi kesalahan di server saat memproses chat."}), 500

# === Endpoint Upload Multiple PDF ===
@app.route("/upload_pdf", methods=["POST"])
def upload_pdf_route():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "Tidak ada bagian file dalam permintaan"}), 400

    files = request.files.getlist("pdf_file")

    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400

    try:
        combined_history = process_multiple_pdfs(files)
        combined_history.insert(0, {"role": "system", "content": "You are a helpful assistant."})

        session['pdf_chat_history'] = combined_history
        print("Session pdf_chat_history disimpan:", session.get('pdf_chat_history'))

        return jsonify({"message": f"{len(files)} file berhasil diproses.", "initial_history": combined_history})

    except Exception as e:
        print(f"Error saat memproses PDF di /upload_pdf: {e}")
        return jsonify({"error": "Gagal memproses file PDF di server."}), 500

# === Endpoint Upload CSV ===
@app.route("/upload_csv", methods=["POST"])
def upload_csv_route():
    if 'csv_file' not in request.files:
        return jsonify({"error": "Tidak ada bagian file dalam permintaan"}), 400

    file = request.files['csv_file']

    if file.filename == '':
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400

    if file and file.filename.endswith('.csv'):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            session['csv_file_path'] = file_path
            return jsonify({
                "message": f"File '{filename}' berhasil diunggah.",
                "file_path": file_path
            })

        except Exception as e:
            print(f"Error saat menyimpan CSV di /upload_csv: {e}")
            return jsonify({"error": "Gagal menyimpan file CSV di server."}), 500

    return jsonify({"error": "Format file tidak valid. Harap unggah file .csv"}), 400

# === Endpoint Chat Lanjutan PDF ===
@app.route("/chat_pdf", methods=["POST"])
def chat_pdf_route():
    try:
        chat_history = session.get('pdf_chat_history')
        data = request.get_json()
        user_prompt = data.get('input')

        if not chat_history or not user_prompt:
            return jsonify({"error": "Riwayat chat atau input tidak boleh kosong."}), 400

        print("Session pdf_chat_history saat chat:", chat_history)

        assistant_reply = continue_pdf_chat(chat_history, user_prompt)

        chat_history.append({"role": "user", "content": user_prompt})
        chat_history.append({"role": "assistant", "content": assistant_reply})
        session['pdf_chat_history'] = chat_history

        return jsonify({"response": assistant_reply})

    except Exception as e:
        print(f"Error di endpoint /chat_pdf: {e}")
        return jsonify({"error": "Gagal mendapatkan balasan dari AI."}), 500

# === Jalankan Aplikasi ===
if __name__ == "__main__":
    app.run(debug=False, port=5000)
