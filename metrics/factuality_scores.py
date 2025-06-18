from transformers import AutoModelForQuestionAnswering, AutoTokenizer
import torch

# Load QA model
model_name = "deepset/roberta-base-squad2"
model = AutoModelForQuestionAnswering.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def calculate_factuality_score(query, response):
    """
    Evaluate factuality of a response using a QA model.
    Returns a score between 0.0 and 1.0 indicating factual correctness.
    
    This works by treating the response as context and the query as a question,
    then checking if the model can extract a consistent answer from the response.
    """
    # Only evaluate factuality for informational/knowledge queries
    if not is_knowledge_query(query):
        return 0.5  # Neutral score for non-knowledge queries
    
    try:
        # Prepare input for the model
        inputs = tokenizer(query, response, return_tensors="pt", max_length=512, 
                          truncation=True, padding="max_length")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Get model predictions
        with torch.no_grad():
            outputs = model(**inputs)
            start_scores = outputs.start_logits
            end_scores = outputs.end_logits
            
            # Get the most likely answer span
            start_idx = torch.argmax(start_scores)
            end_idx = torch.argmax(end_scores)
            
            # Check if the answer span is valid
            if end_idx >= start_idx:
                # Calculate confidence score (normalized)
                confidence = torch.softmax(start_scores, dim=1).max().item() * \
                             torch.softmax(end_scores, dim=1).max().item()
                
                # Higher confidence = higher factuality score
                return min(1.0, confidence * 1.5)  # Scale up slightly but cap at 1.0
            else:
                return 0.3  # Low score for invalid spans
    
    except Exception as e:
        print(f"Error in factuality evaluation: {e}")
        return 0.4  # Default score on error

def is_knowledge_query(query):
    """
    Determine if a query is seeking factual/knowledge information.
    """
    knowledge_indicators = [
        "what", "who", "when", "where", "why", "how", "explain", 
        "tell me about", "information", "facts", "history", "define"
    ]
    
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in knowledge_indicators)