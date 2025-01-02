from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer
from typing import Any
import os
from safetensors import safe_open
from safetensors.torch import save_file
from typing import Tuple, List
import torch
from pprint import pprint
from nesa.backend.registry import ModelRegistry
import warnings
from modules import shared
from typing import Generator, Optional, List, Any, Union


def add_metadata_to_safetensors(file_path: str):
    
    metadata = {"format":"pt"}
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"file '{file_path}' does not exist.")

    with safe_open(file_path, framework="pt") as f:
        tensors = {key: f.get_tensor(key) for key in f.keys()}
        existing_metadata = f.metadata()

    if existing_metadata:
        return
    updated_metadata = existing_metadata if existing_metadata else {}
    updated_metadata.update(metadata)
    save_file(tensors, file_path, metadata=updated_metadata)

@ModelRegistry.register(
    "nesaorg_distilbert-sentiment-encrypted",
    is_model_specific=True)
class HuggingFaceModelMixin:
    """
    A mixin to automate loading of Hugging Face models and tokenizers
    from a local directory or the Hugging Face Hub.
    """

    def __init__(self, **kwargs):
        warnings.warn("Instantiation is deprecated.", DeprecationWarning)
    def load_model_tokenizer(cls,model_name):
        """
        load model and tokenizer using configuration and local files.
        """
        model_dir = os.path.join(shared.args.model_dir,model_name)

        tokenizer = AutoTokenizer.from_pretrained(model_dir,
                                                  local_files_only=True)
        
        model = AutoModelForSequenceClassification.from_pretrained(
            model_dir,
            trust_remote_code=True,
            local_files_only=True
        )
        
        print(f"Model '{model_name}' loaded successfully ")
        return tokenizer, model

    @classmethod
    def perform_inference(
        cls,
        tokenizer: Any,
        model: Any,
        current_msg: str,
        model_name: Optional[Any] = None,
        history: Optional[List[str]] = [],
        system_prompt: Optional[str] = "",
    ) -> Generator[str, None, None]:
        """
        perform inference on the input text and return class labels with scores.
        """
        inputs = tokenizer(
            current_msg,
            return_tensors="pt"
        )
        
        input_ids = inputs["input_ids"].squeeze().tolist()
        formatted_input_ids = f"Encrypted Token IDs:  {', '.join(map(str, input_ids))}\n\n"
        yield formatted_input_ids

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits

        probs = torch.nn.functional.softmax(logits, dim=-1)
        probs = probs.squeeze().tolist()
        
        model_dir = os.path.join(shared.args.model_dir, model_name.replace("/", "_").lower())
        config_path = os.path.join(model_dir, "config.json")
        config = AutoConfig.from_pretrained(config_path, local_files_only=True)

        class_scores = {config.id2label[i]: prob for i, prob in enumerate(probs)}
        sorted_class_scores = dict(sorted(class_scores.items(), key=lambda item: item[1], reverse=True))

        formatted_output = "Class Scores:\n\n"
        formatted_output += "\n\n".join([f"{label}: {prob:.4f}" for label, prob in sorted_class_scores.items()])
        yield formatted_output


    def detokenize(self, token_ids: List[int]) -> str:
        return self.tokenizer.decode(token_ids, skip_special_tokens=True)


if __name__ == "__main__":
    local_model_dir = "models/models--cardiffnlp--twitter-roberta-base-sentiment-latest"
    model_name = local_model_dir.split("models--")[-1].replace("--", "/")
    model_name = "nesaorg/ee_test_nesa"
    print("model:", model_name)
    print("local dir:", local_model_dir)

    model_mixin = HuggingFaceModelMixin(model_name=model_name, local_model_dir=None)
    model_mixin.load_model_and_tokenizer()
    input_text = "I am not feeling bad today."
    outputs = model_mixin.perform_inference(input_text)
    pprint(outputs, indent=4)