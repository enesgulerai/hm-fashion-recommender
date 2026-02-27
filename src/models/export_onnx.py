import os
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer


def export_to_onnx():
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    save_dir = "onnx_model"

    print(f"🚀 Starting ONNX Export for {model_id}...")

    model = ORTModelForFeatureExtraction.from_pretrained(model_id, export=True)
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    os.makedirs(save_dir, exist_ok=True)
    model.save_pretrained(save_dir)
    tokenizer.save_pretrained(save_dir)

    print(f"✅ SUCCESS! ONNX model and tokenizer saved to ./{save_dir}")


if __name__ == "__main__":
    export_to_onnx()
