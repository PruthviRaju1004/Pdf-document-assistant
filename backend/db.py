import psycopg2
import hashlib
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="devpassword",
    )

def insert_client(name: str, api_key: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clients (name, api_key) VALUES (%s, %s) RETURNING id;",
        (name, api_key),
    )
    client_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return client_id

def insert_document(client_id: int, filename: str, file_path: str, content_hash: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (client_id, filename, file_path, content_hash) VALUES (%s, %s, %s, %s) RETURNING id;",
        (client_id, filename, file_path, content_hash),
    )
    document_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return document_id


def insert_chunk(document_id: int, page_number: int, text: str):
    embedding = model.encode(text).tolist()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chunks (document_id, page_number, text, embedding) VALUES (%s, %s, %s, %s);",
        (document_id, page_number, text, embedding),
    )
    conn.commit()
    conn.close()

def search_chunks(document_id: int, query_text: str, top_k: int = 3):
    query_embedding = model.encode(query_text).tolist()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT text, page_number, embedding <=> %s::vector AS distance
        FROM chunks
        WHERE document_id = %s
        ORDER BY distance ASC
        LIMIT %s;
        """,
        (query_embedding, document_id, top_k),
    )
    results = cursor.fetchall()
    conn.close()
    return results

def get_client_by_api_key(api_key: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM clients WHERE api_key = %s;", (api_key,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_document_owner(file_path: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, client_id FROM documents WHERE file_path = %s;", (file_path,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_documents_for_client(client_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT filename, file_path FROM documents WHERE client_id = %s;",
        (client_id,),
    )
    results = cursor.fetchall()
    conn.close()
    return results

def search_chunks_for_client(client_id: int, pdf_paths: list[str], query_text: str, top_k: int = 5, max_distance: float = 0.6):
    query_embedding = model.encode(query_text).tolist()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT chunks.text, chunks.page_number, documents.filename,
               chunks.embedding <=> %s::vector AS distance
        FROM chunks
        JOIN documents ON chunks.document_id = documents.id
        WHERE documents.client_id = %s
          AND documents.file_path = ANY(%s)
          AND chunks.embedding <=> %s::vector < %s
        ORDER BY distance ASC
        LIMIT %s;
        """,
        (query_embedding, client_id, pdf_paths, query_embedding, max_distance, top_k),
    )
    results = cursor.fetchall()
    conn.close()
    return results

def compute_file_hash(file_path: str) -> str:
    with open(file_path, "rb") as f:
        content = f.read()
    return hashlib.sha256(content).hexdigest()

def get_document_by_hash(client_id: int, content_hash: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, file_path FROM documents WHERE client_id = %s AND content_hash = %s;",
        (client_id, content_hash),
    )
    result = cursor.fetchone()
    conn.close()
    return result

if __name__ == "__main__":
    result = get_client_by_api_key("test-key-456")
    print(result)

    missing = get_client_by_api_key("this-key-does-not-exist")
    print(missing)