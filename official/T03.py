import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        items = ["Item 1", "Item 2", "Item 3"]
        self.render('./templates/t03.html', title='My Title', items=items)



def make_app():
    return tornado.web.Application([
        (r"/", MainHandler)
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(5005)
    tornado.ioloop.IOLoop.current().start()