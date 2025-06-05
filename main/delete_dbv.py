from pymongo import MongoClient

def delete_all_documents_in_collection(collection_name):
    # Koneksi ke database MongoDB
    client = MongoClient("mongodb+srv://researchh9:XOHfvT9ehBLF0L6Z@cluster0.e9w9uok.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["bmkg1"]  # Ganti dengan nama database Anda
    collection = db[collection_name]

    # Hapus semua dokumen dalam koleksi
    result = collection.delete_many({})

    print(f"Jumlah dokumen yang dihapus dari koleksi {collection_name}: {result.deleted_count}")

# Contoh penggunaan
delete_all_documents_in_collection("doc1")