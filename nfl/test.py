import nfldb

db = nfldb.connect()

query= """

with pp as
(
	select
		player_id,
		gsis_id,
  		SUM(puntret_yds) AS puntret_yds,
		SUM(receiving_rec) AS receiving_rec,
  		SUM(receiving_tar) AS receiving_tar,
  		SUM(receiving_tds) AS receiving_tds,
  		SUM(receiving_twopta) AS receiving_twopta,
  		SUM(receiving_twoptm) AS receiving_twoptm,
  		SUM(receiving_twoptmissed) AS receiving_twoptmissed,
  		SUM(receiving_yac_yds) AS receiving_yac_yds,
  		SUM(receiving_yds) AS receiving_yds,
  		SUM(rushing_att) AS rushing_att,
  		SUM(rushing_loss) AS rushing_loss,
  		SUM(rushing_loss_yds) AS rushing_loss_yds,
  		SUM(rushing_tds) AS rushing_tds,
  		SUM(rushing_twopta) AS rushing_twopta,
  		SUM(rushing_twoptm) AS rushing_twoptm,
  		SUM(rushing_twoptmissed) AS rushing_twoptmissed,
  		SUM(rushing_yds) AS rushing_yds
	from play_player
	group by player_id, gsis_id
),
g as
(
	select
		gsis_id,
		week,
		season_year,
		season_type
	from game
),
p as
(
	select
		player_id,
		gsis_name,
		first_name,
		last_name
	from player
)
select * from (
select sum(rushing_tds) as sm, gsis_name, player_id, season_year
from pp
left join g using (gsis_id)
left join p using (player_id)
--where sm>1500
group by season_year, gsis_name, player_id
) foo where sm>10

"""

playrec=[]
with nfldb.Tx(db) as cursor:
	cursor.execute(query)
	for row in cursor.fetchall():
		print row
		playrec.append(row)

#for i in range(20):
#	print playrec[i]
