"""
faq_matcher.py - Keyword-based Offline FAQ Matcher

Normalizes user input, scores candidate entries against trigger keywords,
and returns the highest-scoring matching answer. Returns None if no threshold is met.
"""

import os
import re
import json
from typing import Optional, Dict, Any, List

DATA_PATH = os.path.join(os.path.dirname(__file__), "faq_data.json")

def load_faq_dataset(path: str = DATA_PATH) -> List[Dict[str, Any]]:
    """Loads the FAQ dataset from JSON with graceful fallback."""
    if not os.path.exists(path):
        alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faq_data.json")
        if os.path.exists(alt_path):
            path = alt_path
        else:
            return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[FAQ Matcher] ⚠️ Error loading FAQ dataset: {e}")
        return []

def normalize_text(text: str) -> str:
    """Lowercases, removes excess punctuation, and normalizes whitespace."""
    if not text:
        return ""
    text = text.lower()
    # Replace punctuation with spaces
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple spaces
    return " ".join(text.split())

def match_faq(user_message: str, threshold: int = 1) -> Optional[str]:
    """
    Matches a user query against the FAQ dataset using normalized keyword scoring.
    
    Returns:
        The matched answer string if a matching rule crosses `threshold`,
        or None if no match is found.
    """
    norm_query = normalize_text(user_message)
    if not norm_query:
        return None

    dataset = load_faq_dataset()
    if not dataset:
        return None

    query_words = set(norm_query.split())

    best_score = 0
    best_answer = None

    for entry in dataset:
        keywords = entry.get("keywords", [])
        score = 0

        for kw in keywords:
            norm_kw = normalize_text(kw)
            if not norm_kw:
                continue
            
            # 1. Exact phrase match gives high boost
            if norm_kw in norm_query:
                # Longer matching phrases get higher priority
                score += len(norm_kw.split()) * 3
            else:
                # 2. Individual word overlap match
                kw_words = set(norm_kw.split())
                overlap = query_words.intersection(kw_words)
                if len(overlap) == len(kw_words):
                    score += len(overlap) * 2
                elif overlap:
                    score += len(overlap)

        if score > best_score:
            best_score = score
            best_answer = entry.get("answer")

    if best_score >= threshold:
        return best_answer

    return None

if __name__ == "__main__":
    # Quick CLI self-test
    test_queries = [
        "what are your opening hours on Friday?",
        "how can I change my password?",
        "do you have a money back guarantee if I cancel?",
        "can I speak with a human support agent?"
    ]
    for q in test_queries:
        ans = match_faq(q)
        print(f"Q: {q}\nA: {ans}\n")
