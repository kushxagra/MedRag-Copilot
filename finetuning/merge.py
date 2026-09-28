"""
finetuning/merge.py

Merges the trained LoRA adapter into the Qwen2.5-3B-Instruct base weights,
producing a standalone full model ready for GGUF conversion.

Runs on CPU in fp16 -- merging is a one-time matrix operation, not
training, so no GPU/VRAM is needed here.
"""

from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"
ADAPTER_DIR = Path(__file__).parent / "adapter"
MERGED_DIR = Path(__file__).parent / "merged"


def main():
    print("Loading base model (fp16, CPU)...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="cpu",
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    print("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, str(ADAPTER_DIR))

    print("Merging adapter into base weights...")
    model = model.merge_and_unload()

    print(f"Saving merged model to {MERGED_DIR}")
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(MERGED_DIR), safe_serialization=True)
    tokenizer.save_pretrained(str(MERGED_DIR))
    print("Done.")


if __name__ == "__main__":
    main()
