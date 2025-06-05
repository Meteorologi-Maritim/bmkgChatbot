import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings
from configuration_db import *
from langchain_community.document_loaders.csv_loader import UnstructuredCSVLoader
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_community.document_loaders.image import UnstructuredImageLoader
import requests
import time
# import multiprocessing
from concurrent.futures import ThreadPoolExecutor
# from langchain_experimental.text_splitter import SemanticChunker
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from langchain.schema import Document

load_dotenv(override=True)
openai_api_key = os.getenv("OPEN_API_KEY")
MONGODB_ATLAS_CLUSTER_URI = MONGODB_ATLAS_CLUSTER_URI

client = client
DB_NAME = DB_NAME
COLLECTION_NAME = COLLECTION_NAME
ATLAS_VECTOR_SEARCH_INDEX_NAME = ATLAS_VECTOR_SEARCH_INDEX_NAME
MONGODB_COLLECTION = MONGODB_COLLECTION

folder_path = "D:/#BMKG/ojt/chatbot/doc"

def get_filename_from_url(url):
    segments = url.split('/')
    filename = segments[-1]
    filename = filename.split('?')[0]
    return filename

def ocr_image(image_path):
    try:
        # Convert image to text using pytesseract
        text = pytesseract.image_to_string(Image.open(image_path))
        return text
    except Exception as e:
        print(f"Error performing OCR on image {image_path}: {e}")
        return ""
    
def ocr_pdf(pdf_path):
    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        docs = []

        for i, image in enumerate(images, start=1):
            # Perform OCR on each image
            ocr_text = pytesseract.image_to_string(image)
            if ocr_text.strip():  # Check if there's any meaningful text
                doc = Document(
                    page_content=ocr_text,
                    metadata={
                        "source": pdf_path,
                        "filename": get_filename_from_url(pdf_path),
                        "page": i  # Store the current page number
                    }
                )
                docs.append(doc)

        return docs
    except Exception as e:
        print(f"Error performing OCR on PDF {pdf_path}: {e}")
        return []

def get_data(knowledge):
    start_time = time.time()
    try:
        docs = []
        if knowledge["url"].startswith('http://') or knowledge["url"].startswith('https://'):
            response = requests.get(knowledge["url"], stream=True)
            response.raise_for_status()  
        
        if knowledge["url"].endswith('.pdf'):
            ocr_docs = ocr_pdf(knowledge["url"])
            if ocr_docs:
                docs.extend(ocr_docs)
            else:
                try:
                    loader = PyPDFLoader(knowledge["url"], extract_images=True)
                    docs.extend(loader.load())
                except Exception as e:
                    loader = PyPDFLoader(knowledge["url"])
                    docs.extend(loader.load())
            
        elif knowledge["url"].endswith('.png') or knowledge["url"].endswith('.jpg'):
            ocr_text = ocr_image(knowledge["url"])
            if ocr_text:
                doc = Document(
                    page_content=ocr_text, 
                    metadata={
                        "source": knowledge["url"], 
                        "filename": get_filename_from_url(knowledge["url"]),
                        "page": 1  # Assume a single-page image
                    }
                )
                docs.append(doc)
            else:
                loader = UnstructuredImageLoader(knowledge["url"])
                docs.extend(loader.load())
        elif knowledge["url"].endswith('.csv'):
            loader = UnstructuredCSVLoader(knowledge["url"])
            docs.extend(loader.load())
        elif knowledge["url"].endswith('.xls') or knowledge["url"].endswith('.xlsx'):
            loader = UnstructuredExcelLoader(knowledge["url"], mode="elements")
            docs.extend(loader.load())
        else:
            print("Unsupported file format for URL:", knowledge["url"])
        
        end_time = time.time()
        print("get_data execution time:", end_time - start_time, "seconds")
        return docs
    
    except Exception as e:
        print("Error get_data :", e)
        raise Exception(e)
        
def get_chunks(docs):
    start_time = time.time()
    try:
        text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n",
                                                                   "\n",
                                                                   " ",
                                                                   ".",
                                                                   ",",],
                                                       chunk_size = 10000,
                                                       chunk_overlap  = 1000,
                                                       length_function = len,
                                                       is_separator_regex=True)
        
        # text_splitter = SemanticChunker(OpenAIEmbeddings(openai_api_key=openai_api_key), 
        #                                 breakpoint_threshold_type="percentile")
        
        chunks = text_splitter.split_documents(docs)
        end_time = time.time()
        print("get_chunks execution time:", end_time - start_time, "seconds")
        return chunks
    
    except Exception as e:
        print("get_chunks :", e)
        raise Exception(e)
        
def embed_to_mongo(chunks):
    start_time = time.time()
    try:
        vector_search = MongoDBAtlasVectorSearch.from_documents(
            documents=chunks,
            embedding=OpenAIEmbeddings(disallowed_special=(), openai_api_key=openai_api_key),
            collection=MONGODB_COLLECTION,
            index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME)
        end_time = time.time()
        print("embed_to_mongo execution time:", end_time - start_time, "seconds")
        print("Documents embedded successfully.")
        return vector_search
    
    except Exception as e:
        print("Error embedding documents:", e)
        return None

def process_file(file):
    try:
        if file.endswith(('.pdf', '.png', '.jpg', '.csv', '.xlsx')):
            file_path = os.path.join(folder_path, file)
            knowledge = {"url": file_path}
            docs = get_data(knowledge)
            if docs:
                chunks = get_chunks(docs)
                result = embed_to_mongo(chunks)
                if result is not None:
                    print("File", file, "processed successfully.")
        else:
            print("Unsupported file format:", file)
    except Exception as e:
        print(f"Error processing file {file}: {e}")

def main():
    try:
        start_time = time.time()

        with ThreadPoolExecutor() as executor:
            executor.map(process_file, os.listdir(folder_path))

        end_time = time.time()
        print("Total time taken:", end_time - start_time, "seconds")

    except Exception as e:
        print("main:", e)
        raise Exception(e)

if __name__ == "__main__":
    main()