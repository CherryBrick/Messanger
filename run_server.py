import asyncio
import logging
import os
import subprocess

from dotenv import load_dotenv

import server

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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        subprocess.run(['npx', 'kill-port', PORT])
