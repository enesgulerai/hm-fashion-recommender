import os
import shutil

from optimum.onnxruntime import ORTModelForFeatureExtraction, ORTQuantizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig
from transformers import AutoTokenizer


def export_to_onnx():
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    save_dir = "onnx_model"

    print(f"Starting ONNX Export for {model_id}...")

    model = ORTModelForFeatureExtraction.from_pretrained(model_id, export=True)
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    os.makedirs(save_dir, exist_ok=True)
    model.save_pretrained(save_dir)
    tokenizer.save_pretrained(save_dir)

    print("Applying INT8 Dynamic Quantization (This makes it 4x smaller & faster)...")
    quantizer = ORTQuantizer.from_pretrained(model)

    dqconfig = AutoQuantizationConfig.avx2(is_static=False)

    quantizer.quantize(save_dir=save_dir, quantization_config=dqconfig)

    quantized_model_path = os.path.join(save_dir, "model_quantized.onnx")
    original_model_path = os.path.join(save_dir, "model.onnx")

    if os.path.exists(quantized_model_path):
        os.remove(original_model_path)
        os.rename(quantized_model_path, original_model_path)

    print(f"SUCCESS! INT8 Quantized ONNX model and tokenizer saved to ./{save_dir}")


if __name__ == "__main__":
    export_to_onnx()
