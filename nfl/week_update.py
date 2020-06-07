import glob
import os
import sys
import pandas as pd

yr=str(sys.argv[1])
wk=str(sys.argv[2])
list_of_files=glob.glob('data/mainraw/*')
latest_file=max(list_of_files, key=os.path.getctime)
base=pd.read_csv(latest_file)
updno=str(int(latest_file.split('_')[1].split('.')[0])+1)
print('Rscript update.R '+yr+' '+wk)
os.system('Rscript update.R '+yr+' '+wk)
upd=pd.read_csv('data/update/update.csv')
main=pd.concat([base,upd],ignore_index=True, sort=False).drop_duplicates().reset_index()
main.to_csv('data/mainraw/agg_'+updno+'.csv')

