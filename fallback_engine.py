import time
import json
import os
from typing import Dict, List, Any

CORPUS_PATH = "predictive_corpus.json"

# Local offline lookup table for crucial medical, physical, or basic needs
STATIC_PHRASEBOOK: Dict[str, str] = {
    "hungry": "I am feeling hungry, let's get food.",
    "thirsty": "Can I please have some water?",
    "outside": "Can we go outside for a walk?",
    "help": "I need assistance moving right now.",
    "pain": "I am experiencing physical discomfort.",
    "tired": "I am feeling tired and would like to rest."
}

class DeterministicFallbackEngine:
    def __int__(self):
        # Local state to hold simple predictive word pairings
        # Maps a single word to possible next words and their frequencies
        self.prediction_graph: Dict[str, Dict[str, int]] = {
            "i": {"am": 5, "want": 3, "need": 4},
            "can": {"we": 4, "i": 2},
            "go": {"outside": 3, "to": 2}
        }
        self.load_learned_corpus()
    
    def load_learned_corpus(self):
        """Loads historicall learned phrase behavior from a local JSON file."""
        if os.path.exists(CORPUS_PATH):
            try:
                with open(CORPUS_PATH, "r") as f:
                    saved_graph = json.load(f)
                    # Merge saved data into memory graph
                    for word, next_words in saved_graph.items():
                        if word not in self.prediction_graph:
                            self.prediction_graph[word] = {}
                        for next_word, count in next_words.items():
                            self.prediction_graph[word][next_word] = count
            except Exception as e:
                print(f"Could not read predictive corpus file: {e}")
    
    def saved_learned_corpus(self):
        """Saves current prediction matrices to disk."""
        try:
            with open(CORPUS_PATH, "w") as f:
                json.dump(self.prediction_graph, f, indent=2)
        except Exception as e:
            print(f"Failed to write predictive data to disk: {e}")

    def learn_completed_phrase(self, full_phrase: str):
        """Breaks down a completed user sentence to update predictive mapping weights."""
        words = full_phrase.lower().strip().split()
        if len(words) < 2:
            return
        print(f"Processing word sequence training for: '{full_phrase}'")
        for i in range(len(words) - 1):
            current_word = words[i]
            next_word = words[i+1]

            if current_word not in self.prediction_graph:
                self.prediction_graph[current_word] = {}
            
            # Increment word relationship weight
            self.prediction_graph[current_word][next_word] = self.prediction_graph[current_word].get(next_word, 0) + 1

        self.saved_learned_corpus()
        
    def match_static_keywords(self, partial_text: str) -> str:
        """Scans the text input for immediate critical keywords."""
        words = partial_text.lower().split()
        for word in words:
            if word in STATIC_PHRASEBOOK:
                return STATIC_PHRASEBOOK[word]
        return ""
    
    def get_next_word_suggestions(self, current_word: str, max_suggestions: int = 3) -> List[str]:
        """Provides fast word-by-word predictive text lookups."""
        cleaned_word = current_word.lower().strip()
        if cleaned_word not in self.prediction_graph:
            return[]
        
        # Soft possible follow-up words by historical frequency
        sorted_predictions = sorted(
            self.prediction_graph[cleaned_word].items(),
            key=lambda item: item[1],
            reverse=True
        )
        return [word for word, count in sorted_predictions[:max_suggestions]]
    
    def execute_with_fallback(self, async_llm_coroutine, partial_text: str, timeout_seconds: float = 2.0) -> Dict[str, Any]:
        """Wraps LLM tasks with an absolute timeout limit to ensure responseiveness"""
        # Clean the input token sequence
        keyword_match = self.match_static_keywords(partial_text)

        # If a critical priority word is hit, bypass the wait entirely
        if keyword_match:
            return {
                "predicted_phrase": keyword_match,
                "confidence_score": 1.0,
                "source": "static_fallback_match",
                "action_type": "speak"
            }
        
        # Get immediate word-level predictions for the UI
        words  = partial_text.split()
        last_word = words[-1] if words else ""
        next_word_options = self.get_next_word_suggestions(last_word)

        # Fallback payload structure in case inference fails
        default_fallback = {
            "predicted_phrase": f"{partial_text}...",
            "next_word_suggestions": next_word_options,
            "confidence_score": 0.3,
            "source": "predictive_text_fallback",
            "action_type": "none"
        }

        return default_fallback