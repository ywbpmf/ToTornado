import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('<html><body><form action="/" method="post">'
                   '<input type="text" name="message">'
                   '<input type="submit" value="Submit">'
                   '</form></body></html>')

    def post(self, *args, **kwargs):
        self.set_header('Content-Type', 'text/plain')
        self.write('You wrote ' + self.get_argument('message'))


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler)
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(5005)
    tornado.ioloop.IOLoop.current().start()