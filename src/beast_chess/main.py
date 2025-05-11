from multiprocessing import Process, Queue, freeze_support
from time import sleep

from beast_chess.engine import Engine, UciProtocol
from beast_chess.infra import Constants


def main() -> None:
    print(f"{Constants.ENGINE_NAME} {Constants.ENGINE_VERSION} by {Constants.AUTHOR}")

    queue = Queue()
    Process(target=Engine(queue).start, daemon=True).start()
    sleep(0.1)  # wait for the process to start

    UciProtocol(queue).uci_loop()


if __name__ == "__main__":
    freeze_support()
    main()
