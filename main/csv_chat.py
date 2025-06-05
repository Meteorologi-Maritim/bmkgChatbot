# from langchain.agents import create_csv_agent
from langchain_experimental.agents import create_csv_agent
# from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os

def load_environment_variables():
    load_dotenv(override=True)
    openai_api_key = os.getenv("OPEN_API_KEY")  # Pastikan di .env kamu ada OPEN_API_KEY (bukan OPEN_API_KEY)
    return openai_api_key

def create_agent(openai_api_key, source):
    return create_csv_agent(
        ChatOpenAI(
            temperature=0,
            model_name="gpt-4o-mini",
            openai_api_key=openai_api_key
        ),
        source,
        verbose=False
    )
    
def prompt_template(user_input):
    prompt = (
        user_input +
        """
        Berdasarkan pertanyaan diatas, coba jawab pertanyaannya dengan aturan sebagai berikut!
        
        ATURAN MENJAWAB:
        - Gunakan bahasa Indonesia.
        - Jawab hanya jika pertanyaan sesuai dengan konteks dokumen.
        - Berikan jawaban lengkap dan detail, hindari placeholder.
        - Jika ragu, minta maaf dan jangan menjawab.

        PERHITUNGAN MATEMATIS:
        - Berikan hasil perhitungan yang akurat, bukan hanya variabel.

        FORMAT JAWABAN:
        - Gunakan tag HTML untuk merapikan jawaban.
        - Gunakan tag <p>, <ul>, <li>, atau <table> untuk teks.
        - Untuk tabel, gunakan border 1px hitam dengan inline CSS.
        - Gunakan Chart.js untuk chart dengan tag <canvas> dan <script>.

        CONTOH JAWABAN:
        - <p>Jawaban lengkap dalam paragraf.</p>
        - <ul><li>Poin pertama</li><li>Poin kedua</li></ul>
        - <table style="border:1px solid black;"><tr><td>Data</td></tr></table>

        CONTOH MULTIPLE CHART:
        - <div style="position:relative"><canvas id="{randomid}" style="display:block;box-sizing:border-box;height:300px;width:700px" class="bar"></canvas></div>
        - <div style="position:relative"><canvas id="{randomid2}" style="display:block;box-sizing:border-box;height:300px;width:700px" class="line"></canvas></div>
        - <div style="position:relative"><canvas id="{randomid3}" style="display:block;box-sizing:border-box;height:300px;width:700px" class="pie"></canvas></div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            var ctx1 = document.getElementById('{randomid}').getContext('2d');
            var myBarChart = new Chart(ctx1, {{
                type: 'bar',
                data: {{
                    labels: ['Label1', 'Label2'],
                    datasets: [{{
                        label: 'Data1',
                        data: [10, 20]
                    }}]
                }}
            }});

            var ctx2 = document.getElementById('{randomid2}').getContext('2d');
            var myLineChart = new Chart(ctx2, {{
                type: 'line',
                data: {{
                    labels: ['Label1', 'Label2'],
                    datasets: [{{
                        label: 'Data2',
                        data: [30, 40]
                    }}]
                }}
            }});

            var ctx3 = document.getElementById('{randomid3}').getContext('2d');
            var myPieChart = new Chart(ctx3, {{
                type: 'pie',
                data: {{
                    labels: ['Label1', 'Label2'],
                    datasets: [{{
                        label: 'Data3',
                        data: [50, 50]
                    }}]
                }}
            }});
        </script>
        """
    )
    return prompt
    
def user_interaction(agent):
    print("Chatbot is running. Type 'exit', 'quit', or 'q' to stop.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Chatbot has stopped.")
            break
        prompt = prompt_template(user_input)
        result = agent.run(prompt)
        print(f"Assistant: {result}")

def csv_run():
    openai_api_key = load_environment_variables()
    
    source = []
    while True:
        user_input = input("Masukkan URL atau path CSV (atau ketik 'selesai' untuk melanjutkan): ")
        if user_input.lower() == 'selesai':
            break
        source.append(user_input)
    
    if not source:
        print("Tidak ada sumber CSV yang diberikan. Keluar dari program.")
        return
    
    if len(source) == 1:
        source = source[0]
    
    agent = create_agent(openai_api_key, source)
    user_interaction(agent)
