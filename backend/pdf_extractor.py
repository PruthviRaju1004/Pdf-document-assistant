from dataclasses import dataclass
import pdfplumber

@dataclass
class PageText:
    page_number: int
    text: str

def extract_pages(pdf_path: str) -> list[PageText]:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                pages.append(PageText(page_number=i + 1, text=page_text))
    return pages


if __name__ == "__main__":
    pages = extract_pages("backend/iso27001.pdf")
    print(f"Extracted {len(pages)} pages")
    print(f"Page {pages[0].page_number}: {pages[0].text[:200]!r}")
    print(f"Page {pages[5].page_number}: {pages[5].text[:200]!r}")