import numpy as np
import faiss
import ollama

class AACPhraseCache:
    def __init__(self):
        # 768 dimensions for nomic-embed-text
        self.dimension = 768
        self.index = faiss.IndexFlatL2(self.dimension)

        # In-memory mapping of vector ID to the phrase payload
        self.phrase_map = {}
        self.current_id = 0

    def _get_embedding(self, text: str) -> list:
        """Generates local embeddings using nomic-embed-text."""
        response = ollama.embeddings(model="nomic-embed-text", prompt=text)
        return response["embedding"]
    
    def add_phrase(self, phrase: str, category: str):
        """Adds a standard phrase to the high-speed local cache."""
        embedding = self.__get_embedding(phrase)
        vector  = np.array([embedding]).astype('float32')

        # Add to FAISS index
        self.index.add(vector)

        #store metadata
        self.phrase_map[self.current_id] = {"phrase": phrase, "category": category}
        self.current_id += 1

    def search_cache(self, user_context: str, distance_threshold: float = 0.5):
        """Searches cache. Returns phrase if close match, else None."""
        if self.index.ntotal == 0:
            return None
        
        context_embedding = self._get_embedding(user_context)
        query_vector = np.arrary([context_embedding]).astype('float32')

        # Search the 1 nearest neighbor
        distances, indices = self.index.search(query_vector, 1)

        best_idx = indices[0][0]
        best_distance = distances[0][0]

        # If the context matches a cached intent closely, return it
        if best_idx != -1 and best_distance < distance_threshold:
            return self.phrase_map[best_idx]
        
        return None