import asyncio
import logging
import os
import subprocess

from dotenv import load_dotenv
from multiprocessing import freeze_support

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')


async def main():
    server_socket = await asyncio.start_server(
        lambda reader, writer: server.run(reader, writer),
        HOST, int(PORT))
    logging.info(f'Socket is bound to {HOST}:{PORT}.')
    async with server_socket:
        await server_socket.serve_forever()


if __name__ == '__main__':
    freeze_support()
    import server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        subprocess.run(['npx', 'kill-port', PORT])
