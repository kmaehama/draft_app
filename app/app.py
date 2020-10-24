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
        f = open("app/tmp/tmp.json", "r")
        d = json.load(f)
        teams = d["teams"]
        rank = d["now_rank"]
        now_team = d["now_team"]
        if session["user_name"] == teams[now_team]:
            return render_template("nominate.html", rank=rank, your_turn=True)
        else:
            return render_template("nominate.html", rank=rank, your_turn=False)
    else:
        return redirect(url_for("top", status="logout"))


@app.route("/nominate",methods=["post"])
def nominate_post():
    dteam = session["user_name"]
    name = request.form["name"]
    team = request.form["team"]
    can_nominate = False
    try:
        p = db_session.query(Player).filter(Player.name==name).first()
        if p.rank == 0:
            with open("app/tmp/tmp.json", "r") as f:
                d = json.load(f)
            rank = d["now_rank"]

            can_nominate = True
            p.dteam = dteam
            p.rank = rank
            db_session.add(p)
            db_session.commit()

            teams = d["teams"]
            now_team = d["now_team"]
            if rank % 2 == 0:
                if now_team == len(teams) - 1:
                    d["now_rank"] += 1
                else:
                    d["now_team"] += 1
            else:
                if now_team == 0:
                    d["now_rank"] += 1
                else:
                    d["now_team"] -= 1
            with open("app/tmp/tmp.json", "w") as f:
                json.dump(d, f)
    except:
        print("maybe kamogawa")
    return render_template("nominate.html", name=name, team=team, rank=rank, status=can_nominate, your_turn=~can_nominate)


@app.route("/member")
def member():
    if "user_name" in session:
        dteam = session["user_name"]
        players = db_session.query(Player).filter(Player.dteam==dteam).order_by(Player.rank).all()
        return render_template("member.html", name=dteam, players=players)
    else:
        return redirect(url_for("top", status="logout"))


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
    return render_template("setting.html")


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

    return render_template("top.html",status="logout")

if __name__ == "__main__":
    app.run(debug=True)