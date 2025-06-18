import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Detect device
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Load IBM Granite HAP model
model_name_or_path = 'ibm-granite/granite-guardian-hap-125m'
model = AutoModelForSequenceClassification.from_pretrained(model_name_or_path)
tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
model.to(device)

def invoke_hap(texts, threshold=0.5):
    """
    Evaluate harmfulness using Granite HAP model.

    Returns:
        List[Dict] → Each dict contains:
        {
            "score": float,
            "unsafe": bool
        }
    """
    if not isinstance(texts, list):
        texts = [texts]

    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(device)
    
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=1).cpu().numpy()[:, 1]  # class 1 = harmful

    results = []
    for score in probs:
        results.append({
            "score": round(float(score), 6),
            "unsafe": bool(score > threshold)
        })

    return results
