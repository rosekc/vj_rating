from flask import render_template
from sqlalchemy import desc

from . import bp
from .models import Contest, User

@bp.route('/')
def index():
    return render_template('main/index.html')

@bp.route('/rank_list/')
def rank_list():
    users = User.query.order_by(desc(User.rating)).all()
    return render_template('main/rank_list.html', users=users)

@bp.route('/contest_list/')
def contest_list():
    contests = Contest.query.order_by(Contest.start_time).all()
    return render_template('main/contest_list.html', contests=reversed(contests))

@bp.route('/user/<int:user_id>/')
def user_details(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    contest_list_json = user.gen_contest_list()
    return render_template('main/user.html', user=user, contest_list_json=contest_list_json, reversed=reversed)

@bp.route('/contest/<int:contest_id>/')
def contest_details(contest_id):
    contest = Contest.query.filter_by(id=contest_id).first_or_404()
    return render_template('main/contest.html', contest=contest, contestants=contest.contestants)
