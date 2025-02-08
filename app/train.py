from datasets import load_dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    DataCollatorWithPadding,
    TrainingArguments,
    Trainer
)
import numpy as np
import evaluate
import torch
from transformers import pipeline

# Load IMDB dataset
dataset = load_dataset("imdb")

# No need for conversion since IMDB already uses 0 for negative and 1 for positive
# Create smaller datasets for faster training
small_train_dataset = dataset["train"].shuffle(seed=42).select([i for i in list(range(25000))])
small_test_dataset = dataset["test"].shuffle(seed=42).select([i for i in list(range(2500))])

# Initialize tokenizer
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

# Preprocess function
def preprocess_function(examples):
    return tokenizer(examples["text"], truncation=True)  # IMDB uses 'text' field

# Use the full dataset instead of creating smaller versions
tokenized_train = dataset["train"].map(preprocess_function, batched=True)
tokenized_test = dataset["test"].map(preprocess_function, batched=True)

# Create data collator
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# Initialize model with 2 labels
model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased", 
    num_labels=2,  # Changed to 2 for binary classification
    ignore_mismatched_sizes=True
)

# Define metrics function
def compute_metrics(eval_pred):
    accuracy_metric = evaluate.load("accuracy")
    f1_metric = evaluate.load("f1")
    
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    accuracy = accuracy_metric.compute(predictions=predictions, references=labels)["accuracy"]
    f1 = f1_metric.compute(predictions=predictions, references=labels, average='binary')["f1"]
    return {"accuracy": accuracy, "f1": f1}

# Modify training arguments for full dataset
training_args = TrainingArguments(
    output_dir="my-imdb-sentiment-model",
    learning_rate=2e-5,
    per_device_train_batch_size=8,  # Reduced batch size to handle memory better
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    save_strategy="epoch",
    push_to_hub=False,
    evaluation_strategy="epoch",
    logging_strategy="steps",
    logging_steps=500,          # Increased logging steps due to larger dataset
    gradient_accumulation_steps=4,  # Added to handle larger dataset
    fp16=True,  # Added for faster training if you have GPU support
)

# Initialize trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_test,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# Train the model
trainer.train()

# Evaluate the model
evaluation_results = trainer.evaluate()
print("\nEvaluation Results:", evaluation_results)

# Create sentiment analysis pipeline
sentiment_analyzer = pipeline(
    task="sentiment-analysis",
    model=model,
    tokenizer=tokenizer
)

# Function for sentiment analysis with confidence
def analyze_sentiment(texts):
    results = sentiment_analyzer(texts)
    for result in results:
        # Convert label to human-readable format
        if result['label'] == 'LABEL_1':
            result['label'] = 'POSITIVE'
        else:
            result['label'] = 'NEGATIVE'
            
        # Add confidence description
        if result['score'] > 0.9:
            result['confidence'] = 'Very High'
        elif result['score'] > 0.75:
            result['confidence'] = 'High'
        elif result['score'] > 0.6:
            result['confidence'] = 'Moderate'
        else:
            result['confidence'] = 'Low'
    return results

# Test with example reviews
example_texts = [
    "This movie was absolutely fantastic! The acting was great and the story was engaging throughout.",
    "What a terrible waste of time. The plot made no sense and the acting was horrible.",
    "One of the best films I've seen this year. Highly recommended!",
    "I couldn't even finish watching it. The worst movie ever.",
    "The special effects were amazing but the story was a bit weak.",
]

results = analyze_sentiment(example_texts)
print("\nTest Results:")
for text, result in zip(example_texts, results):
    print(f"\nText: {text}")
    print(f"Sentiment: {result['label']} (Confidence: {result['confidence']}, Score: {result['score']:.3f})")
