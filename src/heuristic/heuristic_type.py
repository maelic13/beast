from enum import Enum


class HeuristicType(Enum):
    """
    Supported heuristic types.
    """
    CLASSICAL = "classical"
    RANDOM = "random"

    @staticmethod
    def from_str(string: str) -> "HeuristicType":
        """
        Get HeuristicType from string.
        :param string: identifier
        :return: heuristic type
        """
        match string:
            case "classical":
                return HeuristicType.CLASSICAL
            case "random":
                return HeuristicType.RANDOM
        raise RuntimeError("Invalid heuristic type identifier!")
