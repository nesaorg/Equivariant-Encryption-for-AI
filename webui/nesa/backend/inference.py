from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer
from typing import Any
import os
from safetensors import safe_open
from safetensors.torch import save_file
from typing import Tuple, List
import torch
from pprint import pprint

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

class HuggingFaceModelMixin:
    """
    A mixin to automate loading of Hugging Face models and tokenizers
    from a local directory or the Hugging Face Hub.
    """

    def __init__(self, model_name: str, local_model_dir: str = None):
        """
        initialize with the huggingface model name or local directory.
        """
        self.model_name = model_name
        self.local_model_dir = local_model_dir
        self.config = None
        self.model = None
        self.tokenizer = None

    def load_model_and_tokenizer(self):
        """
        load model and tokenizer using configuration and local files.
        """
        

        self.config = AutoConfig.from_pretrained(self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name,
                                                       force_download=True,
                                                       use_auth_token="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",
                                                       local_files_only=False)
        
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            use_auth_token="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",
            force_download=True,
            trust_remote_code=True,
            local_files_only=False
        )
        print(f"Model '{self.model_name}' loaded successfully with architecture: {self.config.architectures}")


    def perform_inference(self, input_text: str) -> Tuple[List[str], List[float]]:
        """
        perform inference on the input text and return class labels with scores.
        """
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt"
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits

        probs = torch.nn.functional.softmax(logits, dim=-1)
        probs = probs.squeeze().tolist()

        class_scores = {self.config.id2label[i]: prob for i, prob in enumerate(probs)}
        sorted_class_scores = dict(sorted(class_scores.items(), key=lambda item: item[1], reverse=True))

        return sorted_class_scores
    
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