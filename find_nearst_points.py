import classes
from loguru import logger
import get_points_by_dist

def get_points(db, qemb_s, p_start, p_end, pipe):
    resd = get_points_by_dist.get_points_into_route(db, p_start, p_end, 50)

    resd_embs = classes.EmbSearch(resd, 6, qemb_s)
    resd_final = resd_embs.search(pipe)

    resq = qemb_s.search(pipe)

    for i in resq:
        resd_final.append(i)

    ans = list(dict.fromkeys(resd_final))
    return ans
