import socket
from fpdf import FPDF
import sys
import time

HOST = "0.0.0.0"
PORT = int(sys.argv[1])

def recv_exact(conn, size):
    data = b''
    while len(data) < size:
        packet = conn.recv(size - len(data))
        if not packet:
            return None
        data += packet
    return data

def convert_txt_to_pdf(txt_file, pdf_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    with open(txt_file, "r") as f:
        for line in f:
            pdf.cell(200, 10, txt=line.strip(), ln=True)

    pdf.output(pdf_file)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((HOST, PORT))
server.listen(5)

print(f"[WORKER {PORT}] Running...")

while True:
    conn, addr = server.accept()
    print(f"[WORKER {PORT}] Connected: {addr}")

    try:
        name_len = int.from_bytes(recv_exact(conn, 4), 'big')
        original_filename = recv_exact(conn, name_len).decode()
        file_size = int.from_bytes(recv_exact(conn, 8), 'big')

        unique_name = str(int(time.time() * 1000)) + "_" + original_filename

        with open(unique_name, "wb") as f:
            received = 0
            while received < file_size:
                data = conn.recv(min(4096, file_size - received))
                if not data:
                    break
                f.write(data)
                received += len(data)

        print(f"[WORKER {PORT}] Received {unique_name}")

        pdf_name = unique_name.replace(".txt", ".pdf")
        convert_txt_to_pdf(unique_name, pdf_name)

        print(f"[WORKER {PORT}] Converted to PDF")

        with open(pdf_name, "rb") as f:
            pdf_data = f.read()

        conn.send(len(pdf_data).to_bytes(8, 'big'))
        conn.sendall(pdf_data)

        print(f"[WORKER {PORT}] Sent PDF")

    except Exception as e:
        print(f"[WORKER {PORT}] Error: {e}")

    finally:
        conn.close()