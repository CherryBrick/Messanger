import logging
import os
import select
import socket
import threading

from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

to_monitor = []
lock = threading.Lock()


def socket_register():
    server_address = (HOST, int(PORT))
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server_address)

    with lock:
        to_monitor.append(client_socket)
    return client_socket


def send_requests():
    current_socket = None
    try:
        while True:
            request = input("Enter your request: ")
            try:
                if not to_monitor or not (current_socket in to_monitor):
                    current_socket = socket_register()
                current_socket.sendall(request.encode())
            except Exception as e:
                logging.error(f'{e}')
    except KeyboardInterrupt:
        print('No more requests.')
    finally:
        with lock:
            for sock in to_monitor:
                sock.close()
            to_monitor.clear()


def event_loop():
    while True:
        with lock:
            if not to_monitor:
                continue
            ready_to_read, _, _ = select.select(to_monitor, [], [])
        for sock in ready_to_read:
            try:
                response = sock.recv(1024)
                if not response:
                    print("Server closed the connection.")
                    with lock:
                        to_monitor.remove(sock)
                    sock.close()
                print("Received response:", response.decode())
            except Exception as e:
                logging.error(f'{e}')
                with lock:
                    to_monitor.remove(sock)
                    sock.close()


def main():

    event_loop_thread = threading.Thread(target=event_loop)
    event_loop_thread.start()

    send_requests()

    event_loop_thread.join()


if __name__ == "__main__":
    main()
