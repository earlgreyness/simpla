simpla_data = dict(
    host='',
    user='',
    database='',
    password='',
    charset='utf8',  # utf8mb4
)

uri = 'mysql+pymysql://{user}:{password}@{host}/{database}?charset={charset}'


SQLALCHEMY_DATABASE_URI = 'sqlite:///database.sqlite'
SQLALCHEMY_BINDS = {
    'simpla': uri.format(**simpla_data),
}
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = ''

ONLINE_STORE_DOMAIN = ''
ADMIN_PASSWORD = ''
