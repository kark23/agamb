import pandas as pd
import os

dir='trans1/'

#Combine Game Data
first=True
for file in os.listdir(dir):
	if file.startswith('team'):
		print(file)
		if first:
			team=pd.read_pickle(dir+file)
			first=False
		else:
			team=pd.concat([team, pd.read_pickle(dir+file)], ignore_index=True)
team.drop_duplicates(['team','game_id']).to_pickle(dir+'fullteam.pkl')
print(team)
#Combine Player Data
first=True
for file in os.listdir(dir):
	if file.startswith('player'):
		print(file)
		if first:
			plyr=pd.read_pickle(dir+file)
			first=False
		else:
			plyr=pd.concat([plyr, pd.read_pickle(dir+file)], ignore_index=True)
plyr.drop_duplicates(['player_id', 'game_id']).to_pickle(dir+'fullplayer.pkl')

