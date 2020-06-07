# import pandas as pd
import argparse
import calendar
import sys
from collections import defaultdict
from datetime import date, timedelta
from pprint import pprint
from typing import List, Tuple
import pickle

import requests
from requests import get
from os import mkdir, path, makedirs
from pathlib import Path

def month_days(year, month):
    num_days = calendar.monthrange(year, month)[1]
    dates = (date(year, month, day) for day in range(1, num_days+1))
    return [d.strftime("%m/%d/%Y") for d in dates]

api = 'https://resultsdb-api.rotogrinders.com/api'

def filter_invalid(responses):
    return (r for r in responses if r != [])

def scrape_day(day):
    day_url = f'{api}/slates?start={day}&id=20'
    print(day_url)
    day_json = get(day_url).json()
    print(day_json)
    slate_ids = [slate['_id'] for slate in day_json]
    for sid in slate_ids:
        scrape_slate(sid)
    return slate_ids

def scrape_slate(slate_id):
    slate_url = f'{api}/contests?slates={slate_id}'
    print(slate_url)
    slate_json = get(slate_url).json()
    print(slate_json)
    contest_ids = [contest['_id'] for contest in slate_json]
    prizes = [contest['prizes'] for contest in slate_json]

    ret = []

    for p in prizes:
        competition = []
        for level in p:
            competition.append({
                'cash': level['cash'],
                'rank': level['maxFinish'],
            })
        ret.append(competition)
    for (cid, ps) in zip(contest_ids, ret):
        scores = scores_for_ranks(cid, (p['rank'] for p in ps))
        for p, score in zip (ps, scores):
            p['score'] = score
    return ret


def scores_for_ranks(contest_id, ranks):
    pages = defaultdict(list)
    for r in ranks:
        pages[r // 50].append(r)
    scores = []
    for page, ranks in pages.items():
        url = f'{api}/entries?_contestId={contest_id}&sortBy=points&order=desc&index={page}'
        entries = get(url).json()['entries']
        scores.extend(entries[r % 50]['points'] for r in ranks)
    return scores

class Contest:

    def __init__(self, _id, prizes, **kwargs):
        ps = [{'cash': l['cash'], 'rank': l['maxFinish']} for l in prizes]
        scores = scores_for_ranks(_id, (p['rank'] for p in ps))
        for l, score in zip(ps, scores):
            l['score'] = score
        top_entries = f'{api}/entries?_contestId={_id}&sortBy=points&order=desc&index={0}'
        self.dict = {'prizes' : ps, 'top_entires': top_entries, **kwargs}


class Slate:

    def __init__(self, _id, **kwargs):
        url = f'{api}/contests?slates={_id}'
        json = get(url).json()
        fields = ['maxEntries', 'maxEntriesPerUser', 'entryFee', 'name', 'siteContestId']
        contests = [Contest(c['_id'], c['prizes'], **extract_fields(c, fields)).dict for c in json]
        self.dict = {'contests': contests, 'slat_url': url, **kwargs}

def extract_fields(d, fields):
    return {f:d[f] for f in fields}

class Day:

    def __init__(self, day):
        url = f'{api}/slates?start={day}&id=20'
        json = get(url).json()
        slate_fields = ['slatePlayers', 'startingPositions', 'slateTypeName']
        slates = [Slate(s['_id'], **extract_fields(s, slate_fields)).dict for s in json]
        self.dict = {
            'slates': slates, 
            'day_url': url,
            'date': day,
        }

description = """
Save competition data from draftkings for a given date range.
"""

def main():
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('month', type=int, help='month to scrape')
    parser.add_argument('year',type=int, help='year to scrape')
    parser.add_argument('--day',type=int, help='day to scrape', required=False)
    parser.add_argument('--dir',type=str, help='where to store data', required=False, default="fantasy_data")
    args = parser.parse_args()
    days = (month_days(args.year, args.month) if args.day is None 
            else [date(args.year, args.month, args.day).strftime("%m/%d/%Y")])
    for day in days:
        print(f"SCRAPING {day}")
        try:
            scraped = Day(day).dict
            Y, M, D = day.split('/')
            dirpath = path.join(args.dir, Y, M)
            Path(dirpath).mkdir(parents=True, exist_ok=True)
            outpath = path.join(dirpath, f'{D}.pkl')
            print(f'Output to {outpath}')


            with open(outpath, 'wb') as f:
                pickle.dump(scraped, f)
        except:
            print(f"Cannot Scrape {day}")

if __name__ == '__main__':
    main()
