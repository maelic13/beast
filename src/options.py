from threading import Event
from typing import Any


class Options:
    """ Structure to hold search options. """
    def __init__(self) -> None:
        """ Constructor. """
        self.debug = False						# debug option
        self.threads = 1						# number of threads
        self.fifty_move_rule = True				# whether to play with 50-move rule or not
        self.syzygy_path = "<empty>"			# path to syzygy tablebases
        self.syzygy_probe_limit = 6				# probe limit for syzygy tablebases
        self.time_flex = 10						# time flex for time management
        self.search_algorithm = "alphabeta"		# search algorithm
        self.flag = Event()						# flag to start go function
        self.quiescence = True
        self.heuristic = "classical"		    # type of heuristic
        self.network = "regression"				# type of neural network system
        self.model_file = "nets/bnn.2-100k-2.h5"
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
                self.fifty_move_rule = True
            elif value in ["false", "0"]:
                self.fifty_move_rule = False
        elif option == "timeflex":
            self.time_flex = int(value)
        elif option == "searchalgorithm":
            self.search_algorithm = value
        elif option == "syzzygypath":
            self.syzygy_path = value.replace('\\', '/')
        elif option == "syzygyprobelimit":
            self.syzygy_probe_limit = int(value)
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
            self.model_file = value.replace('\\', '/')

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
            return self.syzygy_path
        elif option == "syzygyprobelimit":
            return self.syzygy_probe_limit
        elif option == "quiescence":
            return self.quiescence
        elif option == "heuristic":
            return self.heuristic
        elif option == "network":
            return self.network
        elif option == "modelfile":
            return self.model_file
