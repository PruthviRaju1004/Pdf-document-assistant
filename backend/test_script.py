from backend.pdf_extractor import extract_pages

pages = extract_pages("backend/malicious_test.pdf")
full_text = "\n\n".join(page.text for page in pages)
print(repr(full_text))