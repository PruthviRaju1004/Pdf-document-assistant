import os
from .db import search_chunks_for_client
from .qa_agent import ask

def make_collection_name(pdf_path: str) -> str:
    filename = os.path.basename(pdf_path)          # "iso27001.pdf"
    name_without_ext = os.path.splitext(filename)[0]  # "iso27001"
    safe_name = name_without_ext.replace(" ", "_").replace("-", "_")
    return f"doc_{safe_name}"

def search_multiple_docs(client_id: int, pdf_paths: list[str], question: str, top_k: int = 5):
    rows = search_chunks_for_client(client_id, pdf_paths, question, top_k=top_k)
    print(f"Got {len(rows)} rows back")
    for row in rows:
        print(row)
    results = []
    for text, page_number, filename, distance in rows:
        results.append((text, page_number, filename, distance))

    answer = ask(question, results)
    return answer


if __name__ == "__main__":
    answer = search_multiple_docs(
        client_id=2,
        pdf_paths=["uploads/1c4511e4-5add-4060-ab22-f6a291c95902_coffee_brewing_guide.pdf"],
        question="what water temperature should I use for brewing coffee",
    )
    print(answer)
