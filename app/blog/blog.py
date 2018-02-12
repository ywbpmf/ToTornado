import bcrypt
import concurrent.futures
import os
import re
import subprocess
import pymysql
import tornado.escape
from tornado import gen
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options


define("port", default=5010, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1", help="blog database host")
define("mysql_port", default=3306, help="blog host port", type=int)
define("mysql_db", default="blog", help="blog database name")
define("mysql_user", default="root", help="blog database user")
define("mysql_password", default="root", help="blog database password")

executor = concurrent.futures.ThreadPoolExecutor(2)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', HomeHandler),
            (r'/archive', ArchiveHandler),
            (r'/auth/login', AuthLoginHandler),
            (r'/auth/create', AuthCreateHandler),
        ]
        settings = dict(
            blog_title=u'Tornado Blog',
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={"Entry": EntryModule},
            xsrf_cookie=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="auth/login",
            debug=True
        )

        super(Application, self).__init__(handlers, **settings)

        #
        self.db = pymysql.connect(host=options.mysql_host,
            port=options.mysql_port, db=options.mysql_db,
            user=options.mysql_user, password=options.mysql_password)

        self.maybe_create_tables()

    def maybe_create_tables(self):
        cur = self.db.cursor()
        pass

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        self.clear_cookie('blog_user')
        user_id = self.get_secure_cookie('blog_user')
        if not user_id:
            return None
        with self.db.cursor() as cursor:
             cursor.execute("SELECT * FROM authors WHERE id = %s", (int(user_id)))
             return cursor.fetchone()
        return None

    def any_author_exists(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM authors LIMIT  1")
            authors = cursor.fetchone()
        return bool(authors)


class HomeHandler(BaseHandler):

    def get(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM entries ORDER BY published DESC LIMIT 5")
            entries = cursor.fetchall()
        self.render('home.html', entries=entries)


class ArchiveHandler(BaseHandler):
    def get(self):
        entries = None
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM entries ORDER BY published DESC")
            entries =cursor.fetchall()
        self.render('archive.html', entries=entries)


class AuthLoginHandler(BaseHandler):
    def get(self):
        if not self.any_author_exists():
            self.redirect('/auth/create')
        else:
            self.render('login.html', error=None)

class AuthCreateHandler(BaseHandler):
    def get(self):
        self.render('create_author.html')

    @gen.coroutine
    def post(self):
        if self.any_author_exists():
            raise tornado.web.HTTPError(400, 'author already created')
        hashed_password = yield executor.submit(bcrypt.hashpw,
            tornado.escape.utf8(self.get_argument('password')), bcrypt.gensalt())
        with self.db.cursor() as cursor:
            cursor.execute("INSERT INTO authors (email, name, hashed_password) VALUES (%s, %s, %s)",
                           (self.get_argument('email'), self.get_argument('name'), hashed_password))
            self.db.commit()

            cursor.execute('SELECT id FROM authors WHERE name = %s', (self.get_argument('name')))
            author_id = cursor.fetchone()[0]

            self.set_secure_cookie('blog_user', str(author_id))
            self.redirect(self.get_argument('next', '/'))



class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()