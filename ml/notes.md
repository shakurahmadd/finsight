# FinSight ML — Notes

## LoRA (Low-Rank Adaptation)

### Key Concepts
- Instead of updating a weight matrix W directly, LoRA learns two small matrices A and B where the update is A × B
- If W is 768×768 (589K params), and A is 768×r and B is r×768, you only train 2×768×r params
- At rank r=8: 12,288 params vs 589,824 — ~48x fewer
- Original weights are frozen; only A and B are trained

### Config Decisions
- `r` (rank): controls expressiveness vs parameter count. r=8 is a common default
- `lora_alpha`: scaling factor applied to the LoRA update
- `target_modules`: which weight matrices to apply LoRA to — attention layers for DistilBERT

### Watch-outs
- Don't apply LoRA to the classification head — it's randomly initialised, so there's no pretrained knowledge to preserve. Train it fully instead.
- Higher rank = more params = more expressive but closer to full fine-tuning cost

## Training Loop

### Key Concepts
- DataLoader batches the dataset and shuffles training data each epoch
- Training step order: zero gradients → forward pass → compute loss → backward pass → update weights
- PyTorch accumulates gradients by default — must zero them each step or gradients from previous batches corrupt updates
- `loss.item()` extracts scalar from tensor — use this when accumulating loss, not `loss` itself (prevents GPU memory leak)
- Model and input tensors must be on the same device — always call `.to(device)` on batches

### Validation
- `peft_model.eval()` disables dropout for deterministic inference
- `torch.no_grad()` disables gradient tracking — saves memory and prevents accidental graph corruption
- HuggingFace model returns a `SequenceClassifierOutput` object — access logits via `output.logits`
- Convert logits to predicted class: `torch.argmax(output.logits, dim=1)` — argmax of logits == argmax of softmax probabilities
- `evaluate.load("f1")` with `add_batch()` accumulates predictions across batches, then `compute(average=None)` gives per-class F1

### Watch-outs
- Reset `metric = evaluate.load("f1")` each epoch — otherwise predictions accumulate across epochs
- F1 plateauing while training loss still drops may indicate overfitting — track validation loss to confirm
- Neutral class will always score highest due to class imbalance — per-class F1 is essential to see the full picture

## Loading a Model & Applying LoRA

### Key Concepts
- `AutoModelFor<Task>` — HuggingFace pattern for task-specific model heads
- `SequenceClassification` = one label per sequence; `TokenClassification` = one label per token
- UNEXPECTED weights in loading warning = pretrained MLM head (vocab_transform etc.) — not needed for classification, safe to ignore
- MISSING weights = newly initialised classification head — expected, needs training

### LoRA Config
- `r=8`: rank of the low-rank matrices — controls expressiveness vs parameter count
- `lora_alpha=16`: scaling factor for LoRA update, applied as `lora_alpha/r`. Convention: set to 2x rank
- `target_modules=["q_lin", "v_lin"]`: DistilBERT's attention projection layers
- `task_type=TaskType.SEQ_CLS`: tells PEFT this is a sequence classification task
- Do NOT use `"all-linear"` — it includes the classification head which should be fully trained, not LoRA-adapted

### Watch-outs
- Only the tokeniser is pure Python — it stays on CPU. Only the model needs `.to(device)`
- `peft_model.print_trainable_parameters()` shows trainable vs frozen param counts — use to verify LoRA is applied correctly
- Trainable % should be small (~1%) — if it's large, LoRA may be applied to too many layers

## Evaluation & Class Imbalance

### Key Concepts
- **Accuracy** is unreliable under class imbalance — a model that always predicts neutral would score ~65% without learning anything useful
- **Precision**: of all the times the model predicted a label, what % was correct
- **Recall**: of all the actual instances of a label, what % did the model find
- **F1**: harmonic mean of precision and recall. Harmonic mean punishes imbalance — a model with precision=1.0 and recall=0.0 gets F1=0, not 0.5
- **Per-class F1**: report F1 separately for each class (negative, positive, neutral)

### Why per-class F1
- Averaging into one score lets the dominant class (neutral, 65%) mask poor performance on rare classes
- Negative sentiment (15%) is the most actionable signal for financial research — we need to know explicitly if the model is missing it
- Per-class F1 gives an honest breakdown: strong on neutral, weak on negative = a model that needs more work

### Config Decisions
- Use weighted loss during training to compensate for class imbalance
- Evaluate with per-class F1, not overall accuracy or macro F1 alone

## Tokenisation

### Key Concepts
- Tokeniser converts raw text to token IDs and attention masks — DistilBERT cannot take raw text
- `AutoTokenizer.from_pretrained("distilbert-base-uncased")` loads the matching tokeniser
- `input_ids`: integer token IDs the model reads
- `attention_mask`: 1 for real tokens, 0 for padding — tells model to ignore padding positions
- `token_type_ids`: used for sentence-pair tasks, not needed for classification but harmless

### Config Decisions
- `padding="max_length"`: pads every sequence to exactly max_length tokens
- `max_length=128`: safe upper bound for financial headlines without wasting memory
- `truncation=True`: truncates anything longer than max_length

### Watch-outs
- String columns (like `text`) must be removed before batching — PyTorch cannot collate them into tensors
- `.remove_columns()` returns a new dataset (not inplace) — reassign the result
- `.set_format(type="torch")` is inplace — no need to reassign
- Dynamic padding is more memory efficient but requires `DataCollatorWithPadding` at the DataLoader level, not inside `.map()`

### Weighted Loss
- Formula: `weight = 1 / class_frequency`
- negative: 1/0.15 = 6.67, positive: 1/0.20 = 5.00, neutral: 1/0.65 = 1.54
- Ratios are what matter — PyTorch normalises internally
- Intuition: if a class appears half as often, each mistake on it should cost twice as much so it contributes equally to total loss
- In PyTorch: `nn.CrossEntropyLoss(weight=class_weights)` where class_weights is a tensor of [neg_w, pos_w, neu_w]
