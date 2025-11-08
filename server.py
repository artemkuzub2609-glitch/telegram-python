import socket
import threading

# ==== Кольори для консолі ====
RESET = "\033[0m"
WHITE = "\033[97m"
BLUE = "\033[94m"
PURPLE = "\033[95m"
GREEN = "\033[92m"
RED = "\033[91m"

HOST = '0.0.0.0'
PORT = 8080
clients = []

def broadcast(data, exclude_socket=None):
    for client in clients:
        if client != exclude_socket:
            try:
                client.sendall(data)
            except:
                pass

def handle_client(client_socket, addr):
    print(f"{GREEN}[INFO]{RESET} Клієнт {BLUE}{addr}{RESET} підключився.")
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            broadcast(data, exclude_socket=client_socket)
        except:
            break
    if client_socket in clients:
        clients.remove(client_socket)
    client_socket.close()
    print(f"{RED}[INFO]{RESET} Клієнт {BLUE}{addr}{RESET} відключився.")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"{PURPLE}[SERVER]{RESET} Сервер запущено на {WHITE}{HOST}:{PORT}{RESET}")

    while True:
        client_socket, addr = server_socket.accept()
        clients.append(client_socket)
        t = threading.Thread(target=handle_client, args=(client_socket, addr))
        t.start()

if __name__ == "__main__":
    main()

