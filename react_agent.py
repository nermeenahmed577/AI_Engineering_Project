import json
import os
import re
import sqlite3
import requests

URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"
STEP_LIMIT = 6  # max 6 Steps. 


def setup_db():
    con = sqlite3.connect(":memory:") #Database using SQLite in RAM (Temporary DataBase).
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE components (id INTEGER PRIMARY KEY, name TEXT, voltage REAL, cost_usd REAL, stock INTEGER)"
    )
    items = [
        (1, "STM32F401CCU6", 3.3, 4.50, 12),
        (2, "ESP32-S3", 3.3, 3.80, 25),
        (3, "LM7805", 5.0, 0.45, 100),
        (4, "Red LED 5mm", 2.0, 0.05, 300),
    ]
    cur.executemany("INSERT INTO components VALUES (?, ?, ?, ?, ?)", items) # insert the items in the DataBase
    con.commit()
    return con  #return the Connection .


db = setup_db() #Setup the DataBase .

# Tool that make the Ai Agent search in the Database.
def run_sql(sql):
    if not sql.strip().lower().startswith("select"): # Select only "Don`t Change in the Database". 
        return "blocked: only SELECT queries allowed"  # if it try to changee in the DB print this.
    try:
        cur = db.cursor() # get the Cursor Ready.
        cur.execute(sql)
        cols = [c[0] for c in cur.description] if cur.description else [] #return Columns from the 
        return json.dumps({"cols": cols, "rows": cur.fetchall()})
    except Exception as err:
        return f"sql error: {err}"

# Tool Allow the Agent to make Calculations.
def calc_python(expr):
    blocked = ["__", "import", "open", "exec", "eval", "compile", "os.", "sys."] #block this expressions "Not Allowed"
    if any(b in expr for b in blocked): # if any of this blocked expression exist then 
        return "blocked expression"
    safe_globals = {"__builtins__": {}}
    safe_locals = {"abs": abs, "round": round, "min": min, "max": max, "pow": pow, "sum": sum}
    try:
        return str(eval(expr, safe_globals, safe_locals)) # try to execute the expression and produce the output.
    except Exception as err:
        return f"math error: {err}"

# Tool Allow the Agent to Search in my computer files for the target Word (Needle) in a file.
def search_files(needle, start="."): # start searching from the current directory.
    hits = []
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"} # during searching skip this files Bec they are larg and will slow the process.
    for root, dirs, files in os.walk(start):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")] # not in the skip dir or the hidden files.
        for name in files:
            path = os.path.join(root, name)
            if needle.lower() in name.lower():
                hits.append(path)
                continue
            if name.endswith((".py", ".txt", ".md", ".json", ".csv")): # if this file extention is one of this , then we can open it to look for the neddel .
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        if needle.lower() in f.read(30000).lower():
                            hits.append(path)
                except OSError:
                    pass
        if len(hits) >= 20:
            break
    return json.dumps(hits[:20]) if hits else "no matches"


tools = {
    "run_sql": run_sql,
    "calc_python": calc_python,
    "search_files": search_files,
}

prompt_header = """Answer the user's task step by step using tools if needed.

Format:
Thought: what to do next
Action: tool_name: argument

When done:
Thought: ready to answer
Final Answer: your response

Tools:
- run_sql: SELECT query on components(id, name, voltage, cost_usd, stock)
- calc_python: basic math expression
- search_files: search filenames or text in current folder for a keyword

Pick one action per step and wait for Observation. If a tool fails, fix the input and try again.
"""


def ask_model(prompt):
    try:
        res = requests.post(
            URL,
            json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}},
            timeout=60,
        )
        res.raise_for_status()
        return res.json().get("response", "").strip()
    except Exception as err:
        return f"Final Answer: model call failed ({err})"


def get_action(out):
    m = re.search(r"Action:\s*([a-zA-Z0-9_]+)\s*:\s*(.+)", out)
    if not m:
        return None, None
    return m.group(1).strip(), m.group(2).strip().strip("`") # return the Tool name , the Argument.

# Start the Agent
#  1-Send the Task to the Model.
#  2-Get the Model Judge
#  3-Use the Chosen Tool.
#  4- Get the Tool Output
#  5-Repeat untill the Model get a Final Answer (6 Steps)
def agent_loop(task):
    log = f"{prompt_header}\nTask: {task}\n"

    for i in range(1, STEP_LIMIT + 1):
        print(f"\n[step {i}/{STEP_LIMIT}]")
        out = ask_model(log) #  1-Send the Task to the Model.
        print(out)

        done = re.search(r"Final Answer:\s*(.+)", out, re.DOTALL)
        if done:
            return done.group(1).strip()

        name, arg = get_action(out) # to get the Tool name.
        if not name:
            obs = "format error: use 'Action: <tool>: <input>' or 'Final Answer:'"
            log += f"{out}\nObservation: {obs}\n"
            continue

        if name not in tools:
            obs = f"unknown tool '{name}'"
        else:
            obs = tools[name](arg)

        print("Observation:", obs)
        log += f"{out}\nObservation: {obs}\n"

    fallback = ask_model(f"{log}\nStep limit reached. Give Final Answer from what you found so far:")
    done = re.search(r"Final Answer:\s*(.+)", fallback, re.DOTALL)
    return done.group(1).strip() if done else fallback


if __name__ == "__main__":
    task = (
        "Check stock and cost_usd for STM32F401CCU6, compute total stock value, "
        "and search local files for 'golden'."
    )
    print("\n--- Final ---")
    print(agent_loop(task))