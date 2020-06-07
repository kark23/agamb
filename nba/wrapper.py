import nba_scraper.nba_scraper as ns
import pandas as pd
import catboost
import time
import os
import sys

yr=sys.argv[1]
os.chdir('data')

tm_map={'PHO':'PHX'}

pbp=pd.read_csv(f'raw/pbp{yr}.csv')
print(pbp)
i=pbp['game_id'].max()+1
errs=0
first=True
while errs<=10:
	try:
		if first:
			upd=ns.scrape_game([i])
			first=False
		else:
			upd=pd.concat([upd, ns.scrape_game([i])], ignore_index=True)
	except:
		print(i, 'error!')
		errs+=1
	i+=1
i+=100
try:
	pbp=pd.concat([pbp, upd], ignore_index=True).drop_duplicates()
	pbp.to_csv(f'raw/pbp{yr}.csv')
	upd.to_csv(f'raw/pbpupd.csv')
except:
	pass

strt=time.time()
os.system(f'python3 nba_transform.py update')
print('trans1', time.time()-strt)
os.system(f'python3 combine.py')

dummy=pd.read_csv('dummy/dummyref.csv')
print(dummy)
tm=pd.read_pickle('trans1/fullteam.pkl')
#tmdct={}
#for t in tm['team'].unique():
	#tmdct[t]=tm[(tm['team']==t) & (tm['season']==int(yr)+1)]['game_num'].max()
ply=pd.read_pickle('trans1/fullplayer.pkl')
tm=dummy[['Game Info', 'TeamAbbrev']].copy().rename(columns={'TeamAbbrev': 'team'}).drop_duplicates()
gm=dummy[['Game Info']].copy().drop_duplicates().reset_index()
gm['game_id']=i+ gm.index
tm=tm.merge(gm)
match=tm['Game Info'].str.split(' ').str[0].str.split('@')
tm['home']=(match.str[1]==tm['team']).astype(int)
tm['opp']=match.str[1]
tm.loc[tm['home'] == 1, 'opp']= match.str[0]
tm['stadium']=match.str[1]
tm['wct']=pd.to_datetime(tm['Game Info'].str.split(' ').str[1]+ ' '+ tm['Game Info'].str.split(' ').str[2], format="%d/%m/%Y %I:%M%p", infer_datetime_format=True, utc=False)
tm['adjt']= tm['wct'].dt
tm['season']= int(yr)+ 1
tm['pfor']=0
tm['paga']=0
tm['spread']=0
tm['win']=0
tm['fg2']=0
tm['pct2']=0
tm['fg3']=0
tm['pct3']=0
tm['ast']=0
tm['ast_pct']=0
tm['ft']=0
tm['ft_pct']=0
tm['oreb']=0
tm['oreb_pct']=0
tm['dreb']=0
tm['dreb_pct']=0
tm['stl']=0
tm['blk']=0
tm['tov']=0
tm['poss']=0
tm['fouls']=0
tm[['team', 'opp', 'stadium']]=tm[['team', 'opp', 'stadium']].replace(tm_map)
#tm['game_num']=tm['team'].map(tmdct).astype(int)
#tm['rest']=0
tm=tm.replace(tm_map)
tm=tm.drop(columns=['Game Info'])
tm.to_pickle('dummy/tm.pkl')

plyr=dummy.replace(tm_map).drop(columns=['Position', 'Name + ID', 'ID', 'Roster Position', 'Game Info', 'AvgPointsPerGame']).copy()
plyr=plyr.merge(tm[['game_id', 'team']], left_on='TeamAbbrev', right_on='team')
plyr=plyr.merge(ply[['player_id', 'name', 'team']].drop_duplicates(), left_on=['team', 'Name'], right_on=['team', 'name'], how='left')
plyr=plyr.drop(columns=['TeamAbbrev', 'Name'])
plyr['p_time']=0
plyr['p_fg2']=0
plyr['p_pct2']=0
plyr['p_fg3']=0
plyr['p_pct3']=0
plyr['p_ast']=0
plyr['p_ast_pct']=0
plyr['p_ft']=0
plyr['p_ft_pct']=0
plyr['p_oreb']=0
plyr['p_oreb_pct']=0
plyr['p_dreb']=0
plyr['p_dreb_pct']=0
plyr['p_stl']=0
plyr['p_blk']=0
plyr['p_tov']=0
plyr['p_fouls']=0
plyr['p_pprod']=0
plyr['p_ortg']=0
plyr['p_flr_pct']=0
plyr['p_stops']=0
plyr['p_stop_pct']=0
plyr['p_drtg']=0
plyr['p_usg_pct']=0
plyr['dubdub']=0
plyr['tridub']=0
plyr.to_pickle('dummy/ply.pkl')

strt=time.time()
os.system(f'python3 nba_transform2.py update')
print('trans2', time.time()-strt)

pscale={'p_ast':1.5, 'p_blk':2, 'dubdub':1.5, 'p_dreb':1.25, 'p_fg2':2, 'p_fg3':3.5, 'p_ft':1, 'p_oreb':1.25, 'p_stl':2, 'tridub':3, 'p_tov':-.5}
vars=['p_ast', 'p_blk', 'p_dreb', 'p_fg2', 'p_fg3', 'p_ft', 'p_oreb', 'p_stl', 'p_tov']
dnames=['ast', 'blk', 'drb', 'fg2', 'fg3', 'ft', 'orb', 'stl', 'tov']

xvars={
'p_ast':
['dreb_100', 'p_ast_10', 'p_usg_pct_20', 'pct2_20', 'p_time_2', 'ast_20', 'home', 'p_ft_pct_100', 'fg3_20', 'p_ast_50', 'p_ast_pct_100', 'p_flr_pct_5', 'blk_100', 'p_ft_100', 'p_usg_pct_5', 'game_num', 'p_ast_2',
'p_ast_5', 'p_flr_pct_20', 'poss_20', 'dreb_20', 'ast_100', 'tov_20', 'stadium', 'p_ast_20', 'p_ast_pct_20', 'p_time_10', 'd_paga_20', 'p_tov_100', 'poss_100', 'p_time_100', 'p_pct3_100', 'p_ast_pct_5', 'fg2_100',
'dreb_pct_100', 'p_ast_100', 'p_usg_pct_100', 'fg3_100', 'p_fg2_20', 'p_ft_20', 'p_fg2_100', 'fg2_20', 'p_pct2_100', 'pfor_100', 'season', 'p_fg3_20', 'p_time_50', 'pfor_5', 'd_paga_100', 'p_flr_pct_100', 'pfor_20',
'p_ast_pct_50', 'p_fg3_100', 'pct2_100', 'tov_100', 'dreb_pct_20', 'p_tov_50', 'stl_100'],
'p_blk':
['pfor_50', 'd_poss_2', 'p_drtg_100', 'p_usg_pct_20', 'home', 'p_stops_50', 'p_blk_100', 'blk_100', 'p_stop_pct_100', 'd_tov_100', 'p_flr_pct_10', 'p_stl_50', 'p_flr_pct_20', 'p_time_20', 'd_pfor_20', 'paga_50',
'd_poss_50', 'p_fouls_20', 'p_stop_pct_10', 'stadium', 'p_stops_5', 'p_blk_20', 'paga_100', 'p_time_10', 'poss_50', 'p_usg_pct_50', 'poss_100', 'p_time_100', 'p_stl_10', 'd_pfor_50', 'p_usg_pct_100', 'p_stl_5',
'p_drtg_50', 'd_poss_20', 'p_usg_pct_10', 'pfor_100', 'd_tov_50', 'p_drtg_20', 'p_blk_50', 'p_stl_100', 'season', 'p_stl_20', 'p_time_50', 'p_time_5', 'p_fouls_50', 'blk_50', 'p_flr_pct_50', 'p_stop_pct_50',
'p_flr_pct_100', 'p_drtg_10', 'p_stops_10', 'p_stops_100', 'd_poss_100', 'p_fouls_100', 'p_stop_pct_20', 'd_poss_10'],
'p_dreb':
['dreb_100', 'p_oreb_pct_50', 'dreb_10', 'd_oreb_20', 'p_oreb_100', 'd_dreb_50', 'p_dreb_pct_100', 'p_time_2', 'home', 'p_stops_50', 'oreb_pct_100', 'd_oreb_pct_50', 'd_pfor_5', 'p_ft_100', 'game_num', 'fg2_50',
'p_oreb_pct_20', 'p_ft_pct_20', 'd_pfor_20', 'p_time_20', 'paga_50', 'd_poss_50', 'p_fg2_50', 'dreb_50', 'poss_20', 'p_pct3_10', 'dreb_2', 'p_pct2_50', 'p_dreb_50', 'paga_100', 'poss_50', 'd_pfor_100', 'p_usg_pct_50',
'poss_100', 'p_time_100', 'oreb_50', 'p_oreb_pct_100', 'dreb_pct_100', 'paga_10', 'fg3_100', 'p_usg_pct_100', 'p_drtg_50', 'p_ft_20', 'p_fg2_100', 'p_ft_pct_50', 'fg2_20', 'd_poss_5', 'p_pct2_100', 'p_dreb_100',
'p_oreb_20', 'dreb_pct_5', 'season', 'd_oreb_pct_100', 'p_oreb_50', 'p_dreb_pct_50', 'p_flr_pct_50', 'p_time_50', 'd_oreb_5', 'p_dreb_pct_10', 'p_flr_pct_100', 'p_stop_pct_50', 'tov_100', 'dreb_pct_20', 'd_poss_100',
'p_ft_50', 'd_oreb_pct_20', 'p_dreb_10'],
'p_fg2':
['p_oreb_pct_50', 'pfor_50', 'dreb_pct_50', 'fg2_10', 'p_oreb_100', 'p_usg_pct_20', 'home', 'p_ft_pct_100', 'ast_50', 'p_ast_50', 'p_ast_pct_100', 'p_ft_100', 'p_usg_pct_5', 'game_num', 'fg2_50', 'p_flr_pct_10', 'p_stl_50',
'p_fg2_50', 'p_fg2_5', 'ast_100', 'fg2_5', 'p_pct2_50', 'p_ast_20', 'p_ast_pct_20', 'p_fg3_50', 'd_paga_20', 'p_fg2_10', 'p_usg_pct_50', 'poss_50', 'p_tov_100', 'p_usg_pct_2', 'poss_100', 'p_time_100', 'p_pct3_100',
'p_oreb_pct_100', 'fg2_100', 'dreb_pct_100', 'p_ast_100', 'p_tov_20', 'p_usg_pct_100', 'rest', 'p_fg2_20', 'p_fg2_100', 'fg2_20', 'd_paga_10', 'p_pct2_100', 'p_pct3_5', 'pfor_100', 'p_pct2_5', 'p_flr_pct_2', 'p_stl_100',
'season', 'p_oreb_50', 'p_time_5', 'p_time_50', 'p_flr_pct_50', 'd_paga_100', 'p_flr_pct_100', 'pfor_20', 'p_ast_pct_50', 'p_fg3_100', 'p_pct3_50', 'p_ft_50', 'd_poss_100', 'p_tov_50', 'pct2_100', 'tov_100', 'stl_100'],
'p_fg3':
['p_oreb_pct_50', 'dreb_pct_50', 'p_fg3_5', 'oreb_pct_50', 'fg3_20', 'p_oreb_100', 'fg3_5', 'p_usg_pct_20', 'home', 'p_ft_pct_100', 'ast_50', 'p_ast_50', 'p_ast_pct_100', 'oreb_pct_100', 'p_flr_pct_5', 'p_ft_100',
'p_usg_pct_5', 'game_num', 'p_oreb_pct_20', 'p_stl_50', 'd_paga_50', 'p_flr_pct_20', 'p_fg2_50', 'poss_20', 'p_pct3_10', 'ast_100', 'p_pct2_50', 'p_ast_pct_20', 'p_fg3_50', 'd_paga_20', 'poss_50', 'p_tov_100', 'p_usg_pct_2',
'poss_100', 'p_time_100', 'p_pct3_100', 'p_pct3_20', 'oreb_50', 'p_oreb_pct_100', 'p_fg3_2', 'dreb_pct_100', 'fg3_50', 'p_tov_20', 'fg3_100', 'p_usg_pct_100', 'p_fg2_20', 'p_fg2_100', 'p_ft_pct_50', 'd_paga_10',
'p_pct2_100', 'p_pct2_20', 'p_stl_100', 'season', 'd_dreb_pct_50', 'd_paga_5', 'p_fg3_20', 'p_stl_20', 'p_pct3_2', 'p_time_5', 'p_time_50', 'd_paga_100', 'p_flr_pct_100', 'pfor_20', 'p_ast_pct_50', 'p_fg3_100',
'p_pct3_50', 'poss_10', 'fg3_2', 'p_fg3_10', 'fg3_10'],
'p_ft':
['ft_100', 'p_oreb_pct_50', 'pfor_50', 'ft_10', 'ast_pct_50', 'p_oreb_100', 'p_usg_pct_20', 'home', 'p_ft_pct_100', 'ast_50', 'p_ast_pct_100', 'blk_100', 'oreb_pct_100', 'p_tov_50', 'p_ft_100', 'game_num', 'p_pct2_10',
'ft_20', 'p_flr_pct_20', 'p_time_20', 'ft_pct_50', 'd_fouls_50', 'p_fg2_50', 'ast_pct_100', 'ast_100', 'd_fouls_20', 'p_ast_pct_20', 'p_fg3_50', 'p_usg_pct_50', 'p_tov_100', 'p_usg_pct_2', 'poss_100', 'p_time_100',
'p_pct3_100', 'p_oreb_pct_100', 'p_ast_100', 'p_usg_pct_100', 'p_fg2_20', 'p_ft_20', 'p_fg2_100', 'p_ft_pct_50', 'ft_50', 'p_pct2_100', 'p_usg_pct_10', 'd_fouls_10', 'pfor_100', 'd_fouls_100', 'p_stl_100', 'season',
'p_oreb_50', 'p_time_5', 'p_time_50', 'p_flr_pct_50', 'p_flr_pct_100', 'tov_100', 'p_ast_pct_50', 'p_fg3_100', 'p_pct3_50', 'p_ft_50', 'ft_pct_100'],
'p_oreb':
['dreb_100', 'p_oreb_pct_50', 'pfor_50', 'd_poss_2', 'd_dreb_pct_100', 'dreb_pct_50', 'oreb_20', 'oreb_pct_50', 'p_oreb_100', 'd_dreb_50', 'oreb_5', 'dreb_5', 'home', 'p_ft_pct_100', 'p_usg_pct_20', 'blk_100',
'oreb_pct_100', 'p_ft_100', 'game_num', 'oreb_pct_20', 'oreb_100', 'p_time_20', 'oreb_pct_5', 'd_poss_50', 'p_fg2_50', 'dreb_20', 'poss_20', 'p_pct2_50', 'stadium', 'd_dreb_20', 'd_dreb_100', 'p_dreb_50', 'p_time_10',
'p_dreb_pct_20', 'p_usg_pct_50', 'p_dreb_20', 'poss_50', 'poss_100', 'tov_50', 'p_time_100', 'oreb_50', 'p_oreb_pct_100', 'dreb_pct_100', 'p_usg_pct_100', 'p_fg2_20', 'p_fg2_100', 'p_ft_pct_50', 'd_poss_20', 'd_poss_5',
'p_pct2_100', 'pfor_100', 'season', 'd_dreb_pct_50', 'p_oreb_50', 'd_dreb_pct_20', 'p_dreb_pct_50', 'p_flr_pct_50', 'p_time_50', 'p_flr_pct_100', 'tov_100', 'dreb_pct_20', 'd_poss_100', 'p_ft_50', 'd_oreb_pct_20', 'stl_100'],
'p_stl':
['d_poss_2', 'p_drtg_100', 'p_stops_50', 'd_tov_5', 'p_blk_100', 'game_num', 'p_stop_pct_100', 'd_tov_100', 'p_flr_pct_10', 'd_ast_10', 'd_tov_20', 'p_stl_50', 'p_flr_pct_20', 'p_time_20', 'paga_50', 'stl_20', 'd_poss_50',
'p_stop_pct_10', 'stl_5', 'p_stops_20', 'stadium', 'p_stops_5', 'paga_100', 'stl_50', 'p_time_10', 'p_usg_pct_50', 'poss_100', 'p_time_100', 'stl_2', 'd_tov_2', 'p_stl_10', 'rest', 'p_usg_pct_100', 'p_stl_5', 'p_drtg_50',
'pfor_10', 'd_tov_10', 'd_poss_20', 'd_poss_5', 'p_drtg_20', 'pfor_100', 'd_tov_50', 'p_blk_50', 'p_stl_100', 'season', 'p_stl_20', 'p_time_50', 'd_ast_50', 'p_flr_pct_50', 'stl_10', 'p_stop_pct_50', 'p_flr_pct_100',
'pfor_20', 'poss_10', 'p_stops_10', 'p_stops_100', 'p_stop_pct_20', 'p_fouls_100', 'p_stop_pct_5', 'd_poss_10', 'stl_100'],
'p_tov':
['d_poss_2', 'd_dreb_pct_100', 'dreb_pct_50', 'oreb_pct_50', 'ast_pct_50', 'p_oreb_100', 'p_usg_pct_20', 'home', 'p_ast_50', 'oreb_pct_100', 'd_stl_2', 'p_ft_100', 'p_tov_50', 'game_num', 'p_flr_pct_10', 'p_flr_pct_20',
'p_time_20', 'tov_10', 'd_poss_50', 'p_fg2_50', 'ast_pct_100', 'poss_20', 'tov_20', 'p_ast_20', 'p_dreb_50', 'p_fg3_50', 'p_time_10', 'p_fg2_10', 'poss_50', 'p_usg_pct_50', 'tov_50', 'p_tov_100', 'poss_100', 'p_time_100',
'poss_5', 'dreb_pct_100', 'p_ast_100', 'p_tov_20', 'p_usg_pct_100', 'p_fg2_20', 'd_stl_100', 'd_poss_20', 'p_dreb_100', 'pfor_100', 'season', 'p_fg3_20', 'p_oreb_50', 'p_time_5', 'p_time_50', 'p_flr_pct_50', 'd_stl_10',
'd_stl_20', 'p_flr_pct_100', 'pfor_20', 'poss_10', 'p_fg3_100', 'tov_100', 'p_ft_50', 'd_stl_50', 'd_stl_5']
}

plyr=pd.read_pickle('dummy/ply.pkl')
plyr['fpts']=0
cb=catboost.CatBoostRegressor(iterations=20000, learning_rate=.1, depth=3, od_type='Iter', od_wait=2000)
varl=[]
frist=True
for var, dname in zip (vars, dnames):
	plyvar=pd.read_pickle(f'dummy/modeling/df_{dname}.pkl')
	print(dname, plyvar)
	#print(var, plyvar[xvars[var]])
	xvars[var]=[i for i in xvars[var] if i in list(plyvar.columns)]
	mod=cb.load_model('../modeling/catmods/'+dname)
	varl.append('pred_'+var)
	plyvar['pred_'+var]=cb.predict(plyvar[xvars[var]])
	if first:
		plyr=plyr.merge(plyvar[['name', 'pred_'+var, 'fpts_100']], on='name')
		first=False
	else:
		plyr=plyr.merge(plyvar[['name', 'pred_'+var]], on='name')
	plyr['fpts']+=plyr['pred_'+var]*pscale[var]
mod=cb.load_model('../modeling/catmods/dd')
plyr['pred_dubdub']=mod.predict(plyr[varl])
plyr['fpts']+=plyr['pred_dubdub']*pscale['dubdub']
mod=cb.load_model('../modeling/catmods/td')
plyr['pred_tridub']=mod.predict(plyr[varl])
plyr['fpts']+=plyr['pred_tridub']*pscale['tridub']
plyr.to_pickle('pred/predictions.pkl')
