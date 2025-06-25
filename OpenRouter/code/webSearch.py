import os
import requests
from dotenv import load_dotenv

# === Load API key dari environment ===
def load_api_key():
    load_dotenv(override=True)
    return os.getenv("OPENROUTER_API_KEY")

# === Kirim pertanyaan ke OpenRouter ===
def chat_with_websearch(chat_history, api_key, model="openrouter/auto"):
    print(f"\n🔁 Kirim pertanyaan ke model: {model}")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "plugins": [
            { 
                "id": "web",
                "max_results": 1,
                "search_prompt": "Beberapa hasil pencarian yang relevan:"
                }
        ],
        "messages": chat_history
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        message = result['choices'][0]['message']
        print("\n🧠 Jawaban:")
        print(message['content'])

        if "annotations" in message:
            print("\n🔗 Sumber:")
            for annotation in message["annotations"]:
                if annotation["type"] == "url_citation":
                    info = annotation["url_citation"]
                    print(f"- {info['title']}: {info['url']}")
        else:
            print("\n(Sumber tidak tersedia atau tidak diberikan)")

        return message['content']
    else:
        print("❌ Error:", response.status_code, response.text)
        return "[Gagal mendapatkan respons dari model]"

# === Fungsi CLI: Jalankan interaktif chat dengan Web Search di Terminal ===
def run_websearch_chat():
    api_key = load_api_key()
    if not api_key:
        print("❌ API key tidak ditemukan. Pastikan .env berisi OPENROUTER_API_KEY.")
        return

    print("\n🌐 Chatbot BMKG Web Search (gunakan 'exit' untuk keluar)")
    chat_history = [
    {
        "role": "system",
        "content": "Anda adalah asisten yang hanya menggunakan https://maritim.bmkg.go.id/ sebagai basis pengetahuan. Selalu berikan URL sumbernya.",
        "annotations": [
            {
                "type": "url_citation",
                "url_citation": {
                    "url": "https://maritim.bmkg.go.id/",
                    "title": "Judul hasil pencarian relevan konteks web",
                    "content": "Konten hasil pencarian web",
                    "start_index": 100,
                    "end_index": 200
                }
            }
        ]
    }
]

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("👋 Chatbot dihentikan.")
            break

        # prompt = f"Cari hanya dari https://maritim.bmkg.go.id/ tentang {user_input}. Berikan jawaban yang sesuai konteks dan berikan sumber URL."
        prompt = f"{user_input}"
        chat_history.append({"role": "user", "content": prompt})

        assistant_reply = chat_with_websearch(chat_history, api_key)
        chat_history.append({"role": "assistant", "content": assistant_reply})

# === Entry Point ===
if __name__ == "__main__":
    run_websearch_chat()
