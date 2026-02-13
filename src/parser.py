import io
from pypdf import PdfReader

def parse_document(uploaded_file):
    name = uploaded_file.name.lower()
    data = uploaded_file.read()

    if name.endswith(".txt"):
        return data.decode("utf-8")

    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    raise ValueError("Nur PDF oder TXT erlaubt.")
