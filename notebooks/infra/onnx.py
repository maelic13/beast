from pathlib import Path
from typing import Any

import onnx
import tensorflow as tf
import tf2onnx


def save_onnx(model: Any, model_name: str, example_data: Any, path: Path) -> None:
    model.output_names = ["output"]
    input_signature = [
        tf.TensorSpec(shape=(None, *example_data.shape), dtype=tf.float32, name="input")
    ]
    onnx_model, _ = tf2onnx.convert.from_keras(model, input_signature=input_signature)
    onnx.save(onnx_model, path / f"{model_name}.onnx")


def save_onnx_with_metadata(
    model: Any,
    model_name: str,
    example_data: Any,
    path: Path,
    *,
    model_version: str,
) -> None:
    # Export the model to ONNX
    save_onnx(model, model_name, example_data, path)

    # Add metadata
    onnx_model_path = path / f"{model_name}.onnx"
    onnx_model = onnx.load(onnx_model_path)
    onnx_model.metadata_props.add(key="model_version", value=model_version)

    onnx.save(onnx_model, onnx_model_path)
