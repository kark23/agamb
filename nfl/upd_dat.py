import numpy as np
import pandas as pd
import os

if __name__=='__main__':
    savdir="data/nflsavant"
    nflscrapr=pd.read_csv("data/nflscrapr/NFL Play by Play 2009-2018 (v5).csv")
    frst=True
    for file in os.listdir(savdir):
        if frst:
            nflsavant=pd.read_csv(os.path.join(savdir, file))
            frst=False
        else:
            nflsavant=nflsavant.append(pd.read_csv(os.path.join(savdir, file)), ignore_index = True)
    rnm={'GameID':'game_id','GameDate':'game_date','Quarter':'qtr','OffenseTeam':'posteam','DefenseTeam':'defteam','Down':'down','ToGo':'ydstogo',
        'Yards':'yards_gained','IsRush':'rush_attempt','IsPass':'pass_attempt','IsIncomplete':'incomplete_pass','IsTouchdown':'touchdown','IsSack':'sack',
        'IsIntercpetion':'interception','IsFumble':'fumble_forced'}
    colneed=['home_team','play_id','away_team'
    nflsavant=nflsavant
