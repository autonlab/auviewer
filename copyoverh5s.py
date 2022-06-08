from pathlib import Path
import os
import random
from glob import glob

def copy_h5s(src: Path, dst: Path, num=1):
    #get 10 random files from dst path
    h5Files = glob(str(src / '*.h5'))
    for i in range(num):
        randomh5 = random.choice(h5Files)

        fname = randomh5.split(os.sep)[-1]
        # print(fname)
        # print(1/0)
        print(f'Copying {fname} from {str(src)} to {str(dst)}')
        os.system(f'cp -s {str(src)}/{fname} {str(dst)}/{fname}')

if __name__ == '__main__':
    copy_h5s(Path('/home/cindy/workspace/'), Path('./assets/auvdata/projects/afibsample/originals'), num=3)