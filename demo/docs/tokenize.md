To use Hugging Face's `transformers` library with Nesa's encrypted Llama-3.2-1B model. Follow the steps below to get started.

1. **Hugging Face Token**:
   - Log in to the [Hugging Face website](https://huggingface.co).
   - Click on your profile icon and select **Access Tokens**.
   - Generate a token and use it in place of `<YOUR_TOKEN>` in the code below.

2. **Request Model Access**:
   Visit the [meta-llama/Llama-3.2-1B model page](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct) and request access.

### Load the Tokenizer

```python
from transformers import AutoTokenizer

hf_token = "<HF TOKEN>"  # Replace with your token
model_id = "nesaorg/Llama-3.2-1B-Instruct-Encrypted"
tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token, local_files_only=True)
```

### Tokenize and Decode Text

```python
text = "I'm super excited to join Nesa's Equivariant Encryption initiative!"

# Encode text into token IDs
token_ids = tokenizer.encode(text)
print("Token IDs:", token_ids)

# Decode token IDs back to text
decoded_text = tokenizer.decode(token_ids)
print("Decoded Text:", decoded_text)
```

**Example Output:**
```
Token IDs: [128000, 1495, 1135, 2544, 6705, 284, 2219, 11659, 17098, 22968, 8707, 2544, 3539, 285, 34479]
Decoded Text: I'm super excited to join Nesa's Equivariant Encryption initiative!
```
