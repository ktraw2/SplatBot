import json
import urllib.request

class Splatnet:

    def get_json_schedule(self):
        req = urllib.request.Request(
            url="https://splatoon2.ink/data/schedules.json",
            data=None,
            headers={
                'User-Agent': 'SplatBot/1.0 Discord: AdamWang#1770'
            }
        )
        with urllib.request.urlopen(req) as url:
            json_data = json.loads(url.read().decode())
            return json_data

    def get_json_salmon(self):
        req = urllib.request.Request(
            url="https://splatoon2.ink/data/coop-schedules.json",
            data=None,
            headers={
                'User-Agent': 'SplatBot/1.0 Discord: AdamWang#1770'
            }
        )
        with urllib.request.urlopen(req) as url:
            json_data = json.loads(url.read().decode())
            return json_data

    def get_json_gear(self):
        req = urllib.request.Request(
            url="https://splatoon2.ink/data/merchandises.json",
            data=None,
            headers={
                'User-Agent': 'SplatBot/1.0 Discord: AdamWang#1770'
            }
        )
        with urllib.request.urlopen(req) as url:
            json_data = json.loads(url.read().decode())
            return json_data

    def get_json_splatfest(self):
        req = urllib.request.Request(
            url="https://splatoon2.ink/data/festivals.json",
            data=None,
            headers={
                'User-Agent': 'SplatBot/1.0 Discord: AdamWang#1770'
            }
        )
        with urllib.request.urlopen(req) as url:
            json_data = json.loads(url.read().decode())
            return json_data



