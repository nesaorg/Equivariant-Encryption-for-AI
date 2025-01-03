
# Nesa Encrypted AI Demo

This folder contains a modified version of [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui) set up to demonstrate Nesa’s Equivariant Encryption (EE) on two models:

1. **[nesaorg/distilbert-sentiment-encrypted](https://huggingface.co/nesaorg/distilbert-sentiment-encrypted)** – An encrypted version of `distilbert/distilbert-base-uncased-finetuned-sst-2-english` for sentiment classification.
2. **[nesaorg/Llama-3.2-1B-Instruct-Encrypted](https://huggingface.co/nesaorg/Llama-3.2-1B-Instruct-Encrypted)** – An encrypted version of `meta-llama/Llama-3.2-1B-Instruct` for autoregressive text-generation. 

Use this guide to install and run the demo locally!

## Installation

1. **Clone or Download** this repository:
   ```bash
   git clone https://github.com/nesaorg/nesa
   cd nesa/demo
   ```
	Or download the ZIP from GitHub and unzip it.

2.	Run the Installation Script matching your OS:
	- Linux/Mac: `./start_linux.sh` or `./start_macos.sh`
	- Windows: `start_windows.bat`

3.	Choose Your GPU Vendor when prompted (NVIDIA, AMD, CPU, etc.). The script will install necessary dependencies (PyTorch, Transformers, etc.).

4.	After installation completes, it should automatically launch a local client, or you can manually navigate to http://localhost:7860.

## Usage
We automatically download and select a model for the user, so they can start using right away after the local client loads. We've included information about switching between both demo models below:

#### Llama 3.2
1.	Switch to `nesaorg/Llama-3.2-1B-Instruct-Encrypted` in the Model selection.
2.	Type your prompt into the chat box (for example, `Explain Equivariant Encryption in simple terms.`).
3.	Click Submit to receive an encrypted response. The UI handles local decryption so you see plaintext.

**Note**:
- The Llama 3.2 encrypted tokenizer is on Hugging Face, but the model weights reside on Nesa’s secure server.
- Your user key stays with you, so we never see unencrypted data.


#### DistilBert Classification Mode
1.	Open the “Model” dropdown in the web UI and select DistilBert (Encrypted).
2.	Enter your text in the provided text box (for example, “I’m feeling great about Equivariant Encryption!”).
3.	Click Submit to see classification output.

**Note**:
- We have both the encrypted tokenizer and DistilBert weights locally.
- The entire inference pass is performed on encrypted tokens.
- Latency should be near-zero overhead.



## Troubleshooting
#### Installation fails:
 - Remove the installer_files folder (if it exists) and re-run the start script.
 - If the issue remains, please open an issue in this repository.


## License
The MIT License (MIT)

Copyright (c) 2024 Nesa

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
