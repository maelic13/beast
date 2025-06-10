from multiprocessing import Process, Queue, freeze_support
from time import sleep

from beast_chess.engine import Engine, UciProtocol


def start_engine(command_queue: Queue) -> None:
    """
    Safely start the engine after creating its own new process.
    Necessary for macOS compatibility.
    """
    Engine(command_queue).start()


def main() -> None:
    freeze_support()
    queue = Queue()
    Process(target=start_engine, args=(queue,)).start()
    sleep(0.1)  # wait for the process to start

    protocol = UciProtocol(queue)
    try:
        protocol.uci_loop()
    finally:
        protocol.quit()


if __name__ == "__main__":
    main()
