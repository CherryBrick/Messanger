import logging
import os
import socket
import subprocess

from dotenv import load_dotenv

import server


load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logging.info(f'Socket {server_socket} created.')
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    logging.info('Socket is set up.')
    server_socket.bind((HOST, int(PORT)))
    logging.info(f'Socket is bound to {HOST}:{PORT}.')
    server_socket.listen()
    logging.info('Socket is listening.')

    server.run(server_socket)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        subprocess.run(['npx', 'kill-port', PORT])
