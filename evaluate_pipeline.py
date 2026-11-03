import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# 30 Golden Test Cases.
golden_cases = [
    {
        "id": 1,
        "question": "What is an embedded system?",
        "reference": "An embedded system is a computer system designed to perform a specific task within a larger device.",
        "required_concepts": [["computer", "computing system"], ["specific task"], ["device", "larger system"]] 
    },
    {
        "id": 2,
        "question": "What is a microcontroller?",
        "reference": "A microcontroller is a small computer on a single chip that contains a CPU, memory, and peripherals.",
        "required_concepts": [["single chip", "chip"], ["cpu", "processor"], ["memory"], ["peripherals", "input output"]]
    },
    {
        "id": 3,
        "question": "What is GPIO?",
        "reference": "GPIO stands for General Purpose Input Output. It allows a microcontroller to communicate with external devices.",
        "required_concepts": [["general purpose input output", "gpio"], ["input"], ["output"], ["external devices", "peripherals"]]
    },
    {
        "id": 4,
        "question": "What is the purpose of the GPIO MODER register in STM32?",
        "reference": "MODER configures each GPIO pin as input, output, alternate function, or analog.",
        "required_concepts": [["configures", "sets"], ["input"], ["output"], ["alternate function"], ["analog"]]
    },
    {
        "id": 5,
        "question": "What does the GPIO ODR register do?",
        "reference": "The Output Data Register controls the output state of GPIO pins.",
        "required_concepts": [["output data register", "odr"], ["output state", "output value"], ["gpio", "pin"]]
    },
    {
        "id": 6,
        "question": "What is the purpose of the GPIO IDR register?",
        "reference": "The Input Data Register reads the logic levels present on GPIO pins.",
        "required_concepts": [["input data register", "idr"], ["read", "reads"], ["logic level", "input state"], ["pin", "gpio"]]
    },
    {
        "id": 7,
        "question": "What is the purpose of the GPIO BSRR register?",
        "reference": "BSRR sets or resets individual GPIO output bits atomically.",
        "required_concepts": [["bsrr"], ["set"], ["reset"], ["atomic", "independent"]]
    },
    {
        "id": 8,
        "question": "How do you set a GPIO pin using bit manipulation?",
        "reference": "Set a bit by using bitwise OR with a mask, such as register |= (1U << pin).",
        "required_concepts": [["bitwise or", "|="], ["shift", "<<"], ["mask", "bit"]]
    },
    {
        "id": 9,
        "question": "How do you clear a specific bit in a register?",
        "reference": "Clear a bit by ANDing the register with the inverted bit mask, such as register &= ~(1U << pin).",
        "required_concepts": [["and", "&="], ["not", "~"], ["mask", "bit"], ["clear", "zero"]]
    },
    {
        "id": 10,
        "question": "How do you toggle a specific bit?",
        "reference": "Toggle a bit using bitwise XOR with a mask, such as register ^= (1U << pin).",
        "required_concepts": [["xor", "^="], ["toggle", "invert"], ["mask", "bit"]]
    },
    {
        "id": 11,
        "question": "What is a pull-up resistor?",
        "reference": "A pull-up resistor connects an input signal to the supply voltage so the default input state is HIGH.",
        "required_concepts": [["resistor"], ["supply voltage", "vcc"], ["high"], ["default", "input"]]
    },
    {
        "id": 12,
        "question": "What is a pull-down resistor?",
        "reference": "A pull-down resistor connects an input signal to ground so the default input state is LOW.",
        "required_concepts": [["resistor"], ["ground", "gnd"], ["low"], ["default", "input"]]
    },
    {
        "id": 13,
        "question": "What is a floating input pin?",
        "reference": "A floating input pin has no defined logic level and may read unpredictable HIGH or LOW values.",
        "required_concepts": [["no defined", "undefined"], ["unpredictable", "random"], ["high"], ["low"]]
    },
    {
        "id": 14,
        "question": "What is the difference between input mode and output mode?",
        "reference": "Input mode allows a microcontroller to read an external signal, while output mode allows it to drive a signal.",
        "required_concepts": [["input", "read"], ["external signal"], ["output", "drive"], ["signal"]]
    },
    {
        "id": 15,
        "question": "What is an open-drain output?",
        "reference": "An open-drain output can pull the signal LOW but needs a pull-up resistor to produce a HIGH level.",
        "required_concepts": [["open drain"], ["low"], ["pull-up resistor"], ["high"]]
    },
    {
        "id": 16,
        "question": "What is a push-pull output?",
        "reference": "A push-pull output actively drives the pin both HIGH and LOW.",
        "required_concepts": [["push-pull"], ["high"], ["low"], ["drives", "drive"]]
    },
    {
        "id": 17,
        "question": "Why should two push-pull outputs not be connected directly together?",
        "reference": "If they drive opposite logic levels, a large current may flow and cause excessive power dissipation or damage.",
        "required_concepts": [["opposite", "different"], ["high"], ["low"], ["current"], ["damage", "short circuit"]]
    },
    {
        "id": 18,
        "question": "What does RCC stand for in STM32?",
        "reference": "RCC stands for Reset and Clock Control. It manages clock configuration and peripheral clock enabling.",
        "required_concepts": [["reset and clock control"], ["clock"], ["peripheral"]]
    },
    {
        "id": 19,
        "question": "Which register enables the GPIOA clock on STM32F401?",
        "reference": "The GPIOA clock is enabled by setting bit 0 in the RCC AHB1ENR register.",
        "required_concepts": [["ahb1enr"], ["rcc"], ["gpioa"], ["bit 0", "bit zero"]]
    },
    {
        "id": 20,
        "question": "Which register enables the GPIOB clock on STM32F401?",
        "reference": "The GPIOB clock is enabled by setting bit 1 in the RCC AHB1ENR register.",
        "required_concepts": [["ahb1enr"], ["rcc"], ["gpiob"], ["bit 1", "bit one"]]
    },
    {
        "id": 21,
        "question": "What is a memory-mapped register?",
        "reference": "A memory-mapped register is a hardware register accessed through a specific memory address.",
        "required_concepts": [["hardware register"], ["memory address"], ["accessed", "mapped"]]
    },
    {
        "id": 22,
        "question": "What is a pointer in C?",
        "reference": "A pointer is a variable that stores the memory address of another variable or object.",
        "required_concepts": [["variable"], ["memory address"], ["stores", "holds"]]
    },
    {
        "id": 23,
        "question": "Why are volatile variables used when accessing hardware registers in C?",
        "reference": "Volatile tells the compiler that a value may change unexpectedly, so it must not optimize away required reads or writes.",
        "required_concepts": [["volatile"], ["compiler"], ["change", "unexpected"], ["optimization", "optimize"], ["read", "write"]]
    },
    {
        "id": 24,
        "question": "What is the function of a bit mask?",
        "reference": "A bit mask selects specific bits in a value so they can be tested or modified.",
        "required_concepts": [["mask"], ["select", "specific"], ["bits"], ["modify", "test"]]
    },
    {
        "id": 25,
        "question": "What is a 7-segment display?",
        "reference": "A 7-segment display uses seven LED segments to display decimal digits.",
        "required_concepts": [["seven", "7"], ["segments"], ["led"], ["digits", "numbers"]]
    },
    {
        "id": 26,
        "question": "What is a common-anode 7-segment display?",
        "reference": "In a common-anode display, all LED anodes are connected together, and a segment turns on when its cathode is driven LOW.",
        "required_concepts": [["common anode"], ["anodes"], ["connected together"], ["low"], ["cathode"]]
    },
    {
        "id": 27,
        "question": "What is a common-cathode 7-segment display?",
        "reference": "In a common-cathode display, all LED cathodes are connected together, and a segment turns on when its anode is driven HIGH.",
        "required_concepts": [["common cathode"], ["cathodes"], ["connected together"], ["high"], ["anode"]]
    },
    {
        "id": 28,
        "question": "Why is a current-limiting resistor used with an LED?",
        "reference": "A current-limiting resistor restricts the current through the LED and helps prevent damage.",
        "required_concepts": [["resistor"], ["limits", "restricts"], ["current"], ["led"], ["damage", "protect"]]
    },
    {
        "id": 29,
        "question": "What is the difference between a microprocessor and a microcontroller?",
        "reference": "A microcontroller integrates a CPU, memory, and peripherals on one chip, while a microprocessor typically relies on external memory and peripherals.",
        "required_concepts": [["cpu", "processor"], ["memory"], ["peripherals"], ["one chip", "single chip"], ["external"]]
    },
    {
        "id": 30,
        "question": "What is the purpose of a timer peripheral in a microcontroller?",
        "reference": "A timer peripheral measures time intervals and can generate delays, periodic events, or PWM signals.",
        "required_concepts": [["timer"], ["time interval", "time"], ["delay"], ["periodic", "pwm"]]
    }
]

def call_llm(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False, # we need the final answer to evaluate it
        "options": {"temperature": 0.1}
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload) # Send request to Ollama.
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"Error: {e}"

def llm_as_a_judge(question, reference, generated_output):
    judge_prompt = f"""
    You are an objective AI evaluation judge for technical education in embedded systems.
    Evaluate the generated answer against the reference answer for the given question.
    
    Question: "{question}"
    Reference Answer: "{reference}"
    Generated Output: "{generated_output}"
    
    Rate the output on a scale from 1 to 5 based on factual correctness, technical accuracy, and completeness.
    Give ONLY a valid JSON response in this exact format: {{"score": <int 1-5>, "reason": "<short explanation>"}}
    """
    result_str = call_llm(judge_prompt)
    try:
        start = result_str.find("{")
        end = result_str.rfind("}") + 1
        return json.loads(result_str[start:end]) # put it in Dictionary.
    except:
        return {"score": 1, "reason": "Failed to parse judge response"}

def run_evaluation():
    total_tests = len(golden_cases)
    passed_tests = 0
    results_summary = []
    
    print(f"Starting evaluation suite with {total_tests} test cases...\n") # print line to shoe that the test cases started.
    
    for item in golden_cases:
        test_id = item["id"]
        question = item["question"]
        reference = item["reference"]
        required_concepts = item["required_concepts"]
        
        # prepare the the model prompt
        prompt = f"Answer the following technical question concisely and accurately:\n{question}"
        output = call_llm(prompt)
        
        # 1. Programmatic Assertions بناءً على الـ required_concepts
        missing_concepts = []
        for concept_group in required_concepts:
            # find if any of the required_concepts is missing
            found = any(term.lower() in output.lower() for term in concept_group) # lower to convert the text to lower case.
            if not found:
                missing_concepts.append(concept_group[0]) # if any of the required_concepts is missing add the first on in missing_concepts array .
                
        assertions_passed = len(missing_concepts) == 0
        assertion_error = f"Missing concepts: {missing_concepts}" if not assertions_passed else ""
        
        # 2. LLM-as-a-Judge Scoring
        judge_result = llm_as_a_judge(question, reference, output)
        judge_score = judge_result.get("score", 1)
        
        # Score > 3
        is_success = assertions_passed and (judge_score >= 3)
        
        if is_success:
            passed_tests += 1
            status = "PASS"
        else:
            status = "FAIL"
            
        results_summary.append({
            "id": test_id,
            "question": question,
            "status": status,
            "assertion_error": assertion_error,
            "judge_score": judge_score,
            "judge_reason": judge_result.get("reason", "")
        })
        
        print(f"[{status}] Test #{test_id} | Judge Score: {judge_score}/5 | Error: {assertion_error if assertion_error else 'None'}")

    pass_rate = (passed_tests / total_tests) * 100
    print(f"\n--- Evaluation Complete ---")
    print(f"Pass Rate: {pass_rate:.2f}% ({passed_tests}/{total_tests})")
    
    with open("evaluation_report.json", "w", encoding="utf-8") as f:  #Save the outputs in .json file
        json.dump(results_summary, f, indent=4)
        
    if pass_rate < 75.0:
        exit(1)

if __name__ == "__main__":
    run_evaluation()