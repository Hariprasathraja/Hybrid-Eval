from sentence_transformers import SentenceTransformer, util
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def semantic_similarity(text1, text2):
    emb1 = model.encode(text1, convert_to_tensor=True)
    emb2 = model.encode(text2, convert_to_tensor=True)
    return util.cos_sim(emb1, emb2).item()

def calculate_completeness_score(response):
    words = len(response.split())
    length_score = min(1.0, words / 50)
    sentences = [s.strip() for s in response.split('.') if s.strip()]
    complete_sentences = sum(1 for s in sentences if len(s.split()) >= 3)
    structure_score = min(1.0, complete_sentences / max(1, len(sentences)))
    unique_words = len(set(word.lower() for word in response.split()))
    density_score = min(1.0, unique_words / max(1, words) * 2)
    return (length_score * 0.4) + (structure_score * 0.3) + (density_score * 0.3)

def calculate_relevance_score(query, response):
    similarity = semantic_similarity(query, response)
    query_keywords = set([word.lower() for word in query.split() if len(word) > 3])
    response_words = [word.lower() for word in response.split()]
    keywords_found = sum(1 for k in query_keywords if any(k in r for r in response_words))
    keyword_coverage = keywords_found / len(query_keywords) if query_keywords else 0.5
    return (similarity * 0.7) + (keyword_coverage * 0.3)
