import multiprocessing as mp
import audata

def g(k):
    f = audata.File.open('/home/cindy/Documents/github/auviewer/auviewer/20200311_1502443_1061484.h5')
    ds = f['data/numerics/HR.BeatToBeat']
    for i in range(1, 14):
        a = ds[0]['time'][0]
    f.close()
    return 0
f = audata.File.open('/home/cindy/Documents/github/auviewer/auviewer/20200311_1502443_1061484.h5')
ds = f['data/numerics/HR.BeatToBeat']
pool = mp.Pool(8)
ok = [i for i in range(0, 500)]

pool.map(g, ok)
