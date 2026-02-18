import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def build_retriever(text: str):
    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip())
    chunks = [s.strip() for s in sentences if len(s.strip()) > 80]

    if not chunks:
        chunks = [text[:5000]]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=40000)
    matrix = vectorizer.fit_transform(chunks)

    retriever = {"vectorizer": vectorizer, "matrix": matrix}
    return retriever, chunks

def retrieve_top_chunks(retriever, chunks, query: str, top_k: int = 6):
    qv = retriever["vectorizer"].transform([query])
    sims = cosine_similarity(qv, retriever["matrix"]).flatten()
    idx = sims.argsort()[::-1][:top_k]

    results = []
    for i in idx:
        results.append({
            "chunk_id": f"C{i:04d}",
            "text": chunks[i],
            "score": float(sims[i])
        })
    return results
