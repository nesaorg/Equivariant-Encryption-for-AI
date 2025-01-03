<div align="center">

<!-- Logo with light mode support -->
<picture>
  <source media="(prefers-color-scheme: light)" srcset="docs/nesa-logo-light.png">
  <img alt="Nesa Logo" src="docs/nesa-logo.png" width="50%">
</picture>
<br>
<br>
<p>
Nesa: Run AI models end-to-end encrypted.
</p>

<h3 style="margin-top: 15px; margin-bottom: 15px; display: flex; justify-content: center; align-items: center; gap: 15px;">
  <a href="https://discord.gg/TK89MgJDkz" style="text-decoration: none;">
    <img alt="Discord" src="https://img.shields.io/badge/-Discord-7289DA?style=flat&logo=discord&logoColor=white"></a>
  <a href="https://x.com/nesaorg/" style="text-decoration: none;">
    <img alt="X" src="https://img.shields.io/twitter/follow/nesaorg?style=social">
  </a>
</h3>

<!-- GitHub Repo Stats -->
[![GitHub Repo stars](https://img.shields.io/github/stars/nesaorg/Equivariant-Encryption-for-AI)](https://github.com/nesaorg/Equivariant-Encryption-for-AI/stargazers)
[![GitHub Repo forks](https://img.shields.io/github/forks/nesaorg/Equivariant-Encryption-for-AI)](https://github.com/nesaorg/Equivariant-Encryption-for-AI/network/members)
[![GitHub followers](https://img.shields.io/github/followers/nesaorg?label=Follow)](https://github.com/nesaorg)
</div>

<!---
---
-->

Forget multi-million dollar on-prem infrastructure for AI, get the same privacy guarantees in an API: run AI like the biggest enterprises do.

Latest: Nesa now supports image and video models and RAG with end-to-end encryption.

## Features ##

### Full Privacy ###
nesa serves AI requests with zero visibility on underlying data and full blindness on query.

### Speedy ###
nesa delivers zero latency on encrypted inference (<0.1% original execution time).

### Wide Model Coverage ###
nesa supports encrypting Llama, Mistral, Stable Diffusion and thousands of other models.

### Cost Savings ###
nesa can deliver significant cost savings as an API vs. on-prem AI infrastructure.

### ChatGPT Compatible ###
nesa provides a ChatGPT-compatible API for running encrypted AI with a one line change.

### Quick Set-up ###
nesa is one click to install and go. See documentation.

## How Nesa Achieves Blind AI: Equivariant Encryption (EE) ##

At Nesa, privacy is a critical objective. On our path toward universal private AI, we confronted a key challenge: **how can we perform inference on neural networks without exposing the underlying input and output data to external parties, while returning requests without high latency?** Traditional approaches, such as differential privacy, ZKML or homomorphic encryption (HE), while conceptually strong, fall short in practical deployments for complex neural architectures. These methods struggle to handle non-linear operations efficiently, often imposing substantial computational overhead that makes them infeasible to integrate into real-time or large-scale systems.

Equivariant Encryption (EE) is a new security technology by Nesa, similar to Homomorphic Encryption (HE) in arithmetic-based privacy-preserving structure, but executed inside unique discrete architectures designed to provide complete inference encryption without additional latency.

The result is the first portable on-prem AI infrastructure solution inside of an API. Your cloud provider cannot see your data and queries with Nesa.

## Equivariant Encryption (EE) vs. Homomorphic Encryption (HE)

A snapshot of Equivariant Encryption's properties versus homomorphic encryption:

| **Feature** | **Equivariant Encryption (EE)** | **Homomorphic Encryption (HE)** |
| --- | --- | --- |
| Latency Overhead | Zero | Very High |
| Non-Linear Operations | Exact | Approximation Needed  |
| User Key Control | Direct & Custom | Schema-Defined  |
| Cryptographic Hardness | Massive Combinatorial Complexity | Standard Hardness Assumptions |

**Zero overhead:** Nesa's EE provides the same latency as plaintext inference, with no slowdowns.

**100k+ factorial:** Nesa's EE has a massive combinatorial complexity, contributing to the strongest security guarantees.

## Our Journey to Equivariant Encryption

We have implemented and investigated numerous methodologies that promise end-to-end data privacy. We began with deep orchestration work in **Trusted Execution Environments (TEE)** which is a hardware solution that decrypts, transforms, and re-encrypts data in secure memory. The issue with TEEs, besides cost and access, is that they still provide full back-door administrator access to your data, which for many enterprises and use cases is insufficient. **Differential privacy** seeks to obscure sensitive details by adding statistical noise, but it cannot fully prevent inference on raw data once it is processed by a model. **Homomorphic encryption**, on the other hand, is mathematically elegant: it permits computations directly on encrypted data. This is achieved through operations that are homomorphic to addition and multiplication, enabling algebraic manipulation of ciphertexts that, once decrypted, yield the correct plaintext results. Such a property is exceptionally appealing in scenarios like outsourced cloud computations, where one can perform inference off-site without revealing the sensitive inputs.

However, standard HE schemes are tailored around arithmetic operations. Neural networks, especially those with layers like attention mechanisms, activation functions, or normalization steps, do not map cleanly onto ring or field operations alone. Adapting HE to these complex transformations typically incurs prohibitive computational costs, slowing inference to impractical speeds.

Despite this, the conceptual promise of HE—running inference on encrypted data without decryption—prompted us to seek an alternative. We aimed to preserve the protective qualities of encrypted computation while working around the bottlenecks introduced by non-linear neural functions.

## Equivariant Encryption for Neural Networks

Our solution is **Equivariant Encryption (EE)**. The term **equivariance** signifies a change in representation that preserves the operational structure from the model’s perspective. In other words, we transform the input data into an encrypted domain where the neural network’s computations can be carried out as though it were processing plaintext, all while maintaining the secrecy of the underlying information.

<div align="center">
  <img src="docs/ee.png" alt="equivariant encryption diagram">
</div>

Rather than relying exclusively on arithmetic operations compatible with HE, EE integrates specialized transformations designed around the internal properties of neural networks. We exploit the known architecture, layer composition, and input-output mappings of the model to construct a system in which each step of inference operates correctly on encrypted inputs. This approach avoids expensive retraining on encrypted datasets. Instead, by following a set of mathematical guidelines, we can generate a new variant of the model that works with our encryption schema in a matter of seconds.

Formally, given some plaintext $p_i$, and some ciphertext $c_i$, with $p_i$ = decrypt($c_i$), our EE framework ensures that decrypt(nonlinear($c_1,c_2$)) = nonlinear($p_1,p_2$), where "nonlinear" represents a specific set of non-linear neural functions.

Crucially, the complexity of inference under EE does not surpass that of the unencrypted version. Each forward pass through the network involves approximately the same computational cost. Thus, **inference latency remains unchanged**, a significant advantage compared to conventional HE-based techniques.

To illustrate this with a tangible example, consider transformer-based models like ChatGPT, Claude, or Llama. These models employ tokenizers to convert text into discrete tokens, each mapped to an integer token ID. Under EE, we implement a specialized tokenizer that produces a different, encrypted set of token IDs. The network, now adapted to EE, treats these encrypted token IDs as standard inputs. It processes them identically to how it would process normal tokens, ultimately returning encrypted output tokens that can be decrypted locally by the user. The following diagram outlines this workflow:

<div align="center">
  <img src="docs/tokenizer.png" alt="tokenizer diagram">
</div>

In this setup, all data traveling over the network remains encrypted, and the transformations that produce and consume these tokens are carefully chosen to deny any straightforward method for recovering the plaintext. The attacker sees only encrypted tokens and a model variant designed to operate on that encrypted space, providing no direct, low-cost avenue to extract the original information.

## In-Depth Comparison: HE vs. EE

Below is a more detailed breakdown of how Equivariant Encryption matches or outperforms the expectations we have from traditional Homomorphic Encryption methods:

| Property | Homomorphic Encryption (HE) | Equivariant Encryption (EE) |
| --- | --- | --- |
| **Data Confidentiality (Server Blindness)** | The server never sees plaintext data. | The server never sees plaintext data. |
| **End-to-End Encrypted Computation** | Operations should be fully on encrypted data, with no intermediate decryptions. | EE models run directly on encrypted tokens. No intermediate decryptions are required. |
| **User-Controlled Encryption** | Users should hold keys and control encryption/decryption. | Only the user can map plaintext to transformed tokens using the EE tokenizer as a private key. |
| **Preservation of Accuracy** | The decrypted output should match the result of plaintext inference. | EE ensures final results are identical to plaintext inference outputs, with no accuracy loss. |
| **Support for Arbitrary Model Structures** | HE struggles with non-linearities and complex NN layers. | EE is designed for modern neural architectures and preserves non-linearities. |
| **Minimal Performance Overhead** | HE incurs large computational overhead. | EE imposes no overhead; inference latency matches that of the underlying model on plaintext data. |
| **No Approximation of Functions** | HE may require approximations of complex operations. | EE avoids approximations, preserving exact neural network functions post-transformation. |
| **Scalability to Large Models** | Handling large models under HE is impractical. | EE scales naturally with large models without any computational penalties. |
| **Compatibility with Existing Pipelines** | HE often requires extensive pipeline modifications. | EE requires a one-time transformation, after which pipelines operate as normal. |
| **Clear Security Model & Robustness** | HE has strong theoretical foundations. | EE provides a massively complex, secure combinatorial search space, making brute-force attacks impossible. |

## Attacks on EE Security

We have tested EE with various baseline attack vectors, which can be found here: https://github.com/nesaorg/nesa/blob/main/Attack_Paper.pdf

### LLM-as-a-Judge Attack

Using a state-of-the-art large language model such as GPT-4o to evaluate whether the output P(Oi) is a good answer to the prompt P(Ii).

### Linguistic Domain Knowledge Attack

Using domain knowledge to design the loss function L, so that the loss L can capture the semantic meaning in the (decrypted) input, output and between.

### Brute-force Algorithm Attack

The most naive method is brute force, trying all possible permutations P and choosing the one with the minimal loss value. This algorithm requires time complexity of N!, which is infeasible.

### Random Sampling Attack

Randomly sampling M permutations and choosing the one with the lowest loss value. One can also try genetic algorithms to mix and cross-over multiple tries at different permutations.

### Hill-climbing Algorithm Attack

Starting with an arbitrary initial permutation P. The set of moves is the set of permutations that one can reach by transposing two elements of the permutation.

## Try EE for Yourself

### Nesa Demo on Hugging Face (Distilbert)

We provide a [community encrypted model](https://huggingface.co/nesaorg/distilbert-sentiment-encrypted) on Hugging Face to demonstrate how Equivariant Encryption works.

#### Loading the Model

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Initialize model and tokenizer
model_name = "nesaorg/distilbert-sentiment-encrypted-community-v1"
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
tokenizer = AutoTokenizer.from_pretrained(model_name)
```

#### Running Inference

```python
# Prepare input and run inference
inputs = tokenizer("Hello, I love you", return_tensors="pt")

with torch.no_grad():
    logits = model(**inputs).logits

# Process results
predicted_class_id = logits.argmax().item()
label = model.config.id2label[predicted_class_id]
score = torch.max(torch.nn.Softmax()(logits)).item()

print(f"The sentiment was classified as {label} with a confidence score of {score:.2f}")
```

<!-- ### Nesa Demo on Github (Llama) -->

## The "Hack EE" Contest
<img width="1870" alt="Hack_EE" src="https://github.com/user-attachments/assets/7f3b1150-41c7-442f-bc74-5abf0685c00b" />
&nbsp;
&nbsp;

We invite the community to examine and test the security claims of Equivariant Encryption. As part of our commitment to transparency and continual refinement, we have organized a competition encouraging participants to probe for weaknesses and demonstrate potential exploits.

For details, please visit:
[https://github.com/nesaorg/Equivariant-Encryption-for-AI/blob/main/CONTEST.md](https://github.com/nesaorg/Equivariant-Encryption-for-AI/blob/main/CONTEST.md)
