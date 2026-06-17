import os
import pandas as pd
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from app.config import settings

class DynamicRAGService:
    def __init__(self):
        # Local, lightweight embedding model (100% free, fast compute)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.documents = []

    def build_index_from_file(self, filename: str) -> dict:
        """
        Dynamically loads any uploaded file from the storage directory, 
        serializes it into comprehensive text blocks, and populates FAISS.
        """
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            return {"error": f"Target file '{filename}' not found in upload sandbox."}

        records = []

        # Route parsing based on file extensions
        if filename.endswith(".csv"):
            df = pd.read_csv(file_path)
            for idx, row in df.iterrows():
                # Formulate a natural text statement representing the entire data row dynamically
                row_str = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                records.append({
                    "id": f"row_{idx}",
                    "text": f"Source: {filename} (Row {idx+1}) -> {row_str}",
                    "raw_data": row.to_dict()
                })
        else:
            # For unstructured raw txt files
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for idx, line in enumerate(lines):
                if line.strip():
                    records.append({
                        "id": f"line_{idx}",
                        "text": f"Source: {filename} (Line {idx+1}) -> {line.strip()}",
                        "raw_data": {"text_line": line.strip()}
                    })

        if not records:
            return {"error": "No parseable text elements detected in data file."}

        self.documents = records
        texts = [doc["text"] for doc in records]
        
        # Vectorize text blocks using the local pipeline
        embeddings = self.model.encode(texts, convert_to_numpy=True).astype("float32")
        dimension = embeddings.shape[1]

        # Construct flat L2 Euclidean space index matrix
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        # Write vectors directly to local free storage
        faiss.write_index(self.index, os.path.join(settings.FAISS_DIR, "store.faiss"))
        with open(os.path.join(settings.FAISS_DIR, "docs.pkl"), "wb") as f:
            pickle.dump(self.documents, f)

        return {"status": "success", "indexed_elements": len(records)}

    def semantic_search(self, query: str, top_k: int = 3) -> list:
        """Queries the local FAISS instance using cosine proximity weights."""
        index_path = os.path.join(settings.FAISS_DIR, "store.faiss")
        doc_path = os.path.join(settings.FAISS_DIR, "docs.pkl")

        # Lazy load indexes from storage if the application memory loop recycled
        if self.index is None:
            if os.path.exists(index_path) and os.path.exists(doc_path):
                self.index = faiss.read_index(index_path)
                with open(doc_path, "rb") as f:
                    self.documents = pickle.load(f)
            else:
                return [{"warning": "No local index storage mounted yet. Upload a data stream first."}]

        if not self.documents or self.index.ntotal == 0:
            return []

        # Vectorize incoming inquiry
        query_vector = self.model.encode([query], convert_to_numpy=True).astype("float32")
        
        # Calculate spatial neighbors
        k = min(top_k, len(self.documents))
        distances, indices = self.index.search(query_vector, k)

        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx != -1 and idx < len(self.documents):
                matched_item = self.documents[idx].copy()
                matched_item["similarity_distance"] = float(dist)
                results.append(matched_item)
                
        return results

# Register singleton instance
rag_service = DynamicRAGService()