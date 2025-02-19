from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ast
import json
import subprocess
import os

app = FastAPI()

class CodeInput(BaseModel):
    code: str

# --- Syntax Error Detection --- #
def analyze_syntax(code):
    try:
        ast.parse(code)  # Check if code is valid Python
        return {"status": "Valid Syntax", "errors": []}
    except SyntaxError as e:
        return {
            "status": "Syntax Error",
            "errors": [{"line": e.lineno if e.lineno else 1, "message": e.msg}]
        }

# --- Inefficiency Detection (Nested Loops, Unused Variables) --- #
def detect_inefficiencies(code):
    inefficiencies = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            for child in ast.walk(node):
                if isinstance(child, ast.For):  
                    inefficiencies.append({
                        "line": node.lineno,
                        "message": "Nested loops detected (O(n²)). Consider optimizing."
                    })
        if isinstance(node, ast.Assign) and not isinstance(node.ctx, ast.Store):
            inefficiencies.append({
                "line": node.lineno,
                "message": "Unused variable detected."
            })

    return inefficiencies

# --- CodeQL Security Analysis --- #
def run_codeql_scan():
    db_path = "my_db"
    query_suite = "/Users/sindhu/Projects/AI-Bug-Fixer/backend/codeql/python/ql/src/codeql-suites/python-security-and-quality.qls"
    results_file = "results.sarif"

    if not os.path.exists(db_path):
        raise HTTPException(status_code=500, detail="CodeQL database not found. Run CodeQL database creation first.")

    cmd = f"/opt/homebrew/bin/codeql database analyze {db_path} {query_suite} --format=sarif-latest --output={results_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"CodeQL analysis failed: {result.stderr}")

    if not os.path.exists(results_file):
        raise HTTPException(status_code=500, detail="CodeQL analysis failed. No results found.")

    with open(results_file, "r") as file:
        try:
            results = json.load(file)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse CodeQL results.")

    vulnerabilities = []
    for result in results.get("runs", [])[0].get("results", []):
        message_text = result["message"]["text"]

        ignored_messages = [
            "Import of 'HTTPException' is not used.",
            "Unused import statement",
            "Import not referenced"
        ]
        if any(ignored in message_text for ignored in ignored_messages):
            continue  

        vulnerabilities.append({
            "line": result["locations"][0]["physicalLocation"]["region"]["startLine"],
            "message": message_text
        })

    return vulnerabilities

@app.post("/analyze")
def analyze_code(input_data: CodeInput):
    # Syntax Check
    syntax_result = analyze_syntax(input_data.code)
    
    # If syntax error exists, return immediately
    if syntax_result["status"] == "Syntax Error":
        return {
            "syntax": syntax_result,
            "inefficiencies": [],
            "vulnerabilities": []
        }
    
    # Inefficiency Check
    inefficiencies = detect_inefficiencies(input_data.code)
    
    # Run CodeQL Security Analysis
    vulnerabilities = run_codeql_scan()

    return {
        "syntax": syntax_result,
        "inefficiencies": inefficiencies,
        "vulnerabilities": vulnerabilities
    }
