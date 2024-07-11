import logging
import os
import socket

from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    try:
        while True:
            try:
                while True:
                    request = input('Your request: ')
                    logging.info(f'Request {request} is ready.')
                    client_socket = socket.create_connection((HOST, int(PORT)),
                                                             timeout=5)
                    logging.info(f'Socket connected to {HOST}:{PORT}.')
                    encoded_request = request.encode()
                    logging.info(f'Request {request} is encoded.')
                    client_socket.send(encoded_request)
                    logging.info('Request sent.')
                    response = client_socket.recv(1024)
                    logging.info('Encoded response recieved.')
                    decoded_response = response.decode()
                    logging.info(f'Response is decoded: {decoded_response}.')
                    client_socket.close()
                    logging.info('Connection closed.')
            except Exception as e:
                logging.error(f'{e}')
                if client_socket:
                    client_socket.close()
                    logging.info('Connection closed.')
    except KeyboardInterrupt:
        pass
    finally:
        if client_socket:
            client_socket.close()
            logging.info('Connection closed.')
            logging.info('Client shut down.')


if __name__ == '__main__':
    main()
