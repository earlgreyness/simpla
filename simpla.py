import logging

from sqlalchemy import (
    Column, Integer, Unicode, DateTime, String, Table,
    ForeignKey, Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ArrowType
from flask import (
    Flask, render_template, session, redirect, url_for, request,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, UserMixin,
    logout_user, current_user, login_required,
)


app = Flask(__name__, static_folder='static')
app.config.from_object('config')

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'


@login_manager.user_loader
def load_user(login):
    if login == 'admin':
        user = UserMixin()
        user.id = login
        return user
    return None


association_table = Table('s_products_categories', db.metadata,
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
    parent_id = Column(Integer, ForeignKey('s_products.id'))

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

    @staticmethod
    def get_all_categories():
        return Category.get_all()

    def __repr__(self):
        return "<Product {id}: {name}>".format(id=self.id, name=self.name)


class Category(db.Model):
    __bind_key__ = 'simpla'
    __tablename__ = 's_categories'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    visible = Column(Boolean)

    products = relationship('Product',
                            secondary=association_table,
                            back_populates='categories',
                            order_by='Product.id')

    @classmethod
    def get_all(cls):
        return cls.query.order_by(cls.id).all()

    def __repr__(self):
        return '<Category {id}: {name}>'.format(id=self.id, name=self.name)


@app.route('/products')
@login_required
def show_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('products.html', products=products)


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
