from flask import Flask, request, jsonify, render_template
# from global_chat import global_run
from global_chat import global_ask
from csv_chat import csv_run
from db_chat import db_run
from pdf_chat import vector_run, v_load_environment_variables, recall_embed, get_doc_conversation_chain
from combine_chat import combine_run
from langchain_core.messages import HumanMessage
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

openai_api_key, mongodb_uri, db_name, collection_name, vector_index = v_load_environment_variables()
recall = recall_embed(mongodb_uri, db_name, collection_name, openai_api_key, vector_index)
system_input = "Keahlian AI dalam dokumen PDF"
doc_conversation = get_doc_conversation_chain(recall, system_input, openai_api_key)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    source = data.get('source')
    user_input = data.get('input')

    if not user_input:
        return jsonify({"error": "Input tidak boleh kosong"}), 400
    if not source:
        return jsonify({"error": "Sumber jawaban harus dipilih"}), 400

    try:
        if source == '1':  # Global chat
            answer = global_ask(user_input)
            sources = []
        elif source == '2':  # CSV chat
            answer = csv_run(user_input)
            sources = []
        elif source == '3':  # DB chat
            answer = db_run(user_input)
            sources = []
        elif source == '4':  # PDF/vector chat
            chat_history = [HumanMessage(content=user_input)]
            # doc_result = doc_conversation({'input': user_input, 'chat_history': chat_history})
            doc_result = doc_conversation.invoke({'input': user_input, 'chat_history': chat_history})
            answer = doc_result['answer']
            sources = [{"source": doc.metadata.get('source'), "page": doc.metadata.get('page')} for doc in doc_result.get('context', [])]
        elif source == '5':  # Combination
            answer = combine_run(user_input)
            sources = []
        else:
            return jsonify({"error": "Pilihan sumber tidak valid"}), 400

        return jsonify({
            "response": answer,
            "sources": sources
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
