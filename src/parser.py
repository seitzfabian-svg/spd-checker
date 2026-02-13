import io
from pypdf import PdfReader

def parse_document(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.read()

    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore").strip()

    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()

    raise ValueError("Unsupported file type. Please upload PDF or TXT.")
