from multiprocessing import Process, Queue, freeze_support
from time import sleep

from beast_chess.engine import Engine, UciProtocol
from beast_chess.infra import Constants


def start_engine(command_queue: Queue) -> None:
    """
    Safely start the engine after creating its own new process.
    Necessary for macOS compatibility.
    """
    Engine(command_queue).start()


if __name__ == "__main__":
    print(f"{Constants.ENGINE_NAME} {Constants.ENGINE_VERSION} by {Constants.AUTHOR}")

    freeze_support()
    queue = Queue()
    Process(target=start_engine, args=(queue,), daemon=True).start()
    sleep(0.1)  # wait for the process to start

    UciProtocol(queue).uci_loop()
