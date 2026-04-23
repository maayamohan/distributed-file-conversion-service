import socket
import threading
import time
import csv
import os
import ssl

MASTER_HOST = "0.0.0.0"
MASTER_PORT = 4000

WORKERS = [
    ("127.0.0.1", 5000),
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5002),
]

worker_index = 0
lock = threading.Lock()

def get_next_worker():
    global worker_index
    with lock:
        worker = WORKERS[worker_index % len(WORKERS)]
        worker_index += 1
    return worker

def recv_exact(sock, size):
    data = b''
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            return None
        data += packet
    return data

# CSV setup
if not os.path.exists("performance.csv"):
    with open("performance.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "file_size", "duration_seconds"])

def handle_client(client_conn, client_addr):
    print(f"[MASTER] Connected: {client_addr}")
    worker_conn = None

    try:
        name_len = int.from_bytes(recv_exact(client_conn, 4), 'big')
        filename = recv_exact(client_conn, name_len).decode()
        file_size = int.from_bytes(recv_exact(client_conn, 8), 'big')

        start_time = time.time()

        worker_host, worker_port = get_next_worker()
        worker_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        worker_conn.connect((worker_host, worker_port))

        # forward header
        worker_conn.sendall(name_len.to_bytes(4, 'big'))
        worker_conn.sendall(filename.encode())
        worker_conn.sendall(file_size.to_bytes(8, 'big'))

        # forward file
        received = 0
        while received < file_size:
            data = client_conn.recv(min(4096, file_size - received))
            worker_conn.sendall(data)
            received += len(data)

        # receive pdf size
        pdf_size = int.from_bytes(recv_exact(worker_conn, 8), 'big')
        client_conn.sendall(pdf_size.to_bytes(8, 'big'))

        # forward pdf
        sent = 0
        while sent < pdf_size:
            data = worker_conn.recv(min(4096, pdf_size - sent))
            client_conn.sendall(data)
            sent += len(data)

        duration = time.time() - start_time

        with open("performance.csv", "a", newline="") as f:
            csv.writer(f).writerow([filename, file_size, round(duration, 4)])

        print(f"[MASTER] Done in {duration:.4f}s")

    except Exception as e:
        print("[MASTER ERROR]", e)

    finally:
        client_conn.close()
        if worker_conn:
            worker_conn.close()

def start_master():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((MASTER_HOST, MASTER_PORT))
    server.listen(5)

    server = context.wrap_socket(server, server_side=True)

    print(f"[MASTER] Running (SSL) on {MASTER_PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_master()