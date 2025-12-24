import classes
import get_points_by_dist

def get_points(db, qemb_s, p_start, p_end, pipe):
    resq = qemb_s.search(pipe)
    resq_final = get_points_by_dist.get_points_into_route(resq, p_start, p_end, 8)

    # resd = get_points_by_dist.get_points_into_route(db, p_start, p_end, 50)
    # demb_s = classes.EmbSearch(resd, 10, 10)
    # resd_final = demb_s.search(pipe)

    # return list(dict.from_keys(resd_final.append(resq_final)))
    return resq_final
