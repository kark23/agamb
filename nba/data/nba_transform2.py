import numpy as np
import pandas as pd
import pickle
import copy
import time
import sys
import os

#Helper Functions

def window_agg(df, grp, cols, agg, wins):
	for win in wins:
		beg=time.time()
		adjcols=[f'{c}_{win}' for c in cols]
		df[adjcols]=df.groupby(grp)[cols].shift(1)
		if agg=='mean':
			df[adjcols]=df.groupby(grp)[adjcols].rolling(win, min_periods=1).mean().reset_index()[adjcols]
			#df[adjcols]=df.groupby(grp)[cols].shift(1).rolling(win, min_periods=1).mean() #.reset_index()[cols]
		elif agg=='var':
			df[adjcols]=df.groupby(grp)[adjcols].rolling(win, min_periods=1).var().reset_index()[adjcols]
			#df[adjcols]=df.groupby(grp)[cols].shift(1).rolling(win, min_periods=1).var() #.reset_index()[cols]
		print(time.time()-beg, df)
	return df

def wincols(cols, wins, pre=None):
	col_l=[]
	for win in wins:
		for col in cols:
			if pre==None:
				col_l.append(col+'_'+str(win))
			else:
				col_l.append(pre+col+'_'+str(win))
	return col_l

def aggtrans(var, plyr, tm, psit, phis, tsit, this, osit, ohis, type):
	pcols=psit+ wincols(phis, wins)
	vardf=copy.copy(plyr[pcols])
	forcols=tsit+ wincols(this, wins)
	basetm=copy.copy(tm[forcols])
	#Joins for team/opp
	vardf=vardf.merge(basetm, on=['game_id', 'team'], how='left')
	awycols=osit+ wincols(ohis, wins, 'd_')
	#awycols=['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss'], wins, 'd_')
	rnm={}
	for i in range(len(awycols)):
		rnm[(osit+ wincols(ohis, wins))[i]]=awycols[i]
	baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
	vardf=vardf.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
	if type=='update':
		#tmp=pd.concat(pd.read_pickle(outdir+f'df_{var}.pkl'), vardf[vardf['pop']=='upd'], ignore_index=True)
		#tmp.drop(columns='pop').to_pickle(outdir+f'df_{var}.pkl')
		#vardf[vardf['pop']=='dum'].reset_index().drop(columns='pop').to_pickle(f'dummy/modeling/df_{var}.pkl')
		vardf[vardf['pop']=='base'].reset_index().to_pickle(outdir+f'df_{var}.pkl')
		vardf[vardf['pop']=='dum'].dropna().reset_index().to_pickle(f'dummy/modeling/df_{var}.pkl')
	elif type=='full':
		vardf.to_pickle(outdir+f'df_{var}.pkl')

opt=sys.argv[1]
indir='trans1/'
outdir='trans2/'
wins=[2, 5, 10, 20, 50, 100]
#Inital Team Time Series Agg
team=pd.read_pickle(indir+'fullteam.pkl')
#team=pd.read_pickle(indir+'team2019.pkl')
if opt=='update':
	tm_dum=pd.read_pickle('dummy/tm.pkl')
	#tm_upd=pd.read_pickle(indir+'teamupd.pkl')
	#team= pd.merge(team, tm_upd, on=['team','game_id'], how="outer", indicator=True).query('_merge=="left_only"').copy()
	team['pop']='base'
	#tm_upd['pop']='upd'
	tm_dum['pop']='dum'
	print(type(tm_dum['wct'].iloc[0]), type(team['wct'].iloc[0]))
	#team=pd.concat([team, tm_upd], ignore_index=True)
	team=pd.concat([team, tm_dum], ignore_index=True)
if opt=='full':
	team['pop']='base'
team=team.sort_values(by=['team', 'game_id']).reset_index()
team['game_num']=team.groupby(['season','team']).cumcount()
print(team['wct'])
#team['wct']=team['wct'].dt.tz_convert(None)
#team['rest']=team.groupby(['team'])['wct'].diff()
team['rest']=0
print(team)
aggcols=['pfor', 'paga', 'fg2', 'pct2', 'fg3', 'pct3', 'ast', 'ast_pct', 'ft', 'ft_pct', 'oreb', 'dreb', 'oreb_pct', 'dreb_pct', 'stl', 'blk', 'tov', 'poss', 'fouls']
teamagg=window_agg(team, 'team', aggcols, 'mean', wins)

#Initial Player Time Series Agg
plyr=pd.read_pickle(indir+'fullplayer.pkl')
#plyr=pd.read_pickle(indir+'player2019.pkl')
if opt=='update':
	pl_dum=pd.read_pickle('dummy/ply.pkl')
	#pl_upd=pd.read_pickle(indir+'playerupd.pkl')
	#plyr= pd.merge(plyr, pl_upd, on=['player_id','game_id'], how="outer", indicator=True).query('_merge=="left_only"').copy()
	plyr['pop']='base'
	#pl_upd['pop']='upd'
	pl_dum['pop']='dum'
	#plyr=pd.concat([plyr, pl_upd], ignore_index=True)
	plyr=pd.concat([plyr, pl_dum], ignore_index=True)
	#tmp=plyr[plyr['pop']=='base'].merge(plyr[plyr['pop']!='base'][['player_id']].drop_duplicates(), on='player_id', how='inner').sort_values(by=['season','game_id']).groupby('player_id').head(100).reset_index(drop=True)
	#plyr=pd.concat([tmp, plyr[plyr['pop']!='base']], ignore_index=True).copy()
if opt=='full':
        plyr['pop']='base'
print(plyr)
for c in plyr.columns:
	print(c)
plyr=plyr.sort_values(['player_id', 'game_id']).reset_index()
aggcols=['p_time','p_fg2', 'p_pct2', 'p_fg3', 'p_pct3', 'p_ast', 'p_ast_pct', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_dreb', 'p_dreb_pct', 'p_stl', 'p_blk', 'p_tov', 'p_fouls', 'p_flr_pct', \
'p_stops', 'p_stop_pct', 'p_drtg', 'p_usg_pct', 'dubdub', 'tridub']
plyragg=window_agg(plyr, 'player_id', aggcols, 'mean', wins)
plyragg=window_agg(plyragg, 'player_id', ['fpts'], 'var', [100])
print(plyragg)

#2p Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'p_fg2']
phis=['p_time','p_fg2', 'p_pct2', 'p_fg3', 'p_pct3', 'p_ast', 'p_ast_pct', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_stl', 'p_tov', 'p_flr_pct', 'p_usg_pct']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['pfor', 'fg2', 'pct2', 'ast', 'ast_pct', 'oreb_pct', 'dreb_pct', 'stl', 'blk', 'tov', 'poss']
osit=['game_id', 'team', 'opp']
ohis=['paga', 'oreb_pct', 'dreb_pct', 'poss']
aggtrans('fg2', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

#3p Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'p_fg3']
phis=['p_time','p_fg2', 'p_pct2', 'p_fg3', 'p_pct3', 'p_ast', 'p_ast_pct', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_stl', 'p_tov', 'p_flr_pct', 'p_usg_pct']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['pfor', 'fg3', 'pct3', 'ast', 'ast_pct', 'oreb_pct', 'dreb_pct', 'stl', 'blk', 'tov', 'poss']
osit=['game_id', 'team', 'opp']
ohis=['paga', 'oreb_pct', 'dreb_pct', 'poss']
aggtrans('fg3', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

#Ft Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'p_ft']
phis=['p_time','p_fg2', 'p_pct2', 'p_fg3', 'p_pct3', 'p_ast', 'p_ast_pct', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_stl', 'p_tov', 'p_flr_pct', 'p_usg_pct']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['pfor', 'ft', 'ft_pct', 'ast', 'ast_pct', 'oreb_pct', 'dreb_pct', 'stl', 'blk', 'tov', 'poss']
osit=['game_id', 'team', 'opp']
ohis=['paga', 'oreb_pct', 'dreb_pct', 'poss', 'fouls']
aggtrans('ft', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

#ORB Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'p_oreb']
phis=['p_time','p_fg2', 'p_pct2', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_dreb', 'p_dreb_pct', 'p_flr_pct', 'p_usg_pct']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['pfor', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'stl', 'blk', 'tov', 'poss']
osit=['game_id', 'team', 'opp']
ohis=['paga', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'poss', 'fouls']
aggtrans('orb', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

#DRB Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'p_dreb']
phis=['p_time','p_fg2', 'p_pct2', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_dreb', 'p_dreb_pct', 'p_flr_pct', 'p_usg_pct']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['paga', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'stl', 'blk', 'tov', 'poss']
osit=['game_id', 'team', 'opp']
ohis=['pfor', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'poss', 'fouls']
aggtrans('drb', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

#Assist Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'p_ast']
phis=['p_time','p_fg2', 'p_pct2', 'p_fg3', 'p_pct3', 'p_ft', 'p_ft_pct', 'p_ast', 'p_ast_pct', 'p_tov', 'p_flr_pct', 'p_usg_pct']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['pfor', 'fg2', 'pct2', 'fg3', 'pct3', 'oreb', 'ast', 'ast_pct', 'oreb_pct', 'dreb', 'dreb_pct', 'stl', 'blk', 'tov', 'poss']
osit=['game_id', 'team', 'opp']
ohis=['paga', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'poss']
aggtrans('ast', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

#Steal Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'p_stl']
phis=['p_time', 'p_stl', 'p_blk', 'p_fouls', 'p_flr_pct', 'p_stops', 'p_stop_pct', 'p_drtg', 'p_usg_pct']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['pfor', 'paga', 'stl', 'blk', 'poss']
osit=['game_id', 'team', 'opp']
ohis=['pfor', 'ast', 'ast_pct', 'tov', 'poss']
aggtrans('stl', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

#Block Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'p_blk']
phis=['p_time', 'p_stl', 'p_blk', 'p_fouls', 'p_flr_pct', 'p_stops', 'p_stop_pct', 'p_drtg', 'p_usg_pct']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['pfor', 'paga', 'stl', 'blk', 'poss']
osit=['game_id', 'team', 'opp']
ohis=['pfor', 'ast', 'ast_pct', 'tov', 'poss']
aggtrans('blk', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

#TO Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'p_tov']
phis=['p_time','p_fg2', 'p_fg3', 'p_ast', 'p_ft', 'p_oreb', 'p_dreb', 'p_tov', 'p_flr_pct', 'p_usg_pct']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['pfor', 'ast_pct', 'oreb_pct', 'dreb_pct', 'tov', 'poss']
osit=['game_id', 'team', 'opp']
ohis=['paga', 'oreb_pct', 'dreb_pct', 'poss', 'stl', 'blk']
aggtrans('tov', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

#DD Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'dubdub']
phis=['p_time']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['pfor']
osit=['game_id', 'team', 'opp']
ohis=['paga']
aggtrans('dd', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

#TD Dataframe
psit=['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'tridub']
phis=['p_time']
tsit=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']
this=['pfor']
osit=['game_id', 'team', 'opp']
ohis=['paga']
aggtrans('td', plyragg, teamagg, psit, phis, tsit, this, osit, ohis, opt)

"""
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'p_fg2']+ wincols(['p_time','p_fg2', 'p_pct2', 'p_fg3', 'p_pct3', 'p_ast', 'p_ast_pct', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_stl', 'p_tov', 'p_flr_pct', 'p_usg_pct'], wins)
base2p=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['pfor', 'fg2', 'pct2', 'ast', 'ast_pct', 'oreb_pct', 'dreb_pct', 'stl', 'blk', 'tov', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
base2p=base2p.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
base2p=base2p.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
base2p[base2p['dummy']==0].reset_index().to_pickle(outdir+'df_fg2.pkl')
base2p[base2p['dummy']==1].reset_index().to_pickle('dummy/modeling/df_fg2.pkl')

#3p Dataframe
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'p_fg3']+ wincols(['p_time','p_fg2', 'p_pct2', 'p_fg3', 'p_pct3', 'p_ast', 'p_ast_pct', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_stl', 'p_tov', 'p_flr_pct', 'p_usg_pct'], wins)
base3p=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['pfor', 'fg3', 'pct3', 'ast', 'ast_pct', 'oreb_pct', 'dreb_pct', 'stl', 'blk', 'tov', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
base3p=base3p.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
base3p=base3p.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
base3p[base3p['dummy']==0].reset_index().to_pickle(outdir+'df_fg3.pkl')
base3p[base3p['dummy']==1].reset_index().to_pickle('dummy/modeling/df_fg3.pkl')

#Freethrow Dataframe
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'p_ft']+ wincols(['p_time','p_fg2', 'p_pct2', 'p_fg3', 'p_pct3', 'p_ast', 'p_ast_pct', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_stl', 'p_tov', 'p_flr_pct', 'p_usg_pct'], wins)
baseft=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['pfor', 'ft', 'ft_pct', 'ast', 'ast_pct', 'oreb_pct', 'dreb_pct', 'stl', 'blk', 'tov', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
baseft=baseft.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss', 'fouls'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss', 'fouls'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
baseft=baseft.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
baseft[baseft['dummy']==0].reset_index().to_pickle(outdir+'df_ft.pkl')
baseft[baseft['dummy']==1].reset_index().to_pickle('dummy/modeling/df_ft.pkl')

#Offensive Rebound Dataframe
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'p_oreb']+ wincols(['p_time','p_fg2', 'p_pct2', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_dreb', 'p_dreb_pct', 'p_flr_pct', 'p_usg_pct'], wins)
baseorb=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['pfor', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'stl', 'blk', 'tov', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
baseorb=baseorb.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['paga', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'poss', 'fouls'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['paga', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'poss', 'fouls'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
baseorb=baseorb.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
baseorb[baseorb['dummy']==0].reset_index().to_pickle(outdir+'df_orb.pkl')
baseorb[baseorb['dummy']==1].reset_index().to_pickle('dummy/modeling/df_orb.pkl')

#Defensive Rebound Dataframe
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'p_dreb']+ wincols(['p_time','p_fg2', 'p_pct2', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_dreb', 'p_dreb_pct', 'p_flr_pct', 'p_usg_pct'], wins)
basedrb=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['paga', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'stl', 'blk', 'tov', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
basedrb=basedrb.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['pfor', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'poss', 'fouls'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['pfor', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'poss', 'fouls'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
basedrb=basedrb.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
basedrb[basedrb['dummy']==0].reset_index().to_pickle(outdir+'df_drb.pkl')
basedrb[basedrb['dummy']==1].reset_index().to_pickle('dummy/modeling/df_drb.pkl')

#Assist Dataframe
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'p_ast']+ wincols(['p_time','p_fg2', 'p_pct2', 'p_fg3', 'p_pct3', 'p_ft', 'p_ft_pct', 'p_ast', 'p_ast_pct', 'p_tov', 'p_flr_pct', 'p_usg_pct'], wins)
baseast=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['pfor', 'fg2', 'pct2', 'fg3', 'pct3', 'oreb', 'ast', 'ast_pct', 'oreb_pct', 'dreb', 'dreb_pct', 'stl', 'blk', 'tov', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
baseast=baseast.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['paga', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'poss'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['paga', 'oreb', 'oreb_pct', 'dreb', 'dreb_pct', 'poss'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
baseast=baseast.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
baseast[baseast['dummy']==0].reset_index().to_pickle(outdir+'df_ast.pkl')
baseast[baseast['dummy']==1].reset_index().to_pickle('dummy/modeling/df_ast.pkl')

#Steal Dataframe
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'p_stl']+ wincols(['p_time', 'p_stl', 'p_blk', 'p_fouls', 'p_flr_pct', 'p_stops', 'p_stop_pct', 'p_drtg', 'p_usg_pct'], wins)
basestl=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['pfor', 'paga', 'stl', 'blk', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
basestl=basestl.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['pfor', 'ast', 'ast_pct', 'tov', 'poss'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['pfor', 'ast', 'ast_pct', 'tov', 'poss'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
basestl=basestl.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
basestl[basestl['dummy']==0].reset_index().to_pickle(outdir+'df_stl.pkl')
basestl[basestl['dummy']==1].reset_index().to_pickle('dummy/modeling/df_stl.pkl')

#Block Dataframe
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'p_blk']+ wincols(['p_time', 'p_stl', 'p_blk', 'p_fouls', 'p_flr_pct', 'p_stops', 'p_stop_pct', 'p_drtg', 'p_usg_pct'], wins)
baseblk=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['pfor', 'paga', 'stl', 'blk', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
baseblk=baseblk.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['pfor', 'ast', 'ast_pct', 'tov', 'poss'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['pfor', 'ast', 'ast_pct', 'tov', 'poss'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
baseblk=baseblk.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
baseblk[baseblk['dummy']==0].reset_index().to_pickle(outdir+'df_blk.pkl')
baseblk[baseblk['dummy']==1].reset_index().to_pickle('dummy/modeling/df_blk.pkl')

#Turnover Dataframe
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'p_tov']+ wincols(['p_time','p_fg2', 'p_fg3', 'p_ast', 'p_ft', 'p_oreb', 'p_dreb', 'p_tov', 'p_flr_pct', 'p_usg_pct'], wins)
basetov=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['pfor', 'ast_pct', 'oreb_pct', 'dreb_pct', 'tov', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
basetov=basetov.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss', 'stl', 'blk'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss', 'stl', 'blk'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
basetov=basetov.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
basetov[basetov['dummy']==0].reset_index().to_pickle(outdir+'df_tov.pkl')
basetov[basetov['dummy']==1].reset_index().to_pickle('dummy/modeling/df_tov.pkl')

#Double Double Dataframe
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'dubdub']+ wincols(['p_time','p_fg2', 'p_fg3', 'p_ast', 'p_ast_pct', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_dreb', 'p_dreb_pct', \
'p_tov', 'p_flr_pct', 'p_usg_pct', 'dubdub', 'tridub'], wins)
basedd=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['pfor', 'ast_pct', 'oreb_pct', 'dreb_pct', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
basedd=basedd.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss', 'fouls'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss', 'fouls'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
basedd=basedd.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
basedd[basedd['dummy']==0].reset_index().to_pickle(outdir+'df_dd.pkl')
basedd[basedd['dummy']==1].reset_index().to_pickle('dummy/modeling/df_dd.pkl')

#Triple Double Dataframe
pcols=['game_id', 'player_id', 'name', 'team', 'dummy', 'fpts_100', 'tridub']+ wincols(['p_time','p_fg2', 'p_fg3', 'p_ast', 'p_ast_pct', 'p_ft', 'p_ft_pct', 'p_oreb', 'p_oreb_pct', 'p_dreb', 'p_dreb_pct', \
'p_tov', 'p_flr_pct', 'p_usg_pct', 'dubdub', 'tridub'], wins)
basetd=copy.copy(plyragg[pcols])
forcols=['game_id', 'team', 'opp', 'home', 'stadium', 'season', 'game_num', 'rest']+ wincols(['pfor', 'ast_pct', 'oreb_pct', 'dreb_pct', 'poss'], wins)
basetm=copy.copy(teamagg[forcols])
#Joins for team/opp
basetd=basetd.merge(basetm, on=['game_id', 'team'], how='left')
awycols=['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss', 'fouls'], wins, 'd_')
rnm={}
for i in range(len(awycols)):
	rnm[(['game_id', 'team', 'opp']+ wincols(['paga', 'oreb_pct', 'dreb_pct', 'poss', 'fouls'], wins))[i]]=awycols[i]
baseawy=copy.copy(teamagg[list(rnm.keys())].rename(columns=rnm))
basetd=basetd.merge(baseawy, left_on=['game_id', 'opp'], right_on=['game_id', 'team']).drop(columns=['team_y','opp_y']).rename(columns={'team_x': 'team', 'opp_x': 'opp'})
basetd[basetd['dummy']==0].reset_index().to_pickle(outdir+'df_td.pkl')
basetd[basetd['dummy']==1].reset_index().to_pickle('dummy/modeling/df_td.pkl')
"""
