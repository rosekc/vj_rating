from flask import render_template
from sqlalchemy import desc

from . import main
from ..models import Contest, User

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/rank_list/')
def rank_list():
    users = User.query.order_by(desc(User.rating)).all()
    return render_template('rank_list.html', users=users)

@main.route('/contest_list/')
def contest_list():
    contests = Contest.query.all()
    return render_template('contest_list.html', contests=reversed(contests))

@main.route('/user/<int:user_id>/')
def user_details(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    contest_list_json = user.gen_contest_list()
    return render_template('user.html', user=user, contest_list_json=contest_list_json, reversed=reversed)

@main.route('/contest/<int:contest_id>/')
def contest_details(contest_id):
    contest = Contest.query.filter_by(id=contest_id).first_or_404()
    return render_template('contest.html', contest=contest, contestants=contest.contestants)
