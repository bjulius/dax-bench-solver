import os, json, re, requests, sys

API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def load_task(task_id):
    for level in ["basic", "intermediate", "advanced"]:
        path = f"tasks/{level}/{task_id}.json"
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    return None

def call_api(model, messages):
    r = requests.post(BASE_URL, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                     json={"model": model, "messages": messages, "temperature": 0.2, "max_tokens": 1000}, timeout=60)
    return r.json() if r.status_code == 200 else None

def extract_dax(text):
    m = re.search(r'```(?:dax)?\s*(.*?)```', text, re.DOTALL | re.I)
    if m: return m.group(1).strip()
    m = re.search(r'(\[?\w+[\w\s]*\]?\s*=\s*.+)', text, re.DOTALL)
    return m.group(1).strip() if m else text.strip()

def normalize(dax):
    return re.sub(r'\s+', ' ', dax).strip().lower().replace("'", "'")

def validate(gen, exp, alts):
    if normalize(gen) == normalize(exp): return True
    for a in alts:
        if normalize(gen) == normalize(a): return True
    # Expression match
    gm = re.match(r'\[?[^\]=]+\]?\s*=\s*(.+)', gen, re.DOTALL)
    em = re.match(r'\[?[^\]=]+\]?\s*=\s*(.+)', exp, re.DOTALL)
    if gm and em and normalize(gm.group(1)) == normalize(em.group(1)): return True
    for a in alts:
        am = re.match(r'\[?[^\]=]+\]?\s*=\s*(.+)', a, re.DOTALL)
        if gm and am and normalize(gm.group(1)) == normalize(am.group(1)): return True
    return False

task_id = sys.argv[1]
model = sys.argv[2] if len(sys.argv) > 2 else "anthropic/claude-opus-4.5"
max_iter = int(sys.argv[3]) if len(sys.argv) > 3 else 20

task = load_task(task_id)
if not task:
    print(f"Task not found: {task_id}")
    sys.exit(1)

print(f"Task: {task_id} - {task['title']}")
print(f"Model: {model}")
print(f"Max iterations: {max_iter}")
print(f"Expected: {task['expectedOutput']['dax'][:80]}...")
print("-" * 60)

messages = [
    {"role": "system", "content": task["prompt"]["system"]},
    {"role": "user", "content": f"{task['prompt']['user']}\n\nContext: {task['prompt']['dataModelContext']}"}
]

for i in range(1, max_iter + 1):
    resp = call_api(model, messages)
    if not resp or "choices" not in resp:
        print(f"[{i}] API Error")
        continue
    
    content = resp["choices"][0]["message"]["content"]
    dax = extract_dax(content)
    cost = resp.get("usage", {}).get("cost", 0)
    
    if validate(dax, task["expectedOutput"]["dax"], task["expectedOutput"].get("alternativeCorrect", [])):
        print(f"[{i}] SOLVED! Cost so far: ${cost:.4f}")
        print(f"DAX: {dax[:100]}...")
        sys.exit(0)
    else:
        print(f"[{i}] Failed - {dax[:60]}...")
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": "That doesn't match the expected pattern. Please try again."})

print(f"\nFailed after {max_iter} iterations")
