from flask import Blueprint, render_template
from sqlalchemy import desc

from .models import Post

bp = Blueprint('blog', __name__, url_prefix='/blog',
               template_folder='templates')

@bp.route('/')
def index():
    posts = Post.query.order_by(desc(Post.create_time)).all()
    return render_template('blog/index.html', posts=posts)

@bp.route('/<int:post_id>/')
def get_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    return render_template('blog/post.html', post=post)
