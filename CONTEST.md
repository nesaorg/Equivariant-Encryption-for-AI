<img width="1870" alt="Hack_EE" src="https://github.com/user-attachments/assets/8b9e0eea-97a2-4a3e-b792-233aa0237137" />

# Nesa Hack EE" Contest

Successfully hack Nesa's EE technology and win **$100,000** and a **job offer at Nesa.** 

Grand Prize: **$100,000** ($50,000 USDT + $50,000 NES) to the person who hacks EE and provides the full prompt of the day, with code.

Runner-up Prize: **$1,000** (in USDT or NES) every day to the person who decrypts the most prompt (highest score).

Community Prize: **$1,000** (in NES) every day to the person who guesses the right word in the prompt. Must invite to be eligible!

Welcome to Nesa's "Hack EE" Competition. This event challenges participants to decode encrypted token mappings from a large language model that has been encrypted with Nesa's EE technology to preserve data privacy. Test your skill and try to extract the text from private token ids.

### Background:
At Nesa, privacy and security are essential goals. As part of our efforts toward universal private AI, we have developed **Equivariant Encryption**, a novel security method developed by Nesa in the spirit of Homomorphic Encryption, applying it to thousands of models, including Llama 3, Mistral, and BERT. To test the robustness of Nesa's approach for private AI, we invite you to attempt to recover original text from encrypted token ids.

In this challenge, we focus on our Llama 3 encryption. Our platform will provide prompts and responses as sequences of private token ids over HTTP. For a reference on tokenization, see the [Hugging Face documentation](https://huggingface.co/docs/transformers/en/main_classes/tokenizer).

Your objective is to “hack” the system by mapping these private token ids back to their original text tokens. Note that these ids are privatized; they do not directly match the standard Llama 3 tokenizer ids.

### The Challenge:
1. **Decode the Mystery:**
   * Each day, you will receive:
     * A set of encrypted token ids for a Llama model prompt.
     * A set of encrypted token ids for the model’s response to that prompt.
   * Your task is to decrypt these token ids into their original text tokens.

2. **Winning Criteria:**
   * Submit mappings on https://nesa.ai/contest in the form `{"tokens":{"12":"an","345":"swer","678":" he","90":"re"}}`
   * Your score depends on how many correct mappings you provide.

3. **Daily Prizes:**
   * We award a daily prize to the participant with the most accurate mappings.
   * Scoring:
     * +10 points for each correct mapping.
     * -1 point for each incorrect mapping.
   * In case of a tie, the earliest submission wins.

4. **Submission Rules:**
   * Only your first submission of the day is considered.
   * No additional submissions for that day will be evaluated, so choose carefully.
   * For help with tokenizers as well as example submission format see this notebook [here](https://github.com/nesaorg/Equivariant-Encryption-for-AI/blob/main/tokenizer_example.ipynb).
     
### Grand Prize:
Decode all provided tokens for a given day without any errors, and you win the grand prize. The competition ends once someone achieves this and provides reproducible code. Only one participant can claim the grand prize.

### Competition Flow:
1. **Morning Kickoff:**
   * Each day begins with a tweet linking to a data package.
   * The package includes:
     * The permuted tokenizer mapping (encrypted form).
     * The day’s prompt and output sequences in tokenized form.

2. **Submission Portal:**
   * Submit your `{"tokens":{"12":"an","345":"swer","678":" he","90":"re"}}` mappings, user ID, and timestamp through our secure portal.

3. **Daily Clues:**
   * We may release clues about certain tokens during the day.
   * After a clue is released, you can no longer earn points for correctly decoding those hinted tokens.
   * Submit early to maximize points.

4. **Bonus Points:**
   * After submitting, tweet at Nesa before 9pm EST, mentioning the rarest token (by frequency in that day’s data).
   * If you win the day and your rarest token guess is correct, you receive 50% more payout.
   * No tweet means no bonus.

5. **Live Updates:**
   * If feasible, we will post automated logs with submission timestamps.
   * A daily leaderboard on the portal shows your current standing.

6. **Day’s End:**
   * At the end of the next day, we announce the daily winner and share a leaderboard summary.

7. **Grand Finale:**
   * Perfectly decode all tokens on a given day and provide your code to earn the grand prize.
   * We will make a special announcement for your achievement, and the competition concludes.

### Why Participate?
* **Test Your Skills**: Apply decoding strategies and techniques to a very challenging problem.
* **Earn Prizes**: Receive daily rewards and aim for the grand prize. If you get it, we want you at Nesa.
* **Benchmark Your Approach**: Measure your methods against other competitors in the community.
* **Public Recognition**: Your username and score will be visible, giving you credit for your work.

### Important Notes:
* Any method is allowed-be creative.
* We will provide an example tokenizer and encrypted data pairs for practice, but this example will not match the secret tokenizer used in the challenge.
* Only the first submission you make each day is accepted.
* By participating, you agree to have your username and submissions displayed publicly to maintain transparency and excitement.
* We have made a short white paper outlining attack techniques that might be useful:
   https://github.com/nesaorg/Equivariant-Encryption-for-AI/blob/main/Attack_Paper.pdf
  
The tokens are waiting. Let the Decrypt-a-thon begin!
