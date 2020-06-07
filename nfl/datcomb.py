import numpy as np
import pandas as pd

if __name__=="__main__":
    his=pd.read_csv("data/nflscrapr/NFL Play by Play 2009-2018 (v5).csv")
    d18=pd.read_csv("data/nflscrapr/scrp18.csv")
    d19=pd.read_csv("data/nflscrapr/scrp19.csv")
    main=pd.concat([his,d18,d19],ignore_index=True, sort=False)
    main.to_csv("data/mainraw/agg_0.csv")
