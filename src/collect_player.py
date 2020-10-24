import requests
from bs4 import BeautifulSoup

from models.models import Player
from models.database import db_session

team_list = ['g', 'db', 't', 'c', 'd', 's', 'l', 'h', 'e', 'm', 'f', 'b']
team_list_ja = ['巨人', '横浜', '阪神', '広島', '中日', 'ヤクルト', '西武', 'ソフトバンク', '楽天', 'ロッテ', '日本ハム', 'オリックス']


def collect():
    team = team_list[0]
    url = "https://npb.jp/bis/teams/rst_{}.html".format(team)
    html = requests.get(url)
    soup = BeautifulSoup(html.content, "html.parser")
    plist = soup.find_all(class_="rosterRegister")
    for i in range(len(plist)):
        if i != 0:
            p = plist[i]
            name = p.text.replace("　", "")
            team_ja = team_list_ja[team_list.index(team)]
            player = Player(name, team_ja)
            db_session.add(player)
    db_session.commit()

if __name__ == '__main__':
    collect()