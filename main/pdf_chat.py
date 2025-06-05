#Import Library
import os
from dotenv import load_dotenv
from configuration_db import *
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from bson import ObjectId

def v_load_environment_variables():
    load_dotenv(override=True)
    openai_api_key = os.getenv("OPEN_API_KEY")
    mongodb_atlas_cluster_uri = MONGODB_ATLAS_CLUSTER_URI
    db_name = DB_NAME
    collection_name = COLLECTION_NAME
    atlas_vector_search_index_name = ATLAS_VECTOR_SEARCH_INDEX_NAME
    return openai_api_key, mongodb_atlas_cluster_uri, db_name, collection_name, atlas_vector_search_index_name

def recall_embed(mongodb_atlas_cluster_uri, db_name, collection_name, openai_api_key, atlas_vector_search_index_name):
    return MongoDBAtlasVectorSearch.from_connection_string(
        mongodb_atlas_cluster_uri,
        f"{db_name}.{collection_name}",
        OpenAIEmbeddings(openai_api_key=openai_api_key),
        index_name=atlas_vector_search_index_name
    )
    
def get_doc_conversation_chain(call_vector_search, system_input, openai_api_key):
    context = "{context}"
    
    general_system_template = r""" Anda HARUS mengikuti aturan berikut!
    ATURAN:
    - PAHAMI konteks dokumen yang diberikan, selalu pertimbangkan istilah serupa untuk memahami konteks dokumennya.
    - INGAT langkah pertama adalah memahami konteks dokumen dengan mempertimbangkan istilah serupa.
    - Langkah selanjutnya adalah menjawab seluruh pertanyaan berdasarkan konteks dokumen yang telah Anda pahami. 
    - HANYA jawab pertanyaan jika pertanyaannya berkaitan langsung dengan konteks dokumen yang diberikan.
    - JANGAN memberikan jawaban yang tidak berada di dalam konteks dokumen. Hindari menjawab pertanyaan diluar konteks dokumen.
    - Selalu gunakan lebih banyak teks untuk mengelaborasi jawaban. Namun, pastikan bahwa penjelasan tetap berdasarkan konteks dokumen.
    
    {system_input} {context} 
    """
    
    general_user_template = r"""{input}"""
    
    general_system_template = general_system_template.format(system_input=system_input, context=context)
    messages = [
        SystemMessagePromptTemplate.from_template(general_system_template),
        HumanMessagePromptTemplate.from_template(general_user_template)
    ]
    qa_prompt = ChatPromptTemplate.from_messages(messages)
    
    question_answer_chain = create_stuff_documents_chain(llm = ChatOpenAI(openai_api_key=openai_api_key, 
                                                                          model_name='gpt-4o-mini-2024-07-18'), 
                                                         prompt = qa_prompt)

    # Create the conversation chain
    return create_retrieval_chain(retriever = call_vector_search.as_retriever(search_type="similarity"), 
                                  combine_docs_chain = question_answer_chain)
    
    # return ConversationalRetrievalChain.from_llm(
    #     llm=ChatOpenAI(openai_api_key=openai_api_key, 
    #                    model_name='gpt-3.5-turbo-0125'), 
    #     retriever=call_vector_search.as_retriever(),
    #     chain_type="stuff", 
    #     combine_docs_chain_kwargs={"prompt": qa_prompt},
    #     return_source_documents=True
    # )
    
def user_interaction(doc_chain):
    print("Chatbot is running. Type 'exit', 'quit', or 'q' to stop.")
    chat_history = []
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Chatbot has stopped.")
            break
        
        chat_history.append(HumanMessage(content=user_input))
        
        doc_result = doc_chain.invoke({'input': user_input, 'chat_history': chat_history})
        
        # Append chatbot's response to chat history
        # all = doc_result
        response = doc_result['answer']
        print(f"Assistant: {response}")
        
        for i, doc in enumerate(doc_result['context']):
            source = doc.metadata.get('source')
            page = str(doc.metadata.get('page'))
            print(f"Source {i+1}: {source}, Page: {page}")
            
        # source = doc_result['context'][0].metadata['source']
        # page = str(doc_result['context'][0].metadata['page'])
        
        # chat_history.append(AIMessage(content=response))
        
        # print(f"Assistant: {response}")
        # print(f"Source: {source}")
        # print(f"Page: {page}")
        # print(f"All: {all}")

def vector_run():
    openai_api_key, mongodb_atlas_cluster_uri, db_name, collection_name, atlas_vector_search_index_name = v_load_environment_variables()
    
    # Doc knowledge chatbot setup
    system_input = input("Masukkan Keahlian AI: ")
    recall = recall_embed(mongodb_atlas_cluster_uri, db_name, collection_name, openai_api_key, atlas_vector_search_index_name)
    doc_conversation = get_doc_conversation_chain(recall, system_input, openai_api_key)
    
    user_interaction(doc_conversation)