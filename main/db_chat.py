# Import Library
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from langchain_community.utilities import SQLDatabase
from sqlalchemy.exc import ProgrammingError
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

def d_load_environment_variables():
    load_dotenv(override=True)
    openai_api_key = os.getenv("OPEN_API_KEY")
    db_password = os.getenv("DB_PASSWORD_1")
    return openai_api_key, db_password

def create_sql_chains(llm, databases):
    chains = {}
    for db_name, db in databases.items():
        execute_query = QuerySQLDataBaseTool(db=db)
        write_query = create_sql_query_chain(llm, db)
        
        answer_prompt = PromptTemplate.from_template(
            """Anda HARUS mengikuti aturan berikut!
            ATURAN:
            - Anda adalah agen yang dirancang untuk berinteraksi dengan basis data SQL.
            - Diberikan pertanyaan dari pengguna, buatlah kueri SQL yang sintaksisnya benar untuk dijalankan, lalu lihat hasil kueri tersebut dan kembalikan jawabannya.
            - JANGAN membuat pernyataan DML apa pun (INSERT, UPDATE, DELETE, DROP dsb.) ke basis data.
            - Untuk memulai, Anda HARUS SELALU melihat tabel dalam basis data untuk melihat apa yang dapat Anda tanyakan.
            - Kemudian Anda harus menanyakan skema tabel yang paling relevan.
            - Jika memang tidak ditemukan jawaban dalam database maka jawab dengan kata 'maaf tidak ditemukan jawaban'

            Pertanyaan: {question}
            Kueri SQL: {query}
            Hasil SQL: {result}
            Jawaban: """
        )
        
        answer = answer_prompt | llm | StrOutputParser()
        chains[db_name] = (
            RunnablePassthrough.assign(query=write_query).assign(
                result=itemgetter("query") | execute_query
            )
            | answer
        )
    return chains

def create_connection_string(db_user, db_password, db_host, db_name, db_port):
    return f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def create_sql_databases(db_user, db_password, db_host, db_names, db_port):
    databases = {}
    for db_name in db_names:
        connection_string = create_connection_string(db_user, db_password, db_host, db_name, db_port)
        databases[db_name] = SQLDatabase.from_uri(connection_string)
    return databases

def create_chat_openai(api_key):
    return ChatOpenAI(openai_api_key=api_key, model_name='gpt-3.5-turbo-0125', temperature=0)

def user_interaction(sql_chains):
    print("Chatbot is running. Type 'exit', 'quit', or 'q' to stop.")
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Chatbot has stopped.")
            break
    
        sql_results = []
        for db_name, sql_chain in sql_chains.items():
            try:
                sql_result = sql_chain.invoke({"question": user_input})
                sql_results.append(f"Database {db_name}:\n{sql_result}")
            except ProgrammingError as e:
                sql_results.append(f"Database {db_name}:\nError: {e}")
        
        sql_combined_results = "\n".join(sql_results)
        print(f"Assistant: {sql_combined_results}")
   
def db_run():
    openai_api_key, db_password = d_load_environment_variables()
    # SQL knowledge chatbot setup
    db_user = 'root'
    db_host = 'localhost'
    db_names = ['airportdb']
    db_port = '3306'
    databases = create_sql_databases(db_user, db_password, db_host, db_names, db_port)
    llm = create_chat_openai(openai_api_key)
    sql_chains = create_sql_chains(llm, databases)
    user_interaction(sql_chains)