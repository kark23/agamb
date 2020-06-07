import numpy as np
import pandas as pd
import pickle
import sys
import os

#Helper functions

def safediv(x, y):
	if y!=0:
		return x/y
	else:
		return 0.

def safe_dtparse(x):
	for i in range(len(x)):
		try:
			return pd.to_datetime(x['game_date']+' '+x['wctimestring'], format="%Y-%m-%d %I:%M %p", infer_datetime_format=True).iloc[i]
		except:
			pass
	return np.NaN

class nbatrans:

	def __init__(self, fpath):
		#For now all this instance does is contextualize/transform data
		main=pd.read_csv(fpath)
		self.datmain=main
		#Time zone adjustment dictionary
		self.tz_dct={'MIL':2, 'PHI':3, 'DEN':1, 'SAS':2, 'DAL':2, 'PHX':1, 'WAS':3, 'TOR':3, 'IND':3, 'ORL':3, 'NOK':2,
		'CLE':3, 'NYK':3, 'BOS':3, 'NJN':3, 'DET':3, 'MIA':3, 'MEM':2, 'POR':0, 'MIN':2, 'CHA':3, 'CHI':2, 'SAC':0, 'HOU':2,
		'UTA':1, 'LAC':0, 'SEA':0, 'LAL':0, 'ATL':3, 'GSW':0, 'VAN':0, 'CHH':3, 'NOH':2, 'OKC':2, 'BKN':3, 'NOP':2}
		#Team name change mapping (handle after timezone data to keep relocation accoutning correct)
		self.tm_dct={'VAN':'MEM', 'CHH':'NOP', 'NOK':'NOP', 'NOH':'NOP', 'NJN':'BKN', 'SEA':'OKC'}
		self.uni=list(main['home_team_abbrev'].unique())

	def team_apply(self, x, type):
		#For game/team level putting all aggregations here may be most efficient (if possible)
		ntype=[x for x in ['home','away'] if x!=type][0]
		d = {}
		#Referenced team
		d['team']=x[type+'_team_abbrev'].iloc[0]
		#Opponent
		d['opp']=x[ntype+'_team_abbrev'].iloc[0]
		#Binary 1/0 home/away indicator
		d['home'] = int(type=='home')
		#Game stadium categorical variable
		d['stadium']=x['home_team_abbrev'].iloc[0]
		#West coast time
		d['wct']=safe_dtparse(x)
		#Time adjusted to team reference frame
		try:
			d['adjt']=d['wct']+pd.DateOffset(hours=self.tz_dct[d['team']])
		except:
			d['adjt']=np.NaN
		#Season
		if len(str(x['season'].iloc[0]))<4:
			d['season']=(x['season'].astype(str).str[0]+'0'+x['season'].astype(str).str[1:3]).astype(int).iloc[0]
		else:
			d['season']=int(x['season'].iloc[0])
		#Temporary df to account for sometimes blank last row
		tmp=x[x['score'].notnull()]
		#Points for
		d['pfor']=int(tmp['score'].str.split('-').str[int(type=='home')].iloc[-1])
		#Points Against
		d['paga']=int(tmp['score'].str.split('-').str[int(ntype=='home')].iloc[-1])
		#Spread
		d['spread']=d['pfor']-d['paga']
		#Win indicator
		d['win']=int(d['spread']>0)
		#2p made
		d['fg2']=((x['points_made']==2) & (x[type+'_team_abbrev']==x['event_team'])).sum()
		#2p%
		d['pct2']=safediv(d['fg2'],((x['is_three']==0) & ((x['event_type_de']=='shot') | (x['event_type_de']=='missed_shot')) & (x[type+'_team_abbrev']==x['event_team'])).sum())
		#3p made
		d['fg3']=((x['points_made']==3) & (x[type+'_team_abbrev']==x['event_team'])).sum()
		#3p%
		d['pct3']=safediv(d['fg3'],((x['is_three']==1) & (x[type+'_team_abbrev']==x['event_team'])).sum())
		#Assists
		d['ast']=((x['points_made']>1) & (x['player1_team_abbreviation']==x[type+'_team_abbrev']) & (x['player2_team_abbreviation']==x[type+'_team_abbrev'])).sum()
		#Assist %
		d['ast_pct']=safediv(d['ast'],((x['points_made']>1) & (x[type+'_team_abbrev']==x['event_team'])).sum())
		#ft made
		d['ft']=((x['points_made']==1) & (x[type+'_team_abbrev']==x['event_team'])).sum()
		#ft%
		d['ft_pct']=safediv(d['ft'],((x['event_type_de']=='free-throw') & (x[type+'_team_abbrev']==x['event_team'])).sum())
		#Offensive rebounds
		d['oreb']=((x['is_o_rebound']==1) & (x[type+'_team_abbrev']==x['event_team'])).sum()
		#Offensive rebound %
		d['oreb_pct']=safediv(d['oreb'],(d['oreb']+((x[ntype+'_team_abbrev']==x['event_team']) & (x['is_d_rebound']==1)).sum()))
		#Defensive rebounds
		d['dreb']=((x['is_d_rebound']==1) & (x[type+'_team_abbrev']==x['event_team'])).sum()
		#Defensive rebound %
		d['dreb_pct']=safediv(d['dreb'],(d['dreb']+((x[ntype+'_team_abbrev']==x['event_team']) & (x['is_o_rebound']==1)).sum()))
		#Steals
		d['stl']=((x['is_steal']==1) & (x[type+'_team_abbrev']==x['player2_team_abbreviation'])).sum()
		#Blocks
		d['blk']=((x['is_block']==1) & (x[type+'_team_abbrev']==x['player3_team_abbreviation'])).sum()
		#Turnovers
		d['tov']=((x[type+'_team_abbrev']==x['event_team']) & (x['event_type_de']=='turnover')).sum()
		#Possessions (with reference columns)
		nfg2=((x['points_made']==2) & (x[ntype+'_team_abbrev']==x['event_team'])).sum()
		nfg3=((x['points_made']==3) & (x[ntype+'_team_abbrev']==x['event_team'])).sum()
		fga=((x[type+'_team_abbrev']==x['event_team']) & ((x['event_type_de']=='shot') | (x['event_type_de']=='missed_shot'))).sum()
		nfga=((x[ntype+'_team_abbrev']==x['event_team']) & ((x['event_type_de']=='shot') | (x['event_type_de']=='missed_shot'))).sum()
		fta=((x['event_type_de']=='free-throw') & (x[type+'_team_abbrev']==x['event_team'])).sum()
		nfta=((x['event_type_de']=='free-throw') & (x[ntype+'_team_abbrev']==x['event_team'])).sum()
		noreb=((x['is_o_rebound']==1) & (x[ntype+'_team_abbrev']==x['event_team'])).sum()
		noreb_pct=noreb/(noreb+((x[type+'_team_abbrev']==x['event_team']) & (x['is_d_rebound']==1)).sum())
		ntov=((x[ntype+'_team_abbrev']==x['event_team']) & (x['event_type_de']=='turnover')).sum()
		d['poss']=0.5*((fga+ 0.4*fta- 1.07*d['oreb_pct']* (fga-d['fg2']-d['fg3'])+ d['tov']) + (nfga+ 0.4*nfta- 1.07*noreb_pct*(nfga- nfg2- nfg3)+ ntov))
		#Attempt to add your team gbg aggregations here:
		fouled = x['foul_type'].astype(str) != 'nan'
		d['fouls']=(fouled & (x[type+'_team_abbrev']==x['event_team'])).sum()

		return pd.Series(d, index=list(d.keys()))

	def gbg_agg_team(self, upd=False):
		#Set reference for pandas base df read in during initialization
		base=self.datmain
		#Time from raw data has issues. Hour needs 0 padding and games that go past 12 PM or AM will just roll to 13,14
		#Current derived fields only concerned with beginning time of game, so nulling out issue occurances rather than accounting for time/date rollover
		base['wctimestring']=base['wctimestring'].str.pad(8, side='left', fillchar ='0')
		base.loc[base['wctimestring'].str[:2].astype(int)>12,'wctimestring']=None
		#Create a df from home and away perspective then concatenate
		home=base.groupby(['game_id']).apply(self.team_apply, type='home').reset_index()
		away=base.groupby(['game_id']).apply(self.team_apply, type='away').reset_index()
		agg=pd.concat([home,away], ignore_index=True).replace({'team':self.tm_dct, 'opp':self.tm_dct})
		agg=agg.sort_values(by=['team', 'game_id'])
		#agg['game_num']=agg.groupby(['team']).cumcount()
		#agg['rest']=agg.groupby(['team'])['wct'].diff()
		yr=agg['season'].iloc[0]
		print(agg)
		if upd:
			prior=pd.read_pickle(f'trans1/team{yr}.pkl')
			prior=pd.concat([prior, agg], ignore_index=True)
			prior.to_pickle(f'trans1/team{yr}.pkl')
			#agg.to_pickle(f'trans1/teamupd.pkl')
		else:
			agg.to_pickle(f'trans1/team{yr}.pkl')
		self.df_team=agg

	def pids_apply(self, x):
		#For game/player level putting all aggregations here may be most efficient (if possible)
		d = {}
		ids=[]
		for tm in ['home','away']:
			for plyr in range(1,6):
				ids+=list(x[tm+'_player_'+str(plyr)+'_id'].unique())
		ids=list(set(ids))
		for i in range(34):
			try:
				d['player_'+str(i)]=str(ids[i])
			except:
				d['player_'+str(i)]=None
		return pd.Series(d, index=list(d.keys()))

	def player_apply(self, x, id):
		d={}
		#Player ID
		d['player_id']=x['player_'+str(id)].iloc[0]
		#On court mask
		ocm=((d['player_id']==x['home_player_1_id']) | (d['player_id']==x['home_player_2_id']) | (d['player_id']==x['home_player_3_id']) | (d['player_id']==x['home_player_4_id']) \
		| (d['player_id']==x['home_player_5_id']) | (d['player_id']==x['away_player_1_id']) | (d['player_id']==x['away_player_2_id']) | (d['player_id']==x['away_player_3_id']) \
		| (d['player_id']==x['away_player_4_id']) | (d['player_id']==x['away_player_5_id']))
		#Iterate through lineup columns to identify team/player name
		try:
			tmp=x[ocm].reset_index()
			for tm in ['home','away']:
				for plyr in range(1,6):
					if tmp[tm+'_player_'+str(plyr)+'_id'].iloc[0]==d['player_id']:
						type=tm
						ntype=[x for x in ['home','away'] if x!=type][0]
						d['name']=tmp[tm+'_player_'+str(plyr)].iloc[0]
			d['team']=x[type+'_team_abbrev'].iloc[0]
			#Pull team statistics
			tm=self.df_team
			opp=tm[(tm['team']!=d['team']) & (tm['game_id']==x['game_id'].iloc[0])].to_dict('records')[0]
			tm=tm[(tm['team']==d['team']) & (tm['game_id']==x['game_id'].iloc[0])].to_dict('records')[0]
			#Time played (seconds)
			d['p_time']=(ocm*x['event_length']).sum()
			#2p made
			d['p_fg2']=((x['points_made']==2) & (d['player_id']==x['player1_id'])).sum()
			#2p pct
			d['p_pct2']=safediv(d['p_fg2'],((x['is_three']==0) & ((x['event_type_de']=='shot') | (x['event_type_de']=='missed_shot')) & (d['player_id']==x['player1_id'])).sum())
			#3p made
			d['p_fg3']=((x['points_made']==3) & (d['player_id']==x['player1_id'])).sum()
			#3p%
			d['p_pct3']=safediv(d['p_fg3'],((x['is_three']==1) & (d['player_id']==x['player1_id'])).sum())
			#Assists
			d['p_ast']=((x['points_made']>1) & (x['player1_team_abbreviation']==x[type+'_team_abbrev']) & (x['player2_team_abbreviation']==x[type+'_team_abbrev']) & \
			(d['player_id']==x['player2_id'])).sum()
			#Assist %
			d['p_ast_pct']=safediv(d['p_ast'],(ocm*((x['points_made']>1) & (x[type+'_team_abbrev']==x['event_team']))).sum())
			#ft made
			d['p_ft']=((x['points_made']==1) & (d['player_id']==x['player1_id'])).sum()
			#ft%
			d['p_ft_pct']=safediv(d['p_ft'],((x['event_type_de']=='free-throw') & (d['player_id']==x['player1_id'])).sum())
			#Offensive rebounds
			d['p_oreb']=((x['is_o_rebound']==1) & (d['player_id']==x['player1_id'])).sum()
			#Offensive rebound %
			d['p_oreb_pct']=safediv(d['p_oreb'],((ocm*((x[type+'_team_abbrev']==x['event_team']) & (x['is_o_rebound']==1))).sum() \
			+(ocm*((x[ntype+'_team_abbrev']==x['event_team']) & (x['is_d_rebound']==1))).sum()))
			#Defensive rebounds
			d['p_dreb']=((x['is_d_rebound']==1) & (d['player_id']==x['player1_id'])).sum()
			#Defensive rebound %
			d['p_dreb_pct']=safediv(d['p_dreb'],((ocm*((x[type+'_team_abbrev']==x['event_team']) & (x['is_d_rebound']==1))).sum() \
			+(ocm*((x[ntype+'_team_abbrev']==x['event_team']) & (x['is_o_rebound']==1))).sum()))
			#Steals
			d['p_stl']=((x['is_steal']==1) & (d['player_id']==x['player2_id'])).sum()
			#Blocks
			d['p_blk']=((x['is_block']==1) & (d['player_id']==x['player3_id'])).sum()
			#Turnovers
			d['p_tov']=((d['player_id']==x['player1_id']) & (x['event_type_de']=='turnover')).sum()
			#Fouls
			d['p_fouls']=((d['player_id']==x['player1_id']) & (x['foul_type'].astype(str) != 'nan')).sum()
			#Offensive rtg calculations
			qast=((d['p_time']/(48*60))*(1.14*((tm['ast']- d['p_ast'])/(tm['fg2']+tm['fg3']))))+((((tm['ast']/(48*60))*d['p_time']- d['p_ast'])/ (((tm['fg2']+tm['fg3'])/(48*60)) \
			*d['p_time']- d['p_fg2']- d['p_fg3']))* (1- (d['p_time']/(48*60))))
			fga=(((x['event_type_de']=='shot') | (x['event_type_de']=='missed_shot')) & (d['player_id']==x['player1_id'])).sum()
			tfga=(((x['event_type_de']=='shot') | (x['event_type_de']=='missed_shot')) & (x[type+'_team_abbrev']==x['event_team'])).sum()
			fg_part=(d['p_fg2']+ d['p_fg3'])*(1- .5*(safediv(2*d['p_fg2']+ 3*d['p_fg3'], 2*fga))* qast)
			ast_part=.5* (((tm['pfor']- tm['ft'])- (2*d['p_fg2']+ 3*d['p_fg3']))/ (2* (tfga- fga))) * d['p_ast']
			ft_part=safediv((1-(1-d['p_ft_pct'])**2)*0.4*d['p_ft'],d['p_ft_pct'])
			team_scoring_poss=tm['fg2']+ tm['fg3']+ safediv((1- (1- tm['ft_pct'])**2)* 0.4* tm['ft'], tm['ft_pct'])
			team_play_pct=team_scoring_poss/ (tfga + (tm['ft']/ tm['ft_pct']) * 0.4 + tm['tov'])
			team_orb_weight=((1 - tm['oreb_pct']) * team_play_pct) / ((1- tm['oreb_pct'])* team_play_pct+ tm['oreb_pct']* (1 - team_play_pct))
			orb_part=d['p_oreb']* team_orb_weight* team_play_pct
			fgxposs=(fga-d['p_fg2']- d['p_fg3'])* (1- 1.07* tm['oreb_pct'])
			ftxposs=safediv(((1- d['p_ft_pct'])**2)* 0.4* d['p_ft'],d['p_ft_pct'])
			scposs=(fg_part+ ast_part+ ft_part)* (1- (tm['oreb']/ team_scoring_poss)* team_orb_weight* team_play_pct)+ orb_part
			totposs=scposs+ fgxposs+ ftxposs+ d['p_tov']
			pprod_fg_part=2* (d['p_fg2']+ d['p_fg3']+ 0.5* d['p_fg3'])* (1- 0.5* (safediv(2*d['p_fg2']+ 3*d['p_fg3'], 2* fga)) * qast)
			pprod_ast_part=2* ((tm['fg2']+ tm['fg3']- d['p_fg2']- d['p_fg3']+ 0.5* (tm['fg3']- d['p_fg3']))/ (tm['fg2']+ tm['fg3']- d['p_fg2']- d['p_fg3']))* 0.5* \
			(((tm['pfor']- tm['ft'])- (2*d['p_fg2']+ 3*d['p_fg3']))/ (2* (tfga- fga)))* d['p_ast']
			pprod_orb_part=d['p_oreb']* team_orb_weight* team_play_pct* (tm['pfor'] / (tm['fg2']+ tm['fg3']+ (1- (1- tm['ft_pct'])**2)* 0.4* tm['ft'] *tm['ft_pct']))
			d['p_pprod']=(pprod_fg_part+ pprod_ast_part + d['p_ft'])* (1- (tm['oreb']/ team_scoring_poss)* team_orb_weight* team_play_pct)+ pprod_orb_part
			d['p_ortg']=100*safediv(d['p_pprod'],totposs)
			d['p_flr_pct']=safediv(scposs,totposs)
			#Defensive rtg calculations
			dfga=(((x['event_type_de']=='shot') | (x['event_type_de']=='missed_shot')) & (x[ntype+'_team_abbrev']==x['event_team'])).sum()
			dfg_pct=(opp['fg2']+opp['fg3'])/dfga
			fmwt=(dfg_pct* (1- opp['oreb_pct']))/ (dfg_pct* (1- opp['oreb_pct'])+ (1- dfg_pct)* opp['oreb_pct'])
			stops1=d['p_stl']+ d['p_blk']* fmwt* (1- 1.07* opp['oreb_pct'])+ d['p_dreb']* (1- fmwt)
			stops2=(((dfga- opp['fg2']- opp['fg3']- tm['blk'])/ (48*60))* fmwt* (1- 1.07* opp['oreb_pct'])+ ((opp['tov']- tm['stl'])/ (48*60)))* d['p_time']+ safediv(d['p_fouls'],tm['fouls'])* 0.4* \
			safediv(opp['ft'],opp['ft_pct'])* (1- opp['ft_pct'])**2
			d['p_stops']=stops1+ stops2
			d['p_stop_pct']=safediv(d['p_stops']* 48* 60, tm['poss']* d['p_time'])
			tm_d_rtg=100* safediv(tm['paga'], tm['poss'])
			d_pp_scposs=tm['paga']/ (opp['fg2']+ opp['fg3']+ (1- (1- opp['ft_pct'])**2)* safediv(opp['ft'],opp['ft_pct'])* 0.4)
			stop_pct=(d['p_stops']* (48*60))/ (tm['poss']* d['p_time'])
			d['p_drtg']=tm_d_rtg+ 0.2* (100* d_pp_scposs* (1- d['p_stop_pct'])- tm_d_rtg)
			d['p_usg_pct']=safediv(100 * ((fga+ 0.44* safediv(d['p_ft'],d['p_ft_pct'])+ d['p_tov']) * (48*60)) , (d['p_time'] * (tfga +0.44* safediv(d['p_ft'],d['p_ft_pct'])+ tm['tov'])))
			#Double/Triple Double Metrics
			pts=int((d['p_ft']+ d['p_fg2']*2 +d['p_fg3']*3)>=10)
			reb=int((d['p_oreb']+d['p_dreb'])>=10)
			asst=int(d['p_ast']>=10)
			blk=int(d['p_blk']>=10)
			stl=int(d['p_stl']>=10)
			d['dubdub']=int((pts+reb+asst+blk+stl)>=2)
			d['tridub']=int((pts+reb+asst+blk+stl)>=3)
			d['fpts']=d['p_ast']*1.5+ d['p_blk']*2+ d['dubdub']*1.5+ d['p_dreb']*1.25+ d['p_fg2']*2+ d['p_fg3']*3.5+ d['p_ft']+ d['p_oreb']*1.25+ d['p_stl']*2+ d['tridub']*3+ d['p_tov']*-.5
			return pd.Series(d, index=list(d.keys()))
		#If index error (caused by some games having smaller sets of total players than others), just return none and continue with aggregation
		except IndexError:
			return None
		except Exception as e:
			print(e)

	def gbg_agg_plyr(self, upd=False):
		base=self.datmain
		team=self.df_team
		pids=base.groupby(['game_id']).apply(self.pids_apply).reset_index()
		base=base.merge(pids, on='game_id', how='inner')
		strcols=['player1_id','player2_id','player3_id','home_player_1_id','home_player_2_id','home_player_3_id','home_player_4_id','home_player_5_id',
		'away_player_1_id','away_player_2_id','away_player_3_id','away_player_4_id','away_player_5_id']
		for col in strcols:
			base[col]=base[col].astype(str)
		for id in range(34):
			if id==0:
				agg=base.groupby(['game_id']).apply(self.player_apply, id=id).dropna(subset=['player_id']).reset_index()
			else:
				try:
					tmp=base.groupby(['game_id']).apply(self.player_apply, id=id).dropna(subset=['player_id']).reset_index()
					agg=pd.concat([agg,tmp], ignore_index=True).replace({'team':self.tm_dct})
				except Exception as e:
					print(id, e)
					break
		print(agg)
		yr=team['season'].iloc[0]
		if upd:
			prior=pd.read_pickle(f'trans1/player{yr}.pkl')
			prior=pd.concat([prior, agg], ignore_index=True)
			prior.to_pickle(f'trans1/player{yr}.pkl')
			#agg.to_pickle(f'trans1/playerupd.pkl')
		else:
			agg.to_pickle(f'trans1/player{yr}.pkl')


if __name__=="__main__":
	opt=sys.argv[1]
	if opt=='update':
		yr=opt
		instance=nbatrans(f'raw/pbpupd.csv')
		instance.gbg_agg_team(True)
		instance.gbg_agg_plyr(True)
	if opt=='full':
		for yr in range(2000,2020):
			instance=nbatrans(f'raw/pbp{yr}.csv')
			instance.gbg_agg_team()
			instance.gbg_agg_plyr()
