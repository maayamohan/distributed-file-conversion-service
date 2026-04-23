import socket
import os
import ssl

SERVER_HOST = "10.1.23.10"
SERVER_PORT = 4000


def recv_exact(sock, size):
    data = b''
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            raise Exception("Connection closed early")
        data += packet
    return data


def send_file(file_path):
    if not os.path.exists(file_path):
        print("File not found!")
        return

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client = context.wrap_socket(raw_socket, server_hostname=SERVER_HOST)

    client.connect((SERVER_HOST, SERVER_PORT))
    print("[CLIENT] Connected to Master (SSL)")

    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    client.send(len(filename).to_bytes(4, 'big'))
    client.send(filename.encode())
    client.send(file_size.to_bytes(8, 'big'))

    print(f"[CLIENT] Sending {filename} ({file_size} bytes)")

    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            client.sendall(chunk)

    print("[CLIENT] Waiting for PDF...")

    pdf_size = int.from_bytes(recv_exact(client, 8), 'big')

    with open("output.pdf", "wb") as f:
        received = 0
        while received < pdf_size:
            chunk = client.recv(min(4096, pdf_size - received))
            if not chunk:
                break
            f.write(chunk)
            received += len(chunk)

    print("[CLIENT] PDF saved as output.pdf")

    client.close()


if __name__ == "__main__":
    path = input("Enter .txt file path: ")
    send_file(path)