import json
from datetime import datetime

from sqlalchemy.ext.associationproxy import association_proxy

from . import db
from .utils.rating_calculator import CodeforcesCalculator


class Contestant(db.Model):
    __tablename__ = 'contestants'
    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'), primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey(
        'contests.id'), primary_key=True)
    before_rating = db.Column(db.Integer, default=None)
    after_rating = db.Column(db.Integer, default=1500)
    rank = db.Column(db.Integer)
    solved = db.Column(db.Integer)
    penalty = db.Column(db.Integer)
    user = db.relationship('User', back_populates='as_contestants')
    contest = db.relationship('Contest', back_populates='contestants')

    def as_dict(self):
        return {
            'name': self.contest.name,
            'time': self.contest.start_time.strftime('%Y-%m-%dT%H:%M:%S')  + 'Z',
            'rating': self.after_rating
        }

    def __repr__(self):
        return '<Contestant %d %d>' % (self.user_id, self.after_rating)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True, nullable=False)
    nickname = db.Column(db.String(64), unique=True)
    rank = db.Column(db.Integer, default=None)
    rating = db.Column(db.Integer, default=None)
    as_contestants = db.relationship(
        'Contestant', back_populates='user', order_by=Contestant.contest_id)
    contests = association_proxy('as_contestants', 'contest')

    def gen_contest_list(self):
        return json.dumps(list(map(lambda x: x.as_dict(), self.as_contestants)))


class Contest(db.Model):
    __tablename__ = 'contests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    start_time = db.Column(db.DateTime(), default=datetime.utcnow())
    end_time = db.Column(db.DateTime(), default=datetime.utcnow())
    participant_count = db.Column(db.Integer)
    last_calculate_rating_time = db.Column(db.DateTime, default=None)
    html = db.Column(db.Text)
    users = association_proxy('contestants', 'user')
    contestants = db.relationship(
        'Contestant', back_populates='contest', order_by=Contestant.rank)

    def calculate_rating(self):
        CodeforcesCalculator.calculate_rating(self.contestants)
        db.session.add_all(self.contestants)
        db.session.add_all(self.users)
        self.last_calculate_rating_time = datetime.utcnow()
        self.participant_count = len(self.contestants)
        db.session.add(self)
        db.session.commit()
