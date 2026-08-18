from query import answer_question
from fix_code import fix_code

GOLDEN_QUESTIONS = [
    {
        "question": "What is the mean score for each city?",
        "expected_substrings": ["80.9", "92.1", "88.0"],
    },
    {
        "question": "What is the mean age for each city?",
        "expected_substrings": ["21.5", "32.0", "47.0"],
    },
]

GOLDEN_FIXES = [
    {
        "broken_code": "summary = df.groupby('city').agg({\n    'score': ['mean', 'max'],\n    'age': 'avg'\n})\nprint(summary)",
        "expected_substrings": ["21.5"],
    },
]


def check_output(output, expected_substrings):
    return all(sub in output for sub in expected_substrings)


def evaluate_questions():
    results = []
    for case in GOLDEN_QUESTIONS:
        result = answer_question(case["question"])
        execution = result["execution_result"]
        ran_ok = bool(execution and execution["success"])
        correct = bool(ran_ok and check_output(execution["output"], case["expected_substrings"]))
        results.append({"question": case["question"], "ran_successfully": ran_ok, "correct_output": correct})

        if not correct:
            print(f"\n--- DIAGNOSTIC for failed case: {case['question']!r} ---")
            print("Generated code:\n", result["code"])
            print("Actual output:\n", execution["output"] if execution else "(no execution result)")
            print("Actual error:\n", execution["error"] if execution else "")
            print("Expected to find:", case["expected_substrings"])
            print("--- end diagnostic ---\n")
    return results


def evaluate_fixes():
    results = []
    for case in GOLDEN_FIXES:
        result = fix_code(case["broken_code"])
        execution = result.get("fix_execution_result")
        ran_ok = bool(execution and execution["success"])
        correct = bool(ran_ok and check_output(execution["output"], case["expected_substrings"]))
        results.append({"broken_code": case["broken_code"][:50] + "...", "ran_successfully": ran_ok, "correct_output": correct})
    return results


def main():
    print("=== Question answering golden tests ===")
    q_results = evaluate_questions()
    for r in q_results:
        print(f"  [{'PASS' if r['correct_output'] else 'FAIL'}] ran={r['ran_successfully']} correct={r['correct_output']}: {r['question']}")
    q_pass_rate = sum(r["correct_output"] for r in q_results) / len(q_results)
    print(f"\nQuestion pass rate: {q_pass_rate:.2f}")

    print("\n=== Code-fixing golden tests ===")
    f_results = evaluate_fixes()
    for r in f_results:
        print(f"  [{'PASS' if r['correct_output'] else 'FAIL'}] ran={r['ran_successfully']} correct={r['correct_output']}: {r['broken_code']}")
    f_pass_rate = sum(r["correct_output"] for r in f_results) / len(f_results)
    print(f"\nFix pass rate: {f_pass_rate:.2f}")


if __name__ == "__main__":
    main()