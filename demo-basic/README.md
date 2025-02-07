# Demo Basic: Equivariant Encryption (EE) with DistilBERT

## Overview
This demo contains a minimal script that demonstrates how **Nesa’s Equivariant Encryption (EE)** works with an encrypted version of DistilBERT for sentiment classification.  The goal is to illustrate the practical advantages of Equivariant Encryption (EE) in securing AI model inference without sacrificing performance.

In this demo, you will see that:
- **Client-Side Privacy:** The user’s plaintext input is only visible on the client.
- **Encrypted Tokenization:** The input is tokenized into encrypted tokens. **Only someone with the correct tokenizer (i.e. the decryption key) can recover the original text.**
- **Server-Side Inference:** The server receives only encrypted tokens, runs inference, and returns the logits, or encrypted tokens depending on the model.
- **Client-Side Decryption:** The client then decrypts the server’s response (if in generation mode) to reveal the final, human-readable result.

## Script Overview
The demo script (`demo.py`) follows these steps:

1. **User Input (Client):**
   The user enters a sentence. This plaintext is processed **locally only**.

2. **Tokenization & Encryption (Client):**
   The encrypted tokenizer converts the plaintext into encrypted token IDs.
   *Significance:* Only the client has access to the decryption key. The resulting token IDs are sent to the server—without revealing the original text.

3. **Inference on Encrypted Tokens (Server Simulation):**
   The server loads the encrypted model and performs inference on the encrypted token IDs.
   *Significance:* The server sees **only** the encrypted tokens and never the underlying plaintext.

4. **Encrypted Output Returned (Server → Client):**
   The model produces an encrypted output (e.g., logits or token IDs) as the result of inference.

5. **Decryption & Display (Client):**
   The client uses the same tokenizer (with the decryption key) to convert the encrypted output back into a human-readable result (e.g., sentiment scores).
   *Significance:* Only a user with the correct tokenizer can decrypt and see the final output.

## Prerequisites

- **Python 3.9+**
- **PyTorch**
- **Transformers** library

## Installation

```bash
pip install torch transformers
```


## Running the Demo
1.	Clone or download this repository and navigate to the /demo-basic/ directory.
2.	Ensure that the encrypted model is present in ./distilbert-sentiment-encrypted/.
3.	Run the demo script:
```bash
    python demo.py
```
4.	Follow the prompt to enter your sentence for sentiment analysis.


## Key Points
- End-to-End Encryption: The entire process—from tokenization to inference and decryption—is designed so that only the client ever handles plaintext data.
- Server Blindness: The server processes only encrypted tokens; it does not have access to the underlying sensitive data.
- Client-Controlled Decryption: Only a client with the correct tokenizer (and thus the decryption key) can recover the original text and results.
