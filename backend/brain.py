import sqlite3
import os
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

DB_PATH = os.path.join(os.path.dirname(__file__), "brain.db")
VECTOR_DIM = 512

try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:
    faiss = None
    FAISS_AVAILABLE = False


class Brain:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_db()
        self.vec = HashingVectorizer(n_features=VECTOR_DIM, alternate_sign=False)
        self.faiss_index = None
        if FAISS_AVAILABLE:
            self._init_faiss()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_db(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            filename TEXT,
            content TEXT,
            sanitized TEXT,
            embedding BLOB,
            created_at TEXT
        )
        """
        )
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS index_map (
            doc_id INTEGER PRIMARY KEY,
            idx_pos INTEGER
        )
        """
        )
        conn.commit()
        conn.close()

    def _init_faiss(self):
        # build index from existing embeddings if any
        self.faiss_index = faiss.IndexFlatL2(VECTOR_DIM)
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id, embedding FROM documents WHERE embedding IS NOT NULL")
        rows = cur.fetchall()
        if rows:
            mats = []
            for doc_id, emb_blob in rows:
                vec = np.frombuffer(emb_blob, dtype=np.float32)
                mats.append(vec)
            mat = np.stack(mats).astype('float32')
            self.faiss_index.add(mat)
            # rebuild index_map
            cur.execute("DELETE FROM index_map")
            for i, (doc_id, _) in enumerate(rows):
                cur.execute("INSERT OR REPLACE INTO index_map(doc_id, idx_pos) VALUES (?,?)", (doc_id, i))
            conn.commit()
        conn.close()

    def embed(self, text: str) -> np.ndarray:
        v = self.vec.transform([text])
        arr = v.toarray()[0].astype('float32')
        return arr

    def persist_document(self, filename: str, content: str, sanitized: str) -> int:
        emb = self.embed(sanitized)
        conn = self._connect()
        cur = conn.cursor()
        now = datetime.utcnow().isoformat() + 'Z'
        emb_blob = emb.tobytes()
        cur.execute(
            "INSERT INTO documents(filename, content, sanitized, embedding, created_at) VALUES (?,?,?,?,?)",
            (filename, content, sanitized, emb_blob, now),
        )
        doc_id = cur.lastrowid
        # if faiss available, add to index and record map
        if FAISS_AVAILABLE and self.faiss_index is not None:
            self.faiss_index.add(np.expand_dims(emb, axis=0))
            idx_pos = int(self.faiss_index.ntotal) - 1
            cur.execute("INSERT OR REPLACE INTO index_map(doc_id, idx_pos) VALUES (?,?)", (doc_id, idx_pos))
        conn.commit()
        conn.close()
        return doc_id

    def search(self, query: str, topk: int = 5):
        qv = self.embed(query)
        conn = self._connect()
        cur = conn.cursor()
        results = []
        if FAISS_AVAILABLE and self.faiss_index is not None and self.faiss_index.ntotal > 0:
            D, I = self.faiss_index.search(np.expand_dims(qv, axis=0).astype('float32'), topk)
            idxs = I[0].tolist()
            # map idx to doc_id
            cur.execute("SELECT doc_id, idx_pos FROM index_map WHERE idx_pos IN (%s)" % 
                        ','.join('?'*len(idxs)), tuple(idxs))
            mapping = {row[1]: row[0] for row in cur.fetchall()}
            for pos, dist in zip(idxs, D[0].tolist()):
                doc_id = mapping.get(pos)
                if doc_id:
                    cur.execute("SELECT id, filename, sanitized FROM documents WHERE id=?", (doc_id,))
                    row = cur.fetchone()
                    if row:
                        results.append({"id": row[0], "filename": row[1], "sanitized": row[2], "score": float(dist)})
        else:
            # brute-force over all embeddings
            cur.execute("SELECT id, filename, sanitized, embedding FROM documents WHERE embedding IS NOT NULL")
            rows = cur.fetchall()
            cand = []
            for doc_id, filename, sanitized, emb_blob in rows:
                vec = np.frombuffer(emb_blob, dtype=np.float32)
                # cosine similarity
                denom = (np.linalg.norm(qv) * np.linalg.norm(vec))
                score = float(np.dot(qv, vec) / denom) if denom>0 else 0.0
                cand.append((score, doc_id, filename, sanitized))
            cand.sort(reverse=True, key=lambda x: x[0])
            for score, doc_id, filename, sanitized in cand[:topk]:
                results.append({"id": doc_id, "filename": filename, "sanitized": sanitized, "score": score})
        conn.close()
        return results


brain = Brain()
