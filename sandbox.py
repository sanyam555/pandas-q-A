import re
import subprocess
import tempfile
import os
import sys

BANNED_PATTERNS = [
    r"\bimport\s+os\b",
    r"\bimport\s+sys\b",
    r"\bimport\s+shutil\b",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+socket\b",
    r"\bimport\s+requests\b",
    r"\bimport\s+urllib\b",
    r"__import__",
    r"\bopen\s*\(",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bos\.",
    r"\bsys\.",
    r"\bshutil\.",
    r"\bsubprocess\.",
]

TIMEOUT_SECONDS = 10

SETUP_CODE = """
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "Dana"],
    "age": [25, 32, 18, 47],
    "city": ["NYC", "LA", "NYC", "SF"],
    "score": [85.5, 92.1, 76.3, 88.0],
})
"""


def is_code_safe(code):
    for pattern in BANNED_PATTERNS:
        if re.search(pattern, code):
            return False, pattern
    return True, None


def run_code_safely(code):
    safe, matched_pattern = is_code_safe(code)
    if not safe:
        return {
            "success": False,
            "output": "",
            "error": f"Blocked before running: code contains disallowed pattern '{matched_pattern}'",
        }

    full_code = SETUP_CODE + "\n" + code

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(full_code)
        temp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Code took longer than {TIMEOUT_SECONDS} seconds to run (possible infinite loop)",
        }
    finally:
        os.remove(temp_path)
import ast

def ensure_output_visible(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    if not tree.body:
        return code

    last_node = tree.body[-1]
    if isinstance(last_node, ast.Expr):
        already_print = (
            isinstance(last_node.value, ast.Call)
            and isinstance(last_node.value.func, ast.Name)
            and last_node.value.func.id == "print"
        )
        if not already_print:
            print_call = ast.Expr(value=ast.Call(
                func=ast.Name(id="print", ctx=ast.Load()),
                args=[last_node.value], keywords=[],
            ))
            tree.body[-1] = ast.copy_location(print_call, last_node)
            ast.fix_missing_locations(tree)
            return ast.unparse(tree)

    return code

if __name__ == "__main__":
    test_code = "print(df.groupby('city')['score'].mean())"
    result = run_code_safely(test_code)
    print("Success:", result["success"])
    print("Output:", result["output"])
    print("Error:", result["error"])