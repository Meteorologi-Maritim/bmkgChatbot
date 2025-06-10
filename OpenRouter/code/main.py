from GlobalChat import global_run
# from csv_chat import csv_run
# from db_chat import db_run
# from pdf_chat import vector_run
# from combine_chat import combine_run

def main():
    print("Selamat datang di aplikasi chatbot!")
    print("Pilih sumber jawaban yang ingin Anda gunakan:")
    print("1. Pengetahuan Umum")
    print("2. CSV File (under maintenance)")
    print("3. Database (under maintenance)")
    print("4. Vectorized PDF")
    print("5. Combination of Answer Sources (under maintenance)")
    
    choice = input("Masukkan pilihan Anda (1/2/3/4/5): ")
    
    if choice == '1':
        global_run()
    # elif choice == '2':
    #     csv_run()
    # elif choice == '3':
    #     db_run()
    # elif choice == '4':
    #     vector_run()
    # elif choice == '5':
    #     combine_run()
    else:
        print("Pilihan tidak valid. Silahkan pilih kembali.")

main()