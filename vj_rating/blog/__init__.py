import os

import pytz
from dateutil import parser
from datetime import datetime

from .. import db
from ..utils.moment import CHINA_STANDART_TIME_ZONE
from . import views
from .models import Post
from .views import bp


def default_front_matter():
    return


class Markdown:
    def __init__(self, front_matter=None, content=''):
        self.front_matter = {
            'title': 'New Blog',
            'create_time': datetime.utcnow(),
            'author': 'Noname',
        }
        if isinstance(front_matter, dict):
            self.front_matter.update(front_matter)
        self.content = content

    @classmethod
    def from_file_text(cls, markdown_text):
        splited_list = markdown_text.split('---\n', 2)
        front_matter_text = splited_list[1]
        content = splited_list[2]
        front_matter = {}

        for line in front_matter_text.splitlines():
            k, w = [i.strip() for i in line.split(':', 1)]
            front_matter[k] = w

        front_matter['create_time'] = parser.parse(front_matter['create_time'], ignoretz=True).astimezone(
            CHINA_STANDART_TIME_ZONE).astimezone(pytz.utc)
        prepared_markdown = cls(front_matter, content)
        return prepared_markdown

    def to_file_text(self):
        prepared_str = '---\n'
        for k, v in self.front_matter.items():
            if isinstance(v, datetime):
                v = '{:%Y-%m-%d %H:%M}'.format(v.astimezone(
                    CHINA_STANDART_TIME_ZONE))
            prepared_str += '{}: {}\n'.format(k, v)
        prepared_str += '---\n'
        prepared_str += self.content
        return prepared_str

    def to_post(self):
        post = Post(markdown_content=self.content, **self.front_matter)
        return post
    
    def update_post(self, post):
        post.__dict__.update(self.front_matter)
        post.markdown_content = self.content


class Blog:
    def __init__(self, app):
        self.base_dir = os.path.join(app.instance_path, 'blog')
        self.init_app(app)

    def init_app(self, app):
        app.register_blueprint(bp)

        @app.cli.command()
        def update_post():
            blog_list = [i for i in os.listdir(self.base_dir) if i.endswith('.md')]

            for i in blog_list:
                app.logger.info('processing {}'.format(i))
                with open(os.path.join(self.base_dir, i), 'r', encoding='utf-8') as fp:
                    markdown = Markdown.from_file_text(fp.read())
                    post_id = int(i[:-3]) # remove .md
                    post = Post.query.filter_by(id=post_id).first()
                    markdown.update_post(post)

            db.session.commit()

        @app.cli.command()
        def create_post():
            if not os.path.exists(self.base_dir):
                os.makedirs(self.base_dir)

            markdown = Markdown()
            post = markdown.to_post()
            db.session.add(post)
            db.session.commit()

            file_path = os.path.join(self.base_dir, '{}.md'.format(post.id))


            with open(file_path, 'w', encoding='utf-8') as fp:
                fp.write(markdown.to_file_text())
            
            app.logger.info('new post create at {}'.format(file_path))

            
