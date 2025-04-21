from multiprocessing import Process, Queue
from time import sleep

from constants import Constants
from engine import Engine
from uci_protocol import UciProtocol


def main() -> None:
    print(f"{Constants.ENGINE_NAME} {Constants.ENGINE_VERSION} by {Constants.AUTHOR}")

    queue = Queue()
    Process(target=Engine(queue).start, daemon=True).start()
    sleep(0.1)  # wait for the process to start

    UciProtocol(queue).uci_loop()


if __name__ == "__main__":
    main()
