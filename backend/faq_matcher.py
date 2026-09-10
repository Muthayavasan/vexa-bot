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

# Common conversational stop words to prevent generic false positives
STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had", "can", "could", "would",
    "should", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "i", "me", "my", "we", "our", "you", "your", "it", "its", "this", "that"
}

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
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())

def match_faq(user_message: str, threshold: float = 2.0) -> Optional[str]:
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

    query_tokens = norm_query.split()
    query_content_words = set(w for w in query_tokens if w not in STOP_WORDS)
    if not query_content_words:
        query_content_words = set(query_tokens)

    best_score = 0.0
    best_answer = None

    for entry in dataset:
        keywords = entry.get("keywords", [])
        entry_best_score = 0.0

        for kw in keywords:
            norm_kw = normalize_text(kw)
            if not norm_kw:
                continue

            kw_tokens = norm_kw.split()
            kw_content_words = [w for w in kw_tokens if w not in STOP_WORDS]
            if not kw_content_words:
                kw_content_words = kw_tokens

            kw_score = 0.0

            # 1. Exact phrase substring match
            # e.g. "opening hours" in "what are your opening hours on Friday?"
            if norm_kw in norm_query:
                kw_score = 10.0 + len(kw_tokens) * 3.0
            else:
                # 2. Content word overlap (ignores filler stop words)
                matched_content = [w for w in kw_content_words if w in query_content_words]
                if len(matched_content) == len(kw_content_words):
                    # All significant content words matched!
                    kw_score = 7.0 + len(matched_content) * 2.0
                elif len(matched_content) > 0:
                    # Partial content word overlap
                    ratio = len(matched_content) / len(kw_content_words)
                    kw_score = len(matched_content) * 2.5 * ratio

            if kw_score > entry_best_score:
                entry_best_score = kw_score

        if entry_best_score > best_score:
            best_score = entry_best_score
            best_answer = entry.get("answer")

    if best_score >= threshold:
        return best_answer

    return None

if __name__ == "__main__":
    test_queries = [
        "what are your opening hours on Friday?",
        "how can I change my password?",
        "do you have a money back guarantee if I cancel?",
        "can I speak with a human support agent?",
        "how much does a subscription cost?",
        "what can you help me with?",
        "who are you?"
    ]
    for q in test_queries:
        ans = match_faq(q)
        print(f"Q: {q}\nA: {ans}\n")
