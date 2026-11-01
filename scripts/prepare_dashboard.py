from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from market import history, BENCHMARK
if __name__=='__main__':
    _,meta=history(BENCHMARK,'2022-01-01','2024-12-31',Path(__file__).resolve().parents[1]/'data/local/cache')
    print(meta)
