import requests
from dotenv import load_dotenv
import os

def g_load_environment_variables():
    load_dotenv(override=True)
    openrouter_api_key = os.getenv("OPEN_ROUTER_KEY")
    return openrouter_api_key

def global_chat(history, openrouter_api_key):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": "gpt-3.5-turbo",
        "messages": history
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content']

def global_run():
    history = [{"role": "system", "content": "You are a helpful assistant."}]
    openrouter_api_key = g_load_environment_variables()
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

def global_ask(user_input):
    openrouter_api_key = g_load_environment_variables()
    history = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_input}
    ]
    return global_chat(history, openrouter_api_key)