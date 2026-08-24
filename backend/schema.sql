CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    api_key TEXT UNIQUE NOT NULL
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL
);

CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding vector(384)
);