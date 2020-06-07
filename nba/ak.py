import requests

date = '03/05/2020'
url = f'https://resultsdb-api.rotogrinders.com/api/slates?start={date}&id=20'
url= 'https://resultsdb-api.rotogrinders.com/api/contests?slates=5e61930d8e77912e08278d5a'
print(url)
r = requests.get(url)
json = r.json()
print(r.json())


