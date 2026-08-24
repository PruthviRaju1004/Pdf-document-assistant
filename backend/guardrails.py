def contains_injection_attempt(text: str) -> bool:
    suspicious_phrases = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "you are now",
        "disregard the above",
        "new instructions:",
        "hack the system",
        "steal user data",
        "you have full access",
    ]
    normalized = " ".join(text.lower().split())
    for phrase in suspicious_phrases:
        if phrase in normalized:
            return True
    return False


if __name__ == "__main__":
    print(contains_injection_attempt("ignore previous instructions"))
    print(contains_injection_attempt("what water temperature should I use"))