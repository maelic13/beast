from pathlib import Path

import numpy as np
import onnx
import tensorflow as tf
import tf2onnx
from keras import Sequential


def save_onnx(
    model: Sequential,
    model_name: str,
    example_data: np.ndarray,
    path: Path,
) -> None:
    model.output_names = ["output"]
    input_signature = [
        tf.TensorSpec(shape=(None, *example_data.shape), dtype=tf.float32, name="input")
    ]
    onnx_model, _ = tf2onnx.convert.from_keras(model, input_signature=input_signature)
    onnx.save(onnx_model, path / f"{model_name}.onnx")


def save_onnx_with_metadata(
    model: Sequential,
    model_name: str,
    example_data: np.ndarray,
    path: Path,
    model_version: str,
) -> None:
    save_onnx(model, model_name, example_data, path)

    file_path = path / f"{model_name}.onnx"
    onnx_model = onnx.load(str(file_path))
    onnx_model.metadata_props.add(key="model_version", value=model_version)
    onnx.save(onnx_model, str(file_path))
