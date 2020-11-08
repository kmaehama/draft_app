from flask import Flask, render_template, request, session, redirect, url_for
from models.models import Player, User
from models.database import db_session
from src.collect_player import collect
from app import key
from hashlib import sha256
from sqlalchemy import desc
import json


app = Flask(__name__)
app.secret_key = key.SECRET_KEY


@app.route("/login",methods=["post"])
def login():
    user_name = request.form["user_name"]
    user = User.query.filter_by(user_name=user_name).first()
    if user:
        password = request.form["password"]
        hashed_password = sha256((user_name + password + key.SALT).encode("utf-8")).hexdigest()
        if user.hashed_password == hashed_password:
            session["user_name"] = user_name
            return redirect(url_for("index"))
        else:
            return redirect(url_for("top",status="wrong_password"))
    else:
        return redirect(url_for("top",status="user_notfound"))


@app.route("/")
@app.route("/index")
def index():
    if "user_name" in session:
        dteam = session["user_name"]
        return render_template("index.html", name=dteam)
    else:
        return redirect(url_for("top", status="logout"))

@app.route("/nominate")
def nominate():
    if "user_name" in session:
        #いま自分の番かどうか判定するための変数
        with open("app/tmp/tmp.json", "r") as f:
            d = json.load(f)
        teams = d["teams"]
        rank = d["now_rank"]
        now_team = d["now_team"]

        your_turn = False
        if rank != 1:
            if session["user_name"] == teams[now_team]:
                your_turn = True
        #1巡目指名のときのための変数
        else:
            with open("app/tmp/dora1.json", "r") as f:
                dora1 = json.load(f)
            dora1already = dora1["already"]

            if False in dora1already:
                if teams[dora1already.index(False)] == session["user_name"]:
                    your_turn = True

        return render_template("nominate.html", rank=rank, your_turn=your_turn, now_team=teams[now_team])
    else:
        return redirect(url_for("top", status="logout"))


@app.route("/nominate",methods=["post"])
def nominate_post():
    dteam = session["user_name"]
    name = request.form["name"]
    team = request.form["team"]
    position = request.form["position"]

    with open("app/tmp/tmp.json", "r") as f:
        d = json.load(f)
    rank = d["now_rank"]
    teams = d["teams"]
    now_team = d["now_team"]
    next_rank = rank
    next_team = now_team

    can_nominate = False
    your_turn = True
    try:
        #入力された選手が存在しなければエラーになる
        p = db_session.query(Player).filter(Player.name==name).filter(Player.team==team).first()
        if p.rank == 0:
            can_nominate = True
            if rank != 1:
                p.dteam = dteam
                p.rank = rank
                p.position = position
                db_session.add(p)
                db_session.commit()

                nominated = {"dteam": dteam, "name": name, "position": position, "team": team}
                if now_team == 0 and rank % 2 == 0:
                    all_nominated = {1: nominated}
                    with open("app/tmp/recently.json", "w") as f:
                        json.dump(all_nominated, f)
                elif now_team == 11 and rank % 2 == 1:
                    all_nominated = {12: nominated}
                    with open("app/tmp/recently.json", "w") as f:
                        json.dump(all_nominated, f)
                else:
                    with open("app/tmp/recently.json", "r") as f:
                        all_nominated = json.load(f)
                    all_nominated[now_team+1] = nominated
                    with open("app/tmp/recently.json", "w") as f:
                        json.dump(all_nominated, f)

                msg = "{}が第{}順で{}({}、{})を指名しました。".format(dteam, rank, name, team, position)
                print(msg)
            else:
                with open("app/tmp/dora1.json", "r") as f:
                    dora1 = json.load(f)
                dora1already = dora1["already"]
                dora1["dora1list"][dora1already.index(False)] = name
                dora1["positions"][dora1already.index(False)] = position
                dora1["already"][dora1already.index(False)] = True
                with open("app/tmp/dora1.json", "w") as f:
                    json.dump(dora1, f)
                print("第1順選択希望選手")
                print(dteam)
                print(name)
                print(position)
                print(team)
                
            if rank != 1:
                if rank % 2 == 0:
                    if now_team == len(teams) - 1:
                        d["now_rank"] += 1
                        next_rank = d["now_rank"]
                    else:
                        d["now_team"] += 1
                        next_team = d["now_team"]
                        your_turn = False
                else:
                    if now_team == 0:
                        d["now_rank"] += 1
                        next_rank = d["now_rank"]
                    else:
                        d["now_team"] -= 1
                        next_team = d["now_team"]
                        your_turn = False
                
                with open("app/tmp/tmp.json", "w") as f:
                    json.dump(d, f)
            else:
                your_turn = False
        else:
            print("鴨川です。")
    except Exception as e:
        print(e)
        print("その選手は存在しません。")
    return render_template("nominate.html", name=name, team=team, position=position, rank=next_rank, status=can_nominate, your_turn=your_turn, now_team=teams[next_team])


@app.route("/member")
def member():
    if "user_name" in session:
        dteam = session["user_name"]
        players = db_session.query(Player).filter(Player.dteam==dteam).order_by(Player.rank).all()
        return render_template("member.html", name=dteam, players=players)
    else:
        return redirect(url_for("top", status="logout"))


@app.route("/all")
def show_all():
    with open("app/tmp/tmp.json", "r") as f:
        d = json.load(f)
    teams = d["teams"]
    now_rank = d["now_rank"]
    all_list = {}
    for team in teams:
        team_players = db_session.query(Player).filter(Player.dteam==team).order_by(Player.rank).all()
        plist = []
        for player in team_players:
            plist.append(player.name)
        all_list[team] = plist
    return render_template("all.html", teams=teams, all_list=all_list, now_rank=now_rank)



@app.route("/registar",methods=["post"])
def registar():
    user_name = request.form["user_name"]
    user = User.query.filter_by(user_name=user_name).first()
    if user:
        return redirect(url_for("newcomer",status="exist_user"))
    else:
        password = request.form["password"]
        hashed_password = sha256((user_name + password + key.SALT).encode("utf-8")).hexdigest()
        user = User(user_name, hashed_password)
        db_session.add(user)
        db_session.commit()
        session["user_name"] = user_name
        return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("user_name", None)
    return redirect(url_for("top",status="logout"))


@app.route("/top")
def top():
    status = request.args.get("status")
    return render_template("top.html",status=status)


@app.route("/newcomer")
def newcomer():
    status = request.args.get("status")
    return render_template("newcomer.html",status=status)


@app.route("/setting")
def setting():
    if "user_name" in session:
        if session["user_name"] == "Master":
            return render_template("setting.html")
        else:
            return redirect(url_for("top", status="logout"))
    else:
        return redirect(url_for("top", status="logout"))


@app.route("/setting", methods=["post"])
def create():
    #チーム（アカウント）の作成
    db_session.query(User).delete()
    teams = []
    for i in range(1, 13):
        user_name = request.form["team{}".format(i)]
        teams.append(user_name)
        password = request.form["password{}".format(i)]
        hashed_password = sha256((user_name + password + key.SALT).encode("utf-8")).hexdigest()
        user = User(user_name, hashed_password)
        db_session.add(user)

    with open("app/tmp/secret.json", "r") as f:
        secret = json.load(f)
    manager_name = secret["user_name"]
    manager_pass = secret["password"]
    manager_hashed_pass = sha256((manager_name + manager_pass + key.SALT).encode("utf-8")).hexdigest()
    manager = User(manager_name, manager_hashed_pass)
    db_session.add(manager)
    db_session.commit()

    #選手データベースの作成
    db_session.query(Player).delete()
    collect()

    #jsonファイルの作成
    d = {}
    d["teams"] = teams
    d["now_rank"] = 1
    d["now_team"] = 0 
    with open('app/tmp/tmp.json', 'w') as f:
        json.dump(d, f)

    dora1 = {}
    dora1list = []
    positions = []
    dora1already = []
    for i in range(len(teams)):
        dora1list.append("")
        positions.append("")
        dora1already.append(False)
    dora1["dora1list"] = dora1list
    dora1["positions"] = positions
    dora1["already"] = dora1already
    with open('app/tmp/dora1.json', 'w') as f:
        json.dump(dora1, f)

    return render_template("top.html",status="logout")


@app.route("/dora1")
def dora1():
    if "user_name" in session:
        if session["user_name"] == "Master":
            with open("app/tmp/dora1.json", "r") as f:
                dora1 = json.load(f)
            dora1list = dora1["dora1list"]
            already = dora1["already"]
            if False in already:
                return render_template("dora1.html", mode="still")
            else:
                with open("app/tmp/tmp.json", "r") as f:
                    d = json.load(f)
                teams = d["teams"]
                dora1_dict = {}
                for i in range(len(teams)):
                    dteam = teams[i]
                    name = dora1list[i]
                    if name not in dora1_dict:
                        dora1_dict[name] = [dteam]
                    else:
                        dora1_dict[name].append(dteam)
                
                return render_template("dora1.html", mode="kuji", dora1dict=dora1_dict)
        else:
            return redirect(url_for("top", status="logout"))
    else:
        return redirect(url_for("top", status="logout"))


@app.route("/dora1", methods=["post"])
def dora1_post():
    mode = "decision"
    with open("app/tmp/tmp.json", "r") as f:
        d = json.load(f)
    teams = d["teams"]
    with open("app/tmp/dora1.json", "r") as f:
        dora1 = json.load(f)
    dora1list = dora1["dora1list"]
    result = request.form
    for name, team in result.items():
        for i in range(len(dora1list)):
            if name == dora1list[i]:
                if teams[i] != team:
                    dora1["dora1list"][i] = ""
                    dora1["positions"][i] = ""
                    dora1["already"][i] = False
                else:
                    print("{}は{}が抽選権を獲得しました。".format(name, team))
    with open("app/tmp/dora1.json", "w") as f:
        json.dump(dora1, f)
    for i in range(len(dora1["already"])):
        if dora1["already"][i] == True:
            p = db_session.query(Player).filter(Player.name==dora1["dora1list"][i]).first()
            p.dteam = teams[i]
            p.rank = 1
            p.position = dora1["positions"][i]
            db_session.add(p)
            db_session.commit()
    if False not in dora1["already"]:
        if d["now_rank"] == 1:
            d["now_rank"] = 2
            with open("app/tmp/tmp.json", "w") as f:
                json.dump(d, f)
        print("すべての球団の1位指名が終わりました。")
        print("引き続き、2巡目の指名を始めてください。")
        mode = "finish"
    return render_template("dora1.html", mode=mode)


@app.route("/show")
def show():
    with open("app/tmp/recently.json", "r") as f:
        all_nominated = json.load(f)
    with open("app/tmp/tmp.json", "r") as f:
        d = json.load(f)
    teams = d["teams"]
    return render_template("show.html", all_nominated=all_nominated, teams=teams)
    #return render_template("show.html")


if __name__ == "__main__":
    app.run()