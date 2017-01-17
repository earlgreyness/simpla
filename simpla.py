import logging
import itertools
from collections import namedtuple

from sqlalchemy import (
    Column, Integer, Unicode, DateTime, String, Table,
    ForeignKey, Boolean, UnicodeText, func,
)
from sqlalchemy.orm import relationship, aliased
from sqlalchemy_utils import ArrowType
from flask import (
    Flask, render_template, session, redirect, url_for, request, abort,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, UserMixin,
    logout_user, current_user, login_required,
)
from flask_restful import Api, Resource


app = Flask(__name__, static_folder='static')
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

api = Api(app)


@login_manager.user_loader
def load_user(login):
    if login == 'admin':
        user = UserMixin()
        user.id = login
        return user
    return None


Group = namedtuple('Group', 'parent, children')


association_table = Table(
    's_products_categories', db.metadata,
    Column('product_id', Integer, ForeignKey('s_products.id')),
    Column('category_id', Integer, ForeignKey('s_categories.id')),
    info=dict(bind_key='simpla'),
)


class Product(db.Model):
    __bind_key__ = 'simpla'
    __tablename__ = 's_products'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    created = Column(ArrowType)
    url = Column(Unicode)

    categories = relationship('Category',
                              secondary=association_table,
                              back_populates='products',
                              order_by='Category.id',
                              lazy='joined')

    def get_url(self):
        return 'http://{domain}/products/{label}'.format(
            label=self.url,
            domain=app.config['ONLINE_STORE_DOMAIN'],
        )

    def _get_groups_as_json(self):
        ids = [c.id for c in self.categories]
        try:
            main_id = self.main_category.id
        except AttributeError:
            main_id = None

        def _to_json(c):
            j = (Category.get_mock_root() if c is None else c).json()
            j['present'] = j['id'] in ids
            j['main'] = j['id'] == main_id
            return j

        def _group_to_json(g):
            return {
                'parent': _to_json(g.parent),
                'children': [_to_json(ch) for ch in g.children],
            }

        return [_group_to_json(g) for g in Category.get_by_groups()]

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.get_url(),
            'groups': self._get_groups_as_json(),
        }

    @property
    def main_category(self):
        if not self.categories:
            return None
        return self.categories[0]

    def __repr__(self):
        return "<Product {id}: {name}>".format(id=self.id, name=self.name)


class Category(db.Model):
    __bind_key__ = 'simpla'
    __tablename__ = 's_categories'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    meta_title = Column(Unicode, default='')
    meta_keywords = Column(Unicode, default='')
    meta_description = Column(Unicode, default='')
    url = Column(Unicode)
    visible = Column(Integer)
    parent_id = Column(Integer, ForeignKey('s_categories.id'))
    external_id = Column(Unicode, default='')
    description = Column(UnicodeText, default='')
    position = Column(Integer, default=0)

    parent = relationship('Category',
                          foreign_keys='[Category.parent_id]',
                          remote_side='[Category.id]',
                          lazy='joined')
    products = relationship('Product',
                            secondary=association_table,
                            back_populates='categories',
                            order_by='Product.id')

    def __repr__(self):
        return '<Category {id}: {name}>'.format(id=self.id, name=self.name)

    @classmethod
    def get_mock_root(cls):
        return cls(
            id=0,
            name='Root',
            parent_id=0,
        )

    def is_root(self):
        return self.parent_id == 0

    def json(self):
        return {
            'id': self.id,
            'parent_id': self.parent_id,
            'is_root': self.is_root(),
            'name': self.name,
        }

    @staticmethod
    def get_by_groups():
        Child = aliased(Category, name='child')

        childfree = (
            db.session.query(Category)
                      .outerjoin(Child, Child.parent_id == Category.id)
                      .filter(Category.parent_id == 0)
                      .filter(Child.id.is_(None))
                      .order_by(Category.id)
                      .all()
        )

        children = (
            db.session.query(Category)
                      .filter(Category.parent_id != 0)
                      .order_by(Category.parent_id, Category.id)
                      .all()
        )

        parts = (list(g) for k, g in itertools.groupby(children, key=lambda c: c.parent_id))
        return [Group(None, childfree)] + [Group(g[0].parent, g) for g in parts]


class ProductResource(Resource):
    @login_required
    def get(self):
        id_ = int(request.args['id'])
        return {'product': Product.query.get(id_).json()}


api.add_resource(ProductResource, '/api/product')


@app.route('/')
def show_index():
    return redirect(url_for('show_products'))


@app.route('/products')
@login_required
def show_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('products.html', products=products)


@app.route('/products/<int:id>', methods=['GET', 'POST'])
@login_required
def show_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        raise NotImplementedError
    return render_template('product.html', product=product)


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.permanent = False
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (username, password) == ('admin', app.config['ADMIN_PASSWORD']):
            login_user(load_user('admin'), remember=False)

    next_location = request.args.get('next')
    if current_user.is_authenticated:
        return redirect(next_location or url_for('show_products'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    app.run('localhost', port=5000, debug=True)
