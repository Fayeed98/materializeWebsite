import tornado.ioloop
import tornado.web
import os.path 

# Request handling
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class DetailedPostHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("detailedPost.html")









#Assigning URLs
def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/detailedpost", DetailedPostHandler),
    ],template_path=os.path.join(os.path.dirname(__file__), "templates"),static_path=os.path.join(os.path.dirname(__file__), "static"),debug=True)






if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("live")
    tornado.ioloop.IOLoop.current().start()
