from queue import Queue
from threading import Thread

from beast_chess.engine import Engine, UciProtocol


def main() -> None:
    queue = Queue()
    engine_thread = Thread(target=Engine(queue).start)
    engine_thread.start()

    protocol = UciProtocol(queue)
    try:
        protocol.uci_loop()
    finally:
        protocol.quit()
        engine_thread.join(timeout=1)


if __name__ == "__main__":
    main()
