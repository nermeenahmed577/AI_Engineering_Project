import time
import requests
import json
import pynvml

# Connect with Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# (NVIDIA Management Library)
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # first NVIDIA found

#Function that return VRAM usage in MB.
def get_vram_usage_mb():
    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle) 
    return mem_info.used / (1024 * 1024)

# function that generate a specific Tokens size  target_tokens =(1024,2048,4096,8192) .
def generate_prompt_of_length(target_tokens):
    base_text = "Explain what an Embedded system is in simple words."
    repetitions = (target_tokens * 4) // len(base_text) # integer Division .
    prompt = (base_text * repetitions) + "\n\nSummarize the above text briefly:" # model instruction 
    return prompt
# context_len =(1024,2048,4096,8192) .
def profile_context_length(context_len):
    print(f"\n--- Testing Context Length ~ {context_len} tokens ---")
    
    prompt = generate_prompt_of_length(context_len)
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_ctx": context_len + 512 
        }
    }
    
    vram_before = get_vram_usage_mb() #VRAM usage before being used .
    
    start_time = time.time()  # Time Before Start.
    first_token_time = None
    token_count = 0
    token_timestamps = []  # variable for each token recived time . 
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True) # Send request to Ollama.
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                current_time = time.time()
                
                # if it is (first token) save time 
                if first_token_time is None:
                    first_token_time = current_time
                
                token_timestamps.append(current_time) # add the time to the time array (token_timestamps).
                token_count += 1
                
                if chunk.get("done", False):
                    break

    # if any error happen during the model running    
    except Exception as e:
        print(f"Error during generation (Possibly OOM): {e}") # OOM -> Out of Memory 
        return None

    end_time = time.time()
    vram_after = get_vram_usage_mb()
    
    # TTFT Calculations
    if first_token_time:
        ttft = (first_token_time - start_time) * 1000 # Get the time in millisecond
        
    # (Inter-token latency) Calculation
    if len(token_timestamps) > 1:
        intervals = [token_timestamps[i] - token_timestamps[i-1] for i in range(1, len(token_timestamps))]
        avg_inter_token_latency = (sum(intervals) / len(intervals)) * 1000 

    print(f"Target Context: {context_len} tokens")
    print(f"TTFT (Time To First Token): {ttft:.2f} ms")
    print(f"Inter-token Latency (Avg): {avg_inter_token_latency:.2f} ms/token")
    print(f"Generated Tokens: {token_count}")
    print(f"VRAM Used Before: {vram_before:.2f} MB")
    print(f"VRAM Used After/Peak: {vram_after:.2f} MB")

context_lengths = [1024, 2048, 4096, 8192]

for ctx in context_lengths:
    profile_context_length(ctx)
    time.sleep(2) 
pynvml.nvmlShutdown()