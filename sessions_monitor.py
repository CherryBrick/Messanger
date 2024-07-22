import time

from multiprocessing import Process

import sessions


def session_monitor():
    while True:
        s = sessions.sessions
        m = sessions.messages_to_send
        print(f'{s}\n{m}')
        time.sleep(3)


if __name__ == '__main__':
    monitor_process = Process(target=session_monitor)

    try:
        monitor_process.start()
    except KeyboardInterrupt:
        pass
        monitor_process.terminate()
        monitor_process.join()
