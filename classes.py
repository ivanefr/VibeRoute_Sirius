import get_embedding

class Object:
    def __init__(self, x, y, dist_to_vec, desc, other_params):
        self.x = x
        self.y = y
        self.dist_to_vec = dist_to_vec
        self.desc = desc
        self.other = other_params

class EmbSearch:
    def __init__(self, db, dist_metric, k):
        descs = []
        self.db = db
        for i in self.db:
            descs.append(i.desc)
        self.emb = get_embedding.get_emb(descs)
        self.neigh = get_embedding.NN(self.emb, k, dist_metric)

    def search(self, query):
        q_emb = get_embedding.get_emb(query)
        idx = get_embedding.get_nearst_embedding(self.neigh, q_emb)
        # return idx

        res = []
        for i in idx[0]:
            res.append(self.db[i])

        return res
