import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

model_name_or_path = 'ibm-granite/granite-guardian-hap-125m'
model = AutoModelForSequenceClassification.from_pretrained(model_name_or_path)
tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
model.to(device)

def invoke_hap(ip):
    if not isinstance(ip, list):
        ip = [ip]
    i = tokenizer(ip, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = model(**i).logits
        prediction = torch.argmax(logits, dim=1).cpu().detach().numpy().tolist() 
        probabilities = torch.softmax(logits, dim=1).cpu().detach().numpy()[:,1].tolist()
    return probabilities
