from threading import Event
from typing import Any


class Options:
    """ Structure to hold search options. """
    def __init__(self) -> None:
        """ Constructor. """
        self.debug = False						# debug option
        self.threads = 1						# number of threads
        self.fiftyMoveRule = True				# whether to play with 50-move rule or not
        self.syzygyPath = "<empty>"				# path to syzygy tablebases
        self.syzygyProbeLimit = 6				# probe limit for syzygy tablebases
        self.timeFlex = 10						# time flex for time management
        self.searchAlgorithm = "AlphaBeta"		# search algorithm
        self.flag = Event()						# flag to start go function
        self.quiescence = True
        self.heuristic = "Classic"				# type of heuristic
        self.network = "Regression"				# type of neural network system
        self.modelFile = "nets/bnn_2-100-2.h5"
        self.model = None                       # loaded keras model if available during search

    def set(self, option: str, value: str) -> None:
        """
        Set desired option to desired value.
        :param option: option string identifier
        :param value: value to be set in string form
        """
        option = option.lower()
        value = value.lower()

        if option.lower() == "debug" and value == "on":
            self.debug = True
        elif option == "debug" and value == "off":
            self.debug = False
        elif option == "threads" and 0 < int(value) < 32:
            self.threads = int(value)
        elif option == "syzygy50moverule":
            if value in ["true", "1"]:
                self.fiftyMoveRule = True
            elif value in ["false", "0"]:
                self.fiftyMoveRule = False
        elif option == "timeflex":
            self.timeFlex = int(value)
        elif option == "searchalgorithm":
            self.searchAlgorithm = value
        elif option == "syzzygypath":
            self.syzygyPath = value.replace('\\', '/')
        elif option == "syzygyprobelimit":
            self.syzygyProbeLimit = int(value)
        elif option == "quiescence":
            if value in ["true", "1"]:
                self.quiescence = True
            elif value in ["false", "0"]:
                self.quiescence = False
        elif option == "heuristic":
            self.heuristic = value
        elif option == "network":
            self.network = value
        elif option == "modelfile":
            self.modelFile = value.replace('\\', '/')

    def value(self, option: str) -> Any:
        """
        Get value of desired option.
        :param option: option string identifier
        :return: option value
        """
        option = option.lower()

        if option == "debug":
            return self.debug
        elif option == "threads":
            return self.threads
        elif option == "syzygypath":
            return self.syzygyPath
        elif option == "syzygyprobelimit":
            return self.syzygyProbeLimit
        elif option == "quiescence":
            return self.quiescence
        elif option == "heuristic":
            return self.heuristic
        elif option == "network":
            return self.network
        elif option == "modelfile":
            return self.modelFile
