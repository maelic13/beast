from multiprocessing import Process, Queue

from engine import Engine
from uci_protocol import UciProtocol


if __name__ == "__main__":
    print("Beast 2.0 by Miloslav Macurek")

    queue = Queue()
    engine = Engine(queue)
    Process(target=engine.start, daemon=True).start()

    UciProtocol(queue).uci_loop()
