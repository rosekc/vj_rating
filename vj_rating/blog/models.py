from datetime import datetime

import markdown

from .. import db


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    create_time = db.Column(db.DateTime(), default=datetime.utcnow())
    author = db.Column(db.String())
    markdown_content = db.Column(db.Text)

    len_limit = 200
    markdown_extensions = ['markdown.extensions.extra', 'markdown.extensions.codehilite',
                           'markdown.extensions.tables', 'markdown.extensions.toc', 'markdown.extensions.codehilite']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._need_truncate = None
        self._truncated_html_content = None
    
    @property
    def html_content(self):
        return markdown.markdown(self.markdown_content, extensions=self.markdown_extensions)

    @property
    def need_truncate(self):
        if self._need_truncate is None:
            raise AttributeError('use truncated_html_content before using this attribute')
        return self._need_truncate

    @property
    def truncated_html_content(self):
        len_counter = 0
        truncated = []
        self._need_truncate = False

        for s in self.markdown_content.splitlines():
            if len_counter > self.len_limit:
                self._need_truncate = True
                break
            cur_len = len(s)
            len_counter += cur_len
            truncated.append(s)

        if self._need_truncate:
            truncated.append('\n...\n')

        truncated = '\n'.join(truncated)
        self._truncated_html_content = markdown.markdown(truncated, extensions=self.markdown_extensions)
        return self._truncated_html_content
