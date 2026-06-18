import json
import ollama
from cache_engine import AACPhraseCache
from fallback_engine import DeterministicFallbackEngine

# Initialize core system modules
cache = AACPhraseCache()
fallback_system = DeterministicFallbackEngine()

# seed basic context categories
cache.add_phrase("Hello! How are you?", "Greetings")
cache.add_phrase("Can we go outside?", "Activities")
cache.add_phrase("I need help", "Urgent")

def process_aac_intent(user_input_context: str) -> dict:
    """Processes system context via ultra-fast cahce or fallback LLM."""
    print(f"\n🔍 Processing context: '{user_input_context}'")

    # --- LEVEL 1: IMMEDIATE CRITICAL PHRASEBOOK MATCHING ---
    static_match = fallback_system.match_static_keywords(user_input_context)
    if static_match:
        print("Static Guardrail Hit! Immediate fallback response generated.")
        return {
            "predicted_phrase": static_match,
            "confidence_score": 1.0,
            "source": "static_emergency_phrasebook",
            "action_type": "speak"
        }
    
    # --- LEVEL 2: HIGH-SPEED VECTOR CACHE ---
    cached_match = cache.search_cache(user_input_context, distance_threshold=0.45)
    if cached_match:
        print("Cache Hit! Bypassed LLM inference entirely.")
        return {
            "predicted_phrase": cached_match["phrase"],
            "confidence_score": 1.0,
            "requires_action": True,
            "action_type": "speak"
        }
    
    # --- LEVEL 3: LOCAL LLM INFERENCE WITH PROTECTED WRAPPER ---
    print("Cache Miss. Running local Qen-1.5B quantized inference...")

    # Define system schema constraints
    aac_schema = {
        "type": "object",
        "properties": {
            "predicted_phrase": {"type": "string"},
            "confidence_score": {"type": "number"},
            "requires_action": {"type": "boolean"},
            "action_type": {"type": "string", "enum": ["speak", "navigation", "device_control", "none" ]}
        },
        "required": ["predicted_phrase", "confidence_score", "requires_action", "action_type"]
    }

    system_prompt = (
        "You are Otto, an assistive context engine. Predict the user's intended "
        "phrase based on current device and environment telemetry. "
        "You must respond ONLY with a JSON object matching the requested schema."
    )   
    try:
        # Request inference with a forced small prediction token allocation
        response = ollama.chat(
            model="qwen2.5:1.5b-instruct-q4_K_M",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Current Context: {user_input_context}"}
            ],
            # Forces grammar-constrained decoding at the engine level
            format=aac_schema,
            options={
                "temperature": 0.1, # Low temperature makes output more deterministic
                "num_predict": 128 # Cap output tokens to prevent long-winded answers
            }
        )
        output = json.loads(response['message']['content'])
        output["source"] = "local_llm_inference"
        return output
    
    except Exception as error:
        # LEVEL 4: CRASH/TIMEOUT PROTECTION
        print(f"Local LLM unavailable or timed out ({error}). Engaging prediction engine.")
        # Pass input context to extract word suggestions safely
        return fallback_system.execute_with_fallback(None, user_input_context)
    
if __name__ == "__main__":
    # Test 1: Immediate keyword trigger ("help")
    print("\n--- Running Test 1: Emergency Guardrail ---")
    result_1 = process_aac_intent("I need help right now")
    print(json.dumps(result_1, indent=2))
    
    # Test 2: Predictive word-level sequence
    print("\n--- Running Test 2: Dynamic Learning Trigger ---")
    result_2 = process_aac_intent("I go")
    print(json.dumps(result_2, indent=2))