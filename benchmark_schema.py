import json
import time
import requests
from pydantic import BaseModel, Field

# Connect with Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# Schema Definition
class EmbeddedConceptSchema(BaseModel):
    concept_name: str = Field(description="Name of the embedded systems concept, e.g., GPIO, ODR, Microcontroller")
    definition: str = Field(description="Concise definition of the concept")
    key_registers_or_terms: list[str] = Field(description="List of related technical terms or registers")
    difficulty_level: str = Field(description="Estimated difficulty: Beginner, Intermediate, or Advanced")

# Test Prompt
test_prompt = "Explain what the STM32 GPIO ODR register does and how it controls pin states."

# ----------------------------------------------Methode 1 ---------------------------------------------------
def benchmark_constrained_generation():
    """
       Methode 1 ----> Grammar-Guided / Structured JSON Mode
    """
    json_schema = EmbeddedConceptSchema.model_json_schema() # Change the Schema to JSON Form For Ollama.
    
    # Python Dictionary
    payload = {
        "model": MODEL_NAME,
        "prompt": f"Extract structured information based on this schema from the text: '{test_prompt}'", #Instructions For the Model 
        "format": json_schema, # B2ol LL Model Yltzm Bal Schema .
        "stream": False,
        "options": {"temperature": 0.1} 
        # the Temperature affect the Model randomness at choosing the Output Tokens.(Low Temp == Low Randomness).
    }
    # Start the Time.
    start_time = time.time()
    response = requests.post(OLLAMA_URL, json=payload) #Send to Ollama the Request .
    end_time = time.time() #End the Time.

    # (1) Calculate the Time Taken ----> (Latency)
    elapsed_time = end_time - start_time 
    result_data = response.json() # Change the HTTP response to Python Dictionary.
    response_text = result_data.get("response", "{}")
    eval_count = result_data.get("eval_count", 0) # The number of Generated Tokens For the Output.
    
    # (2) Calculating the Throughput (tokens/sec)
    throughput = eval_count / elapsed_time if elapsed_time > 0 else 0
    
    # (3) Check that the output Match the schema
    try:
        parsed_json = json.loads(response_text) #Check for Syntax Error.
        validated_obj = EmbeddedConceptSchema(**parsed_json) # Check that all the required key_registers_or_terms are in the output .
        is_valid = True
    except Exception as e:
        is_valid = False
        
    return {
        "method": "Grammar-Guided (Ollama JSON Mode)",
        "time_sec": elapsed_time,
        "tokens": eval_count,
        "throughput_tps": throughput,
        "valid_json": is_valid
    }
# ---------------------------------------------- Methode 2 ---------------------------------------------------

def benchmark_unconstrained_with_retries(max_retries=3):
    """
      Methode 2 ----> (Unconstrained) JSON
    """
    prompt = f"""
    Extract structured information from the text: '{test_prompt}'
    You MUST output ONLY a valid JSON object matching this schema structure:
    {json.dumps(EmbeddedConceptSchema.model_json_schema(), indent=2)}
    Do not include any extra text or markdown formatting.
    """
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }
    
    total_tokens = 0
    start_time = time.time()

    # the Loop that is responseable for repeating this steps for 3 times .
    for attempt in range(max_retries):
        response = requests.post(OLLAMA_URL, json=payload)
        res_json = response.json()
        response_text = res_json.get("response", "")
        total_tokens += res_json.get("eval_count", 0) 
        
        try:
            # Clean the Text from any Spaces or Markdown .
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_text)
            EmbeddedConceptSchema(**parsed) # Check that all the required key_registers_or_terms are in the output .
            
            end_time = time.time()
            # Calculate the Time Taken
            elapsed_time = end_time - start_time
            # (2) Calculating the Throughput (tokens/sec)
            throughput = total_tokens / elapsed_time if elapsed_time > 0 else 0
            
            return {
                "method": f"Unconstrained + Retries (Attempt {attempt+1})", # Attempt--> de 2al mo7awla 2al kam
                "time_sec": elapsed_time,
                "tokens": total_tokens,
                "throughput_tps": throughput,
                "valid_json": True
            }
        except Exception:
            continue # repeate in case it fail.
    # (3) Check that the output Match the schema
    end_time = time.time()
    elapsed_time = end_time - start_time
    return {
        "method": "Unconstrained + Retries (Failed after max retries)",
        "time_sec": elapsed_time,
        "tokens": total_tokens,
        "throughput_tps": 0,
        "valid_json": False
    }

if __name__ == "__main__":
    print("Running Milestone 3 Benchmarks...\n")
    
    print("1. Testing Grammar-Guided FSM Decoding (Ollama JSON Schema)...")
    res1 = benchmark_constrained_generation()
    print(json.dumps(res1, indent=4))
    
    print("\n2. Testing Unconstrained Sampling with Retries...")
    res2 = benchmark_unconstrained_with_retries()
    print(json.dumps(res2, indent=4))
    
    print("\n--- Benchmark Summary ---")
    print(f"Grammar-Guided Valid JSON: {res1['valid_json']} | Throughput: {res1['throughput_tps']:.2f} tok/s")
    print(f"Unconstrained Retries Valid JSON: {res2['valid_json']} | Throughput: {res2['throughput_tps']:.2f} tok/s")