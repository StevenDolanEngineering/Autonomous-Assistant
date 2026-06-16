import json
import ollama
from cache_engine import AACPhraseCache

# 1. Initialize and pre-populate the high-speed cache
cache = AACPhraseCache()
cache.add_phrase("Hello! How are you?", "Greetings")
cache.add_phrase("Can we go outside?", "Activities")
cache.add_phrase("I need help", "Urgent")

# 2. Define strict JSON output schema for the LLM fallback
# This forces the model to strictly follow this blueprint
AAC_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "predicted_phrase": {"type": "string"},
        "confidence_Score": {"type": "number"},
        "requires_action": {"type": "boolean"},
        "action_type": {"type": "string", "enum": ["speak", "navigation", "device_control", "none" ]}
    },
    "required": ["predicted_phrase", "confidence_score", "requires_action", "action_type"]
}

def process_aac_intent(user_input_context: str) -> dict:
    """Processes system context via ultra-fast cahce or fallback LLM."""
    print(f"\n🔍 Processing context: '{user_input_context}'")

    # --- PHASE 1: HIGH-SPEED VECTOR CACHE ---
    cached_match = cache.search_cache(user_input_context, distance_threshold=0.45)
    if cached_match:
        print("Cache Hit! Bypassed LLM inference entirely.")
        return {
            "predicted_phrase": cached_match["phrase"],
            "confidence_score": 1.0,
            "requires_action": True,
            "action_type": "speak"
        }
    
    # --- PHASE 2: OPTIMIZED LOCAL LLM FALLBACK ---
    print("Cache Miss. Running local Qen-1.5B quantized inference...")

    system_prompt = (
        "You are Otto, an assistive context engine. Predict the user's intended "
        "phrase based on current device and environment telemetry. "
        "You must respond ONLY with a JSON object matching the requested schema."
    )   

    response = ollama.chat(
        model="qwen2.5:1.5b-instruct-q4_K_M",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current Context: {user_input_context}"}
        ],
        # Forces grammar-constrained decoding at the engine level
        format=AAC_RESPONSE_SCHEMA,
        options={
            "temperature": 0.1, # Low temperature makes output more deterministic
            "num_predict": 128 # Cap output tokens to prevent long-winded answers
        }
    )

    # Because format=SCHEMA is set, this loading is guaranteed to be safe JSON
    return json.loads(response['message']['content'])