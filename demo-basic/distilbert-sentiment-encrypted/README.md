---
tags:
- text-classification
- encryption
- equivariant-encryption
- nesa
license: apache-2.0
thumbnail: nesa-logo.png
library_name: transformers
language:
- en
---


# Nesa's Community Equivariant Encryption on a DistilBERT sentiment model 

This model is an encrypted version (although not secure since the corresponding tokenizer is also released in the model files) of:

https://huggingface.co/distilbert/distilbert-base-uncased-finetuned-sst-2-english/blob/main/README.md

In this community edition v1 encryption schema, we used an approximation of our high fidelity version available for enterprise. Please go to our github repo for more information about Nesa and our Equivariant Encryption method:

https://github.com/nesaorg/nesa

## What is Equivariant Encryption?

Developed at Nesa, Equivariant Encryption allows LLMs to run inference on encrypted tokens so that the device running the model never has access to the plaintext data.  The suggested inference set up is to run the encrypted tokenizer locally with the model weights run in an external system, such as a cloud compute environment. When set up this way, Equivariant Encryption allows totally blind server privacy in the sense that the compute environment never sees the plaintext.  This is in contrast to current methods in production today where prompts, even when encrypted through https, must be converted to plaintext before running inference, such as the case for ChatGPT or Claude.  Using the Equivariant Encryption set up, the response can also be returned as encrypted tokens, when run in generative mode.  This gives the highest level of privacy on both the input and output data currently achievable.  

## Limitations of the Community Version

Due to the approximations involved, the results of this model are only expected to reproduce the results of the original model about 92% of the time with a small change in the confidence scores as well.
This public version demonstrates that inference with our encryption scheme results in zero additional latency.  We encourage the community to benchmark the encrypted version with the original version to confirm this level of fidelity.  We also invite people to compare our encrypted model weights against the original model.

## Running the model

To load up the model, use the following code:
```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
model_name = "nesaorg/distilbert-sentiment-encrypted-community-v1"

model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
tokenizer = AutoTokenizer.from_pretrained(model_name)
```

To run inference on an example, use the following code:
```python
inputs = tokenizer("Hello, I love you", return_tensors="pt")

with torch.no_grad():
    logits = model(**inputs).logits

predicted_class_id = logits.argmax().item()
label = model.config.id2label[predicted_class_id]
score = torch.max(torch.nn.Softmax()(logits)).item()
print(f"The sentiment was classified as {label} with a confidence score of {score}")
```