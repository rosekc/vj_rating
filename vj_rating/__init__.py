import os

import click
import pytz
from flask import Flask
from flask_frozen import Freezer
from flask_sqlalchemy import SQLAlchemy

#from flask_moment import Moment
from .utils.moment import Moment

db = SQLAlchemy()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' +
        os.path.join(app.instance_path, 'dev.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        FREEZER_DESTINATION=os.path.join(app.instance_path, 'bulid'),
        EXPLAIN_TEMPLATE_LOADING=True,
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    moment = Moment(app)
    db.init_app(app)
    freezer = Freezer(app)

    from .main import bp as main_blueprint
    app.register_blueprint(main_blueprint)

    from .main.models import User, Contest, Contestant
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Contest=Contest, Contestant=Contestant)

    @app.cli.command()
    def init():
        rank_path = os.path.join(app.instance_path, 'rank')
        if not os.path.exists(rank_path):
            os.mkdir(os.path.join(app.instance_path, 'rank'))

    @app.cli.command()
    def test():
        """Run the unit tests."""
        import unittest
        tests = unittest.TestLoader().discover('tests')
        unittest.TextTestRunner(verbosity=2).run(tests)

    from .utils.html_parser import VjudgeParser
    from .utils.rating_calculator import CodeforcesCalculator

    def load_rank(path):
        with open(path, encoding='utf-8') as f:
            contest = VjudgeParser.parse(f.read())
            contest.calculate_rating()

    @app.cli.command()
    def cal():
        db.drop_all()
        db.create_all()

        base_dir = os.path.join(app.instance_path, 'rank')
        li = os.listdir(base_dir)

        li = [i for i in li if i.endswith('.html')]

        for i in li:
            print('processing {}'.format(i))
            load_rank(os.path.join(base_dir, i))

        # reassign rank
        from sqlalchemy import desc
        
        contests = Contest.query.order_by(desc(Contest.start_time)).all()

        (c.calculate_rating() for c in contests)
        db.session.add_all(contests)

        users = User.query.order_by(desc(User.rating)).all()
        cur_rank = 1
        cnt = 1
        last_rating = users[0].rating
        for u in users:
            if last_rating == u.rating:
                u.rank = cur_rank
            else:
                u.rank = cnt
                cur_rank = cnt
            last_rating = u.rating
            cnt += 1
        db.session.add_all(users)
        db.session.commit()

    @app.cli.command()
    def freeze():
        freezer.freeze()

    from .blog import Blog
    blog = Blog(app)

    return app
