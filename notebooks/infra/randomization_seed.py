import os
import random

import keras
import numpy as np
import tensorflow as tf


def set_seed(seed: int) -> None:
    # Environment seed
    os.environ["PYTHONHASHSEED"] = str(seed)

    # Python seed
    random.seed(seed)

    # Numpy seed
    np.random.seed(seed)

    # keras
    keras.utils.set_random_seed(seed)

    # tensorflow
    tf.config.experimental.enable_op_determinism()
    tf.random.set_seed(seed)
