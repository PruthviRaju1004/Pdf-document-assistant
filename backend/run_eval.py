import json
import os
from .main import search_multiple_docs

def main():
    eval_path = os.path.join(os.path.dirname("backend/run_eval.py"), "eval_set.json")
    
    with open(eval_path, "r", encoding="utf-8") as f:
        eval_cases = json.load(f)
        
    passed = 0
    failed = 0
    
    for i, case in enumerate(eval_cases):
        question = case.get("question")
        client_id = case.get("client_id")
        pdf_paths = case.get("pdf_paths")
        expected_contains = case.get("expected_contains", "")
        
        # Check handling/answer content
        answer = search_multiple_docs(client_id, pdf_paths, question)
        answer_lower = answer.lower() if isinstance(answer, str) else str(answer).lower()
        handle_ok = expected_contains.lower() in answer_lower
        case_passed = handle_ok
        
        if case_passed:
            passed += 1
            print(f"[PASS] Case {i+1}")
        else:
            failed += 1
            print(f"[FAIL] Case {i+1}")
            print(f"       Expected substring: '{expected_contains}'")
            print(f"       Got: {answer[:200]!r}")

    print("\n=== EVALUATION SUMMARY ===")
    print(f"Total Passed: {passed}")
    print(f"Total Failed: {failed}")
    print(f"Total Cases : {passed + failed}")

if __name__ == "__main__":
    main()
