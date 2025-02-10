import time
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

def print_section(title):
    separator = "=" * (len(title) + 10)
    print(f"\n{separator}\n  {title}\n{separator}\n")

def main():
    """Note the comments show where each part of the code would run in a client-server architecture."""

    # ------------------------------------------
    # [Client]
    # ------------------------------------------
    user_input = input("Enter a sentence for sentiment analysis: ")

    print_section("[Client]")
    print("Client encrypts and tokenizes the input using the tokenizer/encryption key.")

    model_path = "./distilbert-sentiment-encrypted"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    encrypted_input = tokenizer(user_input, return_tensors="pt")

    time.sleep(3) # sleeping for readability

    # ------------------------------------------
    # [Server]
    # ------------------------------------------
    print_section("[Server]")
    print("Input received from client:")
    print(encrypted_input["input_ids"])

    print("\nRunning inference with the encrypted inputs and encrypted model...")
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    with torch.no_grad():
        logits = model(**encrypted_input).logits

    probs = torch.nn.functional.softmax(logits, dim=-1)[0]



    print("Produces encrypted output:")
    print(probs.tolist())
    print("\n[Note: The server has only ever seen the encrypted inputs and outputs. It does not have access to the decryption key.]")
    time.sleep(3)

    # ------------------------------------------
    # [Client]
    # ------------------------------------------
    print_section("[Client]")
    print("Client receives the encrypted output and decrypts it using the tokenizer/decryption key.")
    label_mapping = model.config.id2label
    result = {label_mapping[i]: float(prob) for i, prob in enumerate(probs)}

    print("\nresults:")
    for label, score in result.items():
        print(f"{label}: {score:.4f}")


if __name__ == "__main__":
    main()
