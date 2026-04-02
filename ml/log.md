# FinSight ML — Project Log

## 2026-03-31

### What I did
- Began Phase 1: fine-tuning DistilBERT for financial sentiment classification
- Discussed LoRA mechanics and why it reduces compute vs full fine-tuning
- Decided on training strategy: LoRA on attention layers, full training on classification head, everything else frozen
- Set up ml/log.md and ml/notes.md for documentation

### Decisions made
- Apply LoRA only to attention layers (not the classification head, which is randomly initialised and needs full training)
- Classification head trained fully because it has no pretrained knowledge to preserve

### Blockers / questions
- Still to answer: how to handle class imbalance, and which evaluation metric to use

## 2026-04-01

### What I did
- Opened Colab notebook: finsight_sentiment_training.ipynb (T4 GPU runtime)
- Installed dependencies: torch, numpy, transformers, peft, huggingface_hub, datasets, evaluate
- Loaded dataset: zeroshot/twitter-financial-news-sentiment
- Verified splits (train/validation) and features (text, label)
- Confirmed class distribution: negative=1442, positive=1923, neutral=6178 (matches CLAUDE.md)
- Computed class weights tensor and moved to GPU

### Decisions made
- Import specific classes per cell rather than importing whole libraries upfront
- Use `1 / counts` for class weights (ratios identical to `1 / frequencies`, PyTorch normalises internally)
- Use `torch.FloatTensor` for class weights, moved to GPU with `.to(device)`

### Blockers / questions
- Next: tokenise the dataset, load DistilBERT, apply LoRA via PEFT

## 2026-04-01 (continued)

### What I did
- Tokenised dataset using AutoTokenizer.from_pretrained("distilbert-base-uncased")
- Applied tokenizer to full dataset using .map(tokenize)
- Removed "text" column (strings cause batching errors in PyTorch)
- Set dataset format to PyTorch tensors with .set_format(type="torch")
- Verified output: input_ids, attention_mask, label all returned as tensors

### Decisions made
- max_length=128 (financial headlines are short, 512 would waste memory)
- padding="max_length" (simpler than dynamic padding for MVP; can optimise later with DataCollatorWithPadding)
- Left token_type_ids in (tensor-compatible, harmless, not worth removing)

### Blockers / questions
- Next: load DistilBERT and apply LoRA via PEFT

## 2026-04-01 (continued)

### What I did
- Loaded DistilBERT for sequence classification: AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=3)
- Moved model to GPU
- Applied LoRA via PEFT: LoraConfig with r=8, lora_alpha=16, target_modules=["q_lin", "v_lin"]
- Wrapped model with get_peft_model
- Verified: 740,355 trainable params out of 67,696,134 total (1.09%)

### Decisions made
- target_modules=["q_lin", "v_lin"] — attention layers only, not classification head
- r=8, lora_alpha=16 (alpha=2x rank is standard convention)
- Classification head remains fully trainable (randomly initialised, no pretrained knowledge)

### Blockers / questions
- Next: DataLoader and training loop

## 2026-04-01 (continued)

### What I did
- Created train and validation DataLoaders (batch_size=32, shuffle=True for train)
- Defined AdamW optimiser (lr=2e-5) and CrossEntropyLoss with class weights
- Wrote training loop with loss tracking and per-epoch average loss print
- Wrote validation loop with per-class F1 using evaluate library
- Ran 3 epochs of training

### Results
- Training loss: 0.591 → 0.575 → 0.557 (decreasing, model is learning)
- Per-class F1 after epoch 3: negative=0.642, positive=0.706, neutral=0.839
- Neutral performs best (most training examples), negative weakest (fewest examples)
- F1 plateaued across epochs despite loss still decreasing

### Decisions made
- batch_size=32 (standard default)
- lr=2e-5 (standard for transformer fine-tuning)
- 3 epochs starting point — can increase if needed
- Colab notebook not committed to git yet — will add to ml/ when complete

### Blockers / questions
- Validation loss not tracked — needed to properly diagnose overfitting vs plateau
- Next: add validation loss, consider more epochs or hyperparameter tuning, then push weights to HuggingFace Hub

## 2026-04-02

### What I did
- Added validation loss tracking to the training loop
- Added `transformers.set_seed(42)` for reproducibility (seeds DataLoader shuffle, LoRA adapter init, classification head init)
- Re-ran training for 3 epochs with full metrics

### Results
- Epoch 0: train loss 1.032, val loss 0.815, F1: [negative=0.517, positive=0.577, neutral=0.824]
- Epoch 1: train loss 0.742, val loss 0.588, F1: [negative=0.635, positive=0.638, neutral=0.852]
- Epoch 2: train loss 0.653, val loss 0.610, F1: [negative=0.613, positive=0.645, neutral=0.833]

### Decisions made
- Set epochs=2: validation loss increases at epoch 2 (0.588 → 0.610) while training loss continues to decrease — early overfitting signal; epoch 1 is the best checkpoint
- Did not implement early stopping — unnecessary for MVP when optimal epoch count is already known from results
- Pushed model and tokenizer to HuggingFace Hub: shakurahmad/finsight-distilbert
- Pushed tokenizer alongside model even though it is the default distilbert-base-uncased — keeps repo self-contained for runtime loading on EC2

### Phase 1 complete
- Weights live at: shakurahmad/finsight-distilbert
