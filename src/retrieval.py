from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def build_retriever(text):
    sentences = text.split(".")
    chunks = [s.strip() for s in sentences if len(s.strip()) > 50]

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(chunks)

    retriever = {
        "vectorizer": vectorizer,
        "matrix": matrix
    }

    return retriever, chunks

def retrieve_top_chunks(retriever, chunks, query, top_k=5):
    qv = retriever["vectorizer"].transform([query])
    sims = cosine_similarity(qv, retriever["matrix"]).flatten()
    idx = sims.argsort()[::-1][:top_k]

    results = []
    for i in idx:
        results.append({
            "text": chunks[i],
            "score": float(sims[i])
        })

    return results
