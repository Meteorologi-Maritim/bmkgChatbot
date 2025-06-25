import requests
from dotenv import load_dotenv
import os

# === Memuat API Key dari .env ===
def g_load_environment_variables():
    load_dotenv(override=True)
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    return openrouter_api_key

# === Fungsi untuk Mengirim Permintaan ke OpenRouter ===
def global_chat(history, openrouter_api_key):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Chatbot BMKG"
    }
    json_data = {
        "model": "openai/gpt-4o-mini",
        "messages": history
    }
    response = requests.post(url, headers=headers, json=json_data)
    
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    
    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content']

# === Fungsi Utama untuk Dipanggil dari Flask (1x input) ===
def global_run(user_input):
    openrouter_api_key = g_load_environment_variables()
    history = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_input}
    ]
    return global_chat(history, openrouter_api_key)

# === Fungsi Opsional: CLI Chatbot (manual, tidak dipakai di Flask) ===
def run_interactive_cli_chat():
    openrouter_api_key = g_load_environment_variables()
    history = [{"role": "system", "content": "You are a helpful assistant."}]
    print("Chatbot is running. Type 'exit', 'quit', or 'q' to stop.")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Chatbot has stopped.")
            break

        history.append({"role": "user", "content": user_input})
        response = global_chat(history, openrouter_api_key)
        history.append({"role": "assistant", "content": response})

        print(f"Assistant: {response}")

if __name__ == "__main__":
    run_interactive_cli_chat()