from pymongo import MongoClient
MONGODB_ATLAS_CLUSTER_URI = "mongodb+srv://researchh9:XOHfvT9ehBLF0L6Z@cluster0.e9w9uok.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGODB_ATLAS_CLUSTER_URI)
DB_NAME = "bmkg1"
COLLECTION_NAME = "doc1"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "vector_index"
MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]
COLLECTION_NAME_OWN = "history_chat"
COLLECTION_NAME_GLOBAL = "history_chat_global"
