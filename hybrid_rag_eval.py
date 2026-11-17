import json
import requests
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import chromadb

# Load lightweight models locally
print("-> Loading models...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# Complete 30 Golden Test Cases
cases = [
    {
        "id": 1,
        "question": "What is an embedded system?",
        "reference": "An embedded system is a computer system designed to perform a specific task within a larger device."
    },
    {
        "id": 2,
        "question": "What is a microcontroller?",
        "reference": "A microcontroller is a small computer on a single chip that contains a CPU, memory, and peripherals."
    },
    {
        "id": 3,
        "question": "What is GPIO?",
        "reference": "GPIO stands for General Purpose Input Output. It allows a microcontroller to communicate with external devices."
    },
    {
        "id": 4,
        "question": "What is the purpose of the GPIO MODER register in STM32?",
        "reference": "MODER configures each GPIO pin as input, output, alternate function, or analog."
    },
    {
        "id": 5,
        "question": "What does the GPIO ODR register do?",
        "reference": "The Output Data Register controls the output state of GPIO pins."
    },
    {
        "id": 6,
        "question": "What is the purpose of the GPIO IDR register?",
        "reference": "The Input Data Register reads the logic levels present on GPIO pins."
    },
    {
        "id": 7,
        "question": "What is the purpose of the GPIO BSRR register?",
        "reference": "BSRR sets or resets individual GPIO output bits atomically."
    },
    {
        "id": 8,
        "question": "How do you set a GPIO pin using bit manipulation?",
        "reference": "Set a bit by using bitwise OR with a mask, such as register |= (1U << pin)."
    },
    {
        "id": 9,
        "question": "How do you clear a specific bit in a register?",
        "reference": "Clear a bit by ANDing the register with the inverted bit mask, such as register &= ~(1U << pin)."
    },
    {
        "id": 10,
        "question": "How do you toggle a specific bit?",
        "reference": "Toggle a bit using bitwise XOR with a mask, such as register ^= (1U << pin)."
    },
    {
        "id": 11,
        "question": "What is a pull-up resistor?",
        "reference": "A pull-up resistor connects an input signal to the supply voltage so the default input state is HIGH."
    },
    {
        "id": 12,
        "question": "What is a pull-down resistor?",
        "reference": "A pull-down resistor connects an input signal to ground so the default input state is LOW."
    },
    {
        "id": 13,
        "question": "What is a floating input pin?",
        "reference": "A floating input pin has no defined logic level and may read unpredictable HIGH or LOW values."
    },
    {
        "id": 14,
        "question": "What is the difference between input mode and output mode?",
        "reference": "Input mode allows a microcontroller to read an external signal, while output mode allows it to drive a signal."
    },
    {
        "id": 15,
        "question": "What is an open-drain output?",
        "reference": "An open-drain output can pull the signal LOW but needs a pull-up resistor to produce a HIGH level."
    },
    {
        "id": 16,
        "question": "What is a push-pull output?",
        "reference": "A push-pull output actively drives the pin both HIGH and LOW."
    },
    {
        "id": 17,
        "question": "Why should two push-pull outputs not be connected directly together?",
        "reference": "If they drive opposite logic levels, a large current may flow and cause excessive power dissipation or damage."
    },
    {
        "id": 18,
        "question": "What does RCC stand for in STM32?",
        "reference": "RCC stands for Reset and Clock Control. It manages clock configuration and peripheral clock enabling."
    },
    {
        "id": 19,
        "question": "Which register enables the GPIOA clock on STM32F401?",
        "reference": "The GPIOA clock is enabled by setting bit 0 in the RCC AHB1ENR register."
    },
    {
        "id": 20,
        "question": "Which register enables the GPIOB clock on STM32F401?",
        "reference": "The GPIOB clock is enabled by setting bit 1 in the RCC AHB1ENR register."
    },
    {
        "id": 21,
        "question": "What is a memory-mapped register?",
        "reference": "A memory-mapped register is a hardware register accessed through a specific memory address."
    },
    {
        "id": 22,
        "question": "What is a pointer in C?",
        "reference": "A pointer is a variable that stores the memory address of another variable or object."
    },
    {
        "id": 23,
        "question": "Why are volatile variables used when accessing hardware registers in C?",
        "reference": "Volatile tells the compiler that a value may change unexpectedly, so it must not optimize away required reads or writes."
    },
    {
        "id": 24,
        "question": "What is the function of a bit mask?",
        "reference": "A bit mask selects specific bits in a value so they can be tested or modified."
    },
    {
        "id": 25,
        "question": "What is a 7-segment display?",
        "reference": "A 7-segment display uses seven LED segments to display decimal digits."
    },
    {
        "id": 26,
        "question": "What is a common-anode 7-segment display?",
        "reference": "In a common-anode display, all LED anodes are connected together, and a segment turns on when its cathode is driven LOW."
    },
    {
        "id": 27,
        "question": "What is a common-cathode 7-segment display?",
        "reference": "In a common-cathode display, all LED cathodes are connected together, and a segment turns on when its anode is driven HIGH."
    },
    {
        "id": 28,
        "question": "Why is a current-limiting resistor used with an LED?",
        "reference": "A current-limiting resistor restricts the current through the LED and helps prevent damage."
    },
    {
        "id": 29,
        "question": "What is the difference between a microprocessor and a microcontroller?",
        "reference": "A microcontroller integrates a CPU, memory, and peripherals on one chip, while a microprocessor typically relies on external memory and peripherals."
    },
    {
        "id": 30,
        "question": "What is the purpose of a timer peripheral in a microcontroller?",
        "reference": "A timer peripheral measures time intervals and can generate delays, periodic events, or PWM signals."
    }
]

# Init The DataBase to store our output (ChromaDB).
client = chromadb.Client()
db = client.get_or_create_collection(name="embedded_kb_full") #return the collection if it exist , and if not creat it.

docs = [c["reference"] for c in cases] # all the ref of all the cases in one place.

ids = [str(c["id"]) for c in cases] # all the ids of all the cases in one place.

db.add(documents=docs, ids=ids) # add them to a Collection.

# We Have 2 ways to search :
# 1- Vector Search , 
# 2- Keywors Search (using BM25 "Best Matching 25"). 

 
# BM25 setup (For method 2)
tokenized = [doc.lower().split() for doc in docs]
bm25 = BM25Okapi(tokenized)

def hybrid_search(query, k=3):
    # 1 - Vector search
     #Send the Question to the DB to find the closest Vector Similarity.
    res = db.query(query_texts=[query], n_results=k)
    dense_hits = res["documents"][0]
    
    # 2- BM25 search
    q_tokens = query.lower().split()
    # Get the Score depend on the Similarity.
    # (The more the Score the better the Relation between the Q and The Answer).
    scores = bm25.get_scores(q_tokens)
    # get the index of the Similsr 3 Answers .
    top_bm25 = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    # now get the answer from the index.
    sparse_hits = [docs[i] for i in top_bm25]
    
    # Combine and remove duplicates while preserving order
    combined = dense_hits + sparse_hits
    return list(dict.fromkeys(combined))[:k]

def ask_ollama(prompt):
    r = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    })
    return r.json().get("response", "").strip()

def run_evaluation():
    print(f"\nRunning full Hybrid RAG evaluation on {len(cases)} test cases...\n")
    passed = 0
    
    for item in cases:
        qid = item["id"]
        q = item["question"]
        
        # 1. Retrieve
        retrieved = hybrid_search(q, k=3)
        if not retrieved:
            print(f"[Fail] Q{qid}: No documents retrieved")
            continue
            
        # 2. Rerank safely
        pairs = [[q, doc] for doc in retrieved] # Connect each Question With it's Refrance .
        scores = reranker.predict(pairs) # get the Relevance Score for each pair.
        ranked_pairs = sorted(zip(scores, retrieved), key=lambda x: x[0], reverse=True) # sort from High Simm to lower 
        ranked_docs = [doc for _, doc in ranked_pairs][:2] # choose Top 2.
        
        context = "\n".join(ranked_docs) # then send them to the Model.
        
        # 3. Generate answer using local LLM
        prompt = f"Context:\n{context}\n\nQuestion: {q}\nAnswer concisely based on the context:"
        ans = ask_ollama(prompt)
        
        # 4. Evaluate using LLM-as-a-Judge
        eval_prompt = f"""
        You are an evaluator. Check if the generated answer is factually consistent with the context.
        Context: {context}
        Answer: {ans}
        Does the answer match the facts in the context without major hallucinations? 
        Answer with YES or NO only.
        """
        verdict = ask_ollama(eval_prompt)
        
        is_ok = "yes" in verdict.lower()
        if is_ok:
            passed += 1
            print(f"[Pass] Q{qid}: {q}")
        else:
            print(f"[Fail] Q{qid}: {q} | Ans: {ans}")
            
    score = (passed / len(cases)) * 100
    print(f"\n==============================")
    print(f"Final Evaluation Score: {score:.1f}% ({passed}/{len(cases)})")
    print(f"==============================")

if __name__ == "__main__":
    run_evaluation()