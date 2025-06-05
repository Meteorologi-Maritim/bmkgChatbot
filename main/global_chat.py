# Import Library
import openai
from dotenv import load_dotenv
import os

def g_load_environment_variables():
    load_dotenv(override=True)
    openai_api_key = os.getenv("OPEN_API_KEY")
    return openai_api_key

def global_chat(history, openai_api_key):
    openai.api_key = openai_api_key
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=history)
    return response.choices[0].message.content

def global_run():
    history = [{"role": "system", "content": "You are a helpful assistant."}]
    openai_api_key = g_load_environment_variables()
    print("Chatbot is running. Type 'exit', 'quit', or 'q' to stop.")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Chatbot has stopped.")
            break
        
         # Add the user input to the history
        history.append({"role": "user", "content": user_input})
        
        # Get the response from the chatbot
        response = global_chat(history, openai_api_key)
        
        # Add the chatbot's response to the history
        history.append({"role": "assistant", "content": response})
        
        print(f"Assistant: {response}")