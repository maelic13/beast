from multiprocessing import Process, Queue
from time import sleep

from engine import Engine
from uci_protocol import UciProtocol


if __name__ == "__main__":
    print("Beast 2.0 by Miloslav Macurek")

    queue = Queue()
    Process(target=Engine(queue).start, daemon=True).start()
    sleep(0.1)  # wait for process to start

    UciProtocol(queue).uci_loop()
