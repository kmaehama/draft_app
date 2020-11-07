from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from models.database import Base


class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    name = Column(String(16))
    team = Column(String(16))
    dteam = Column(String(16), default="")
    rank = Column(Integer, default=0)

    def __init__(self, name=None, team=None, already=None, rank=None):
        self.name = name
        self.team = team
        self.already = already
        self.rank = rank

    def __repr__(self):
        return '<Name %r>' % (self.name)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_name = Column(String(128), unique=True)
    hashed_password = Column(String(128))

    def __init__(self, user_name=None, hashed_password=None):
        self.user_name = user_name
        self.hashed_password = hashed_password

    def __repr__(self):
        return '<Name %r>' % (self.user_name)