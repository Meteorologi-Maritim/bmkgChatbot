import os
import uuid
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_csv_agent

def load_api_key():
    """
    Memuat API key dari file .env.
    Fungsi ini mencari OPENROUTER_API_KEY sesuai dengan file .env Anda.
    """
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY tidak ditemukan di file .env Anda.")
    return api_key

def create_langchain_agent(api_key, file_path):
    """
    Membuat LangChain agent yang dikonfigurasi untuk CSV.
    """
    llm = ChatOpenAI(
        model='mistralai/mistral-7b-instruct-v0.2',
        temperature=0,
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    
    agent = create_csv_agent(
        llm=llm,
        path=file_path,
        agent_type="openai-tools",
        verbose=True,
        allow_dangerous_code=True,
        handle_parsing_errors="Silakan coba ajukan pertanyaan dengan cara yang berbeda, saya kesulitan memproses permintaan Anda.",
    )
    return agent

def create_dynamic_prompt(user_input):
    """
    Membuat prompt yang dinamis dengan instruksi dan ID unik untuk chart.
    """
    bar_chart_id = f"chart_{uuid.uuid4().hex[:8]}"
    line_chart_id = f"chart_{uuid.uuid4().hex[:8]}"
    pie_chart_id = f"chart_{uuid.uuid4().hex[:8]}"
    
    prompt = f"""
    Pertanyaan Pengguna: "{user_input}"

    ---
    ATURAN DAN FORMAT JAWABAN:
    1.  **Bahasa**: Selalu gunakan Bahasa Indonesia yang baik dan jelas.
    2.  **Konteks**: Jawab HANYA berdasarkan data yang ada di dalam file CSV. Jika data tidak cukup, katakan "Maaf, data yang ada tidak cukup untuk menjawab pertanyaan ini."
    3.  **Perhitungan**: Saat melakukan perhitungan (seperti total, rata-rata, dll.), TULISKAN HASIL AKHIRNYA. Jangan hanya menyebutkan langkah-langkahnya.
    4.  **Format HTML**:
        * Gunakan tag HTML standar (<p>, <ul>, <li>, <table>) untuk menyajikan jawaban teks.
        * Untuk tabel, WAJIB gunakan inline style: `<table style="width: 100%; border-collapse: collapse; border: 1px solid black;">`. Setiap `<th>` dan `<td>` juga harus memiliki style `border: 1px solid #dddddd; text-align: left; padding: 8px;`.
    5.  **Visualisasi Data (Chart)**:
        * Jika pertanyaan meminta visualisasi atau perbandingan, BUATLAH CHART menggunakan Chart.js.
        * Setiap chart HARUS berada di dalam div-nya sendiri seperti ini: `<div><canvas id="ID_UNIK_CHART"></canvas></div>`.
        * Sertakan skrip Chart.js HANYA SATU KALI di akhir: `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`.
        * Gunakan ID unik yang sudah disediakan di bawah untuk setiap kanvas.

    ---
    ID UNIK UNTUK CHART (Gunakan ini di dalam <canvas> dan skrip Chart.js):
    - ID untuk Bar Chart: `{bar_chart_id}`
    - ID untuk Line Chart: `{line_chart_id}`
    - ID untuk Pie Chart: `{pie_chart_id}`
    ---

    Tolong berikan jawaban yang lengkap sekarang.
    """
    return prompt

# Cache agent agar tidak dibuat ulang terus saat request masuk
_agent_cache = {}

def csv_chat(user_input, file_path):
    """
    Fungsi utama untuk pemanggilan dari Flask.
    Menerima input user dan path file CSV, lalu mengembalikan hasil HTML dari agent.
    """
    try:
        api_key = load_api_key()
        cache_key = file_path

        if cache_key not in _agent_cache:
            agent = create_langchain_agent(api_key, file_path)
            _agent_cache[cache_key] = agent
        else:
            agent = _agent_cache[cache_key]

        dynamic_prompt = create_dynamic_prompt(user_input)
        response = agent.invoke({"input": dynamic_prompt})
        return response["output"]

    except Exception as e:
        return f"<p style='color:red;'>Terjadi kesalahan saat memproses: {e}</p>"

# Jika ingin menjalankan interaktif CLI (opsional)
def run_interaction_loop(agent):
    print("\n--- Chatbot CSV Siap ---")
    print("Ketik 'exit' atau 'quit' untuk berhenti.")
    
    while True:
        user_input = input("\nAnda: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Terima kasih! Chatbot berhenti.")
            break

        dynamic_prompt = create_dynamic_prompt(user_input)
        
        try:
            response = agent.invoke({"input": dynamic_prompt})
            print(f"\nAsisten:\n{response['output']}")
        except Exception as e:
            print(f"Terjadi kesalahan: {e}")

def main():
    try:
        api_key = load_api_key()

        source_files = []
        print("Masukkan path lokal atau URL ke file CSV Anda.")
        print("Ketik 'done' jika sudah selesai menambahkan file.")
        
        while True:
            path_input = input(f"Path file CSV ke-{len(source_files) + 1}: ")
            if path_input.lower() == 'done':
                if not source_files:
                    print("Tidak ada file yang dimasukkan. Program berhenti.")
                    return
                break
            source_files.append(path_input)

        agent = create_langchain_agent(api_key, source_files)
        run_interaction_loop(agent)

    except ValueError as e:
        print(f"Error Konfigurasi: {e}")
    except Exception as e:
        print(f"Terjadi error tak terduga: {e}")

if __name__ == "__main__":
    main()
