from sentence_transformers import SentenceTransformer
from transformers import pipeline
import faiss
import numpy as np

class RAGEngine:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.qa_model = pipeline("text2text-generation", model="google/flan-t5-base")
        self.index = faiss.IndexFlatL2(384)
        self.proposals = []

    def add_proposal(self, text: str):
        self.proposals.append(text)
        vec = self.model.encode([text])
        self.index.add(np.array(vec))

    def query_proposals(self, question: str, top_k: int = 3):
        vec = self.model.encode([question])
        D, I = self.index.search(np.array(vec), top_k)
        context = " ".join([self.proposals[i] for i in I[0]])
        result = self.qa_model(f"Context: {context}. Question: {question}")
        return result[0]['generated_text']

