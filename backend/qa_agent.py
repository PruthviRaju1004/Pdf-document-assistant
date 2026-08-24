import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def build_prompt(question: str, chunks: list) -> str:
    context_parts = []
    for text, page_number, filename, distance in chunks:
         context_parts.append(f"--- Source: {filename}, page {page_number} ---\n{text}")
    context = "\n\n".join(context_parts)
    prompt = f"""You are answering questions using only the text provided below. If the answer isn't in the text, say "I don't have enough information to answer that." After each claim you make, cite the source like this: (Source: <pdf filename>, page <number>).

{context}

Question: {question}"""

    return prompt

def ask(question: str, chunks: list) -> str:
    prompt = build_prompt(question, chunks)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text

if __name__ == "__main__":
    from .main import search_multiple_docs

    answer = search_multiple_docs(
        client_id=2,
        pdf_paths=["backend/iso27001.pdf", "backend/coffee_brewing_guide.pdf"],
        question="what water temperature should I use for brewing coffee",
    )
    print(answer)