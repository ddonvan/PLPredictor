import requests

standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
data = requests.get(standings_url)

from bs4 import BeautifulSoup

soup = BeautifulSoup(data.text)
standings_table = soup.select('table.stats_table')[0]
# get squad links
links = standings_table.find_all('a')
links = [l.get("href") for l in links]
links = [l for l in links if '/squad' in l]

