import os
from dotenv import load_dotenv
from anthropic import Anthropic

from .db import get_documents_for_client, search_chunks_for_client

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

MAX_TOOL_ITERATIONS = 5

tools = [
    {
        "name": "list_documents",
        "description": "Get the list of documents this client has uploaded, including filenames. Use this when the user asks what documents are available, or refers to a document by name.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "search_documents",
        "description": "Search the client's uploaded documents for content relevant to a question, and return the most relevant excerpts with citations. Use this whenever the user asks something that requires looking inside their documents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The user's question, used to search document content for relevant passages.",
                }
            },
            "required": ["query"],
        },
    },
]


def list_documents(client_id: int) -> str:
    documents = get_documents_for_client(client_id)
    if not documents:
        return "This client has no uploaded documents."
    lines = [f"- {filename} ({file_path})" for filename, file_path in documents]
    return "Documents:\n" + "\n".join(lines)


def search_documents(client_id: int, query: str) -> str:
    documents = get_documents_for_client(client_id)
    if not documents:
        return "No documents available to search."

    pdf_paths = [file_path for _, file_path in documents]
    rows = search_chunks_for_client(client_id, pdf_paths, query)

    if not rows:
        return "No relevant content found in the client's documents for this query."

    parts = []
    for text, page_number, filename, distance in rows:
        parts.append(f"--- Source: {filename}, page {page_number} ---\n{text}")
    return "\n\n".join(parts)


def run_tool(tool_name: str, tool_input: dict, client_id: int) -> str:
    if tool_name == "list_documents":
        return list_documents(client_id)
    elif tool_name == "search_documents":
        return search_documents(client_id, tool_input["query"])
    else:
        return f"Unknown tool: {tool_name}"


def ask_with_tools(client_id: int, question: str) -> str:
    messages = [{"role": "user", "content": question}]

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            text_blocks = [b.text for b in response.content if b.type == "text"]
            return "\n".join(text_blocks)

        messages.append({"role": "assistant", "content": response.content})

        tool_result_blocks = []
        for block in response.content:
            if block.type == "tool_use":
                result = run_tool(block.name, block.input, client_id)
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_result_blocks})

    return "I wasn't able to complete this request after several tool calls — please try rephrasing your question."


if __name__ == "__main__":
    answer = ask_with_tools(client_id=2, question="what documents do I have?")
    print("Answer 1:", answer)

    answer2 = ask_with_tools(client_id=2, question="what water temperature should I use for coffee?")
    print("\nAnswer 2:", answer2)