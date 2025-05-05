from enum import Enum


class HeuristicType(Enum):
    """
    Supported heuristic types.
    """

    CLASSICAL = "classical"
    LEGACY_NEURAL_NETWORK = "legacy_neural_network"
    NEURAL_NETWORK = "neural_network"
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
            case "legacy_neural_network":
                return HeuristicType.LEGACY_NEURAL_NETWORK
            case "neural_network":
                return HeuristicType.NEURAL_NETWORK
            case "random":
                return HeuristicType.RANDOM
        msg = "Invalid heuristic type identifier!"
        raise RuntimeError(msg)
