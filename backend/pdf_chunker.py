from dataclasses import dataclass

@dataclass
class Chunk:
    text: str
    chunk_id: str

@dataclass
class PageChunk:
    text: str
    page_number: int
    chunk_id: str

def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> list[Chunk]:
    chunks = []
    start = 0
    chunk_num = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text_piece = text[start:end]
        chunks.append(Chunk(text=chunk_text_piece, chunk_id=f"chunk_{chunk_num}"))
        chunk_num += 1
        start += chunk_size - overlap
    return chunks

def chunk_pages(pages: list, chunk_size: int = 700, overlap: int = 100) -> list[PageChunk]:
    chunks = []
    chunk_num = 0

    for page in pages:
        page_pieces = chunk_text(page.text, chunk_size, overlap)
        for piece in page_pieces:
            chunks.append(
                PageChunk(
                    text=piece.text,
                    page_number=page.page_number,
                    chunk_id=f"chunk_{chunk_num}",
                )
            )
            chunk_num += 1
    return chunks

if __name__ == "__main__":
    from .pdf_extractor import PageText

    fake_pages = [
        PageText(page_number=1, text="0123456789" * 2),   # 20 chars
        PageText(page_number=2, text="ABCDEFGHIJ" * 2),   # 20 chars
    ]

    chunks = chunk_pages(fake_pages, chunk_size=10, overlap=3)
    for c in chunks:
        print(f"{c.chunk_id} (page {c.page_number}): {c.text!r}")