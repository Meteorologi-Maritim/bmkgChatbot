from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.exc import ProgrammingError
from global_chat import g_load_environment_variables, global_chat
from csv_chat import create_agent, prompt_template
from db_chat import d_load_environment_variables, create_sql_databases, create_chat_openai, create_sql_chains
from pdf_chat import v_load_environment_variables, recall_embed, get_doc_conversation_chain
from langchain_core.messages import HumanMessage, AIMessage

def csv_chat_run(user_input):
    openai_api_key = g_load_environment_variables()
    source = "https://sin1.contabostorage.com/51245209b740442e97dc64f1f2400b16:wavebot-staging/test-dir/edit_csv.csv"
    agent = create_agent(openai_api_key, source)
    prompt = prompt_template(user_input)
    result = agent.invoke(prompt)
    response = result['output']
    source = "file csv"
    return response, source

def vector_chat_run(user_input, system_input):
    openai_api_key, mongodb_atlas_cluster_uri, db_name, collection_name, atlas_vector_search_index_name = v_load_environment_variables()
    
    system_input = system_input
    recall = recall_embed(mongodb_atlas_cluster_uri, db_name, collection_name, openai_api_key, atlas_vector_search_index_name)
    doc_conversation = get_doc_conversation_chain(recall, system_input, openai_api_key)
    
    chat_history = []
    chat_history.append(HumanMessage(content=user_input))
    doc_result = doc_conversation.invoke({'question': user_input, 'chat_history': chat_history})
    
    response = doc_result['answer']
    source =  doc_result['source_documents'][0].metadata['source']
    return response, source

def db_chat_run(user_input):
    openai_api_key, db_password = d_load_environment_variables()
    db_user = 'root'
    db_host = 'localhost'
    db_names = ['airportdb']
    db_port = '3306'
    databases = create_sql_databases(db_user, db_password, db_host, db_names, db_port)
    llm = create_chat_openai(openai_api_key)
    sql_chains = create_sql_chains(llm, databases)
    
    sql_results = []
    for db_name, sql_chain in sql_chains.items():
        try:
            sql_result = sql_chain.invoke({"question": user_input})
            sql_results.append(f"Database {db_name}:\n{sql_result}")
        except ProgrammingError as e:
            sql_results.append(f"Database {db_name}:\nError: {e}")
    
    sql_combined_results = "\n".join(sql_results)
    return sql_combined_results

def refine_combined_answer(openai_api_key, vector_answer, db_answer):
    llm = ChatOpenAI(openai_api_key=openai_api_key, 
                     model_name='gpt-3.5-turbo-0125', 
                     temperature=0)
    
    refine_prompt = PromptTemplate.from_template(
        """
        Jawaban dari Pengetahuan Vectorized PDF/CSV: {vector_answer}
        Jawaban dari Pengetahuan Database: {db_answer}
        
        - Terdapat 2 sumber jawaban, yaitu Jawaban dari Pengetahuan Vectorized PDF/CSV dan Jawaban dari Pengetahuan Database. 
        - Berikan jawaban yang paling relevan untuk diberikan kepada pengguna sebagai Jawaban Akhir.
        - Berikan Jawaban Akhir secara akurat dan tepat sesuai dengan pertanyaan dari pengguna.
        
        Jawaban Akhir: """
    )
    
    combined_input = {"vector_answer": vector_answer,
                      "db_answer": db_answer,
                      }
    
    refined_answer = (refine_prompt | llm | StrOutputParser()).invoke(combined_input)
    return refined_answer

def combine_run():
    openai_api_key = g_load_environment_variables()
    
    print("Chatbot is running. Type 'exit', 'quit', or 'q' to stop.")
    system_input = input("Masukkan Keahlian AI: ")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Chatbot has stopped.")
            break
        
        # Simulating fetching answers from different sources
        # global_answer = global_chat_run(user_input)
        vector_answer, source = vector_chat_run(user_input, system_input)
        # csv_answer = csv_chat_run(user_input)
        db_answer = db_chat_run(user_input)
        
        if source.endswith('.csv'):
            vector_answer, source = csv_chat_run(user_input)
        else:
             vector_answer, source =  vector_answer, source
             
        combined_answer = refine_combined_answer(openai_api_key, vector_answer, db_answer)
        
        # print(f"Assistant vector/csv: {vector_answer}")
        # print(f"Source: {source}\n")
        # print(f"Assistant database: {db_answer}")
        print(f"Assistant: {combined_answer}")