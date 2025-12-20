import numpy as np
from sklearn.neighbors import NearestNeighbors
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")

def get_emb(sentences):
    return model.encode(sentences)

def get_simularity(embeddings, q_embeddings):
    return model.similarity(embeddings, q_embeddings)

def NN(embeddings, k, dist):
    neigh = NearestNeighbors(n_neighbors=k, radius=dist)
    neigh.fit(embeddings)
    return neigh

def get_nearst_embedding(neigh, q_embeddings):
    return np.asarray(neigh.kneighbors(q_embeddings, return_distance=False))
