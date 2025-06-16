import os
from flask import Flask, request, render_template, jsonify, session
from werkzeug.utils import secure_filename
from flask_session import Session

# === Impor fungsi eksternal ===
from GlobalChat import global_run 
from PdfChat import process_uploaded_pdf, continue_pdf_chat
from CsvChat import csv_chat 

# === Inisialisasi Flask ===
app = Flask(__name__)

# Gunakan secret key yang aman dan bisa di-set lewat environment variable
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-default-secret-key')

# === Konfigurasi Flask-Session (server-side session) ===
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
    # Jangan hapus session di sini agar riwayat tetap tersimpan selama sesi berjalan
    return render_template("index.html")

# === Endpoint Chat Utama ===
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
                return jsonify({"error": "Path file CSV tidak ada di sesi. Silakan unggah file terlebih dahulu."}), 400
            
            response_text = csv_chat(user_input, file_path)
        
        else:
            response_text = f"Mode untuk sumber '{source}' saat ini belum tersedia."

        return jsonify({"response": response_text})

    except Exception as e:
        print(f"Error di endpoint /chat: {e}")
        return jsonify({"error": "Terjadi kesalahan di server saat memproses chat."}), 500

# === Endpoint Unggah PDF dan Mulai Chat ===
@app.route("/upload_pdf", methods=["POST"])
def upload_pdf_route():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "Tidak ada bagian file dalam permintaan"}), 400
    
    file = request.files['pdf_file']
    
    if file.filename == '':
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400
        
    if file and file.filename.endswith('.pdf'):
        try:
            initial_history = process_uploaded_pdf(file)
            session['pdf_chat_history'] = initial_history
            print("Session pdf_chat_history disimpan:", session.get('pdf_chat_history'))
            return jsonify({"initial_history": initial_history})
        except Exception as e:
            print(f"Error saat memproses PDF di /upload_pdf: {e}")
            return jsonify({"error": "Gagal memproses file PDF di server."}), 500
    
    return jsonify({"error": "Format file tidak valid. Harap unggah file .pdf"}), 400

# === Endpoint Unggah CSV Baru ===
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

        # Update riwayat chat di session dengan user prompt dan balasan assistant
        chat_history.append({"role": "user", "content": user_prompt})
        chat_history.append({"role": "assistant", "content": assistant_reply})
        session['pdf_chat_history'] = chat_history

        return jsonify({"response": assistant_reply})

    except Exception as e:
        print(f"Error di endpoint /chat_pdf: {e}")
        return jsonify({"error": "Gagal mendapatkan balasan dari AI."}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)  # debug=False agar session stabil
