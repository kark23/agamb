import nba_scraper.nba_scraper as ns
import pandas as pd
import time
import os
import sys

def date_app(maindir,spec,df=None,write=True):
	strt=time.time()
	i=0
	while True:
		try:
			if df is None:
				main=pd.read_csv(maindir)
			else:
				main=df
			app=ns.scrape_date_range(spec,spec)
			main=pd.concat([main,app],ignore_index=True,sort=False).drop_duplicates()
			if write:
				main.to_csv(maindir)
			print(str(time.time()-strt)+' seconds')
			return main
		except Exception as e:
			print(e)
			print('retrying')
			i+=1
			if i>10:
				print('failed 10 times, exiting')
				sys.exit()

if __name__=="__main__":
	opt=sys.argv[1]
	beg=sys.argv[2]
	end=sys.argv[3]
	dir=sys.argv[4]
	first=True
	if opt=='update':
		for dt in pd.date_range(beg,end):
			if first:
				df=date_app(dir,dt)
				first=False
			else:
				df=date_app(dir,dt,df)
	if opt=='full':
		try:
			os.mkdir(dir+'/errors')
		except:
			pass
		for yr in range(int(beg),int(end)+1):
			ssn=str(yr)[0]+str(yr)[2:]
			try:
				os.mkdir(dir+'/'+str(yr))
			except:
				pass
			for id in range(int(f"{ssn}00001"), int(f"{ssn}01231")):
				if os.path.exists(dir+'/'+str(yr)+'/'+str(id)+'.csv'):
					pass
				else:
					strt=time.time()
					try:
						df=ns.scrape_game([id])
						df.to_csv(dir+'/'+str(yr)+'/'+str(id)+'.csv')
					except:
						print('error '+str(id))
						file=open(dir+'/errors/error'+str(id)+'.txt', "w")
						file.close()
					print(str(time.time()-strt)+' seconds')
	else:
		print('invalid option')
		sys.exit()
