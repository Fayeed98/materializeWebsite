import tornado.ioloop
import tornado.web
import os.path 

# Request handling
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class DetailedPostHandler(tornado.web.RequestHandler):
	def get(self,car):
		# File handling code
		print(car)
		if car == "pagani":
			lines = "".join([ line.rstrip("\n") for line in open('static/pagani.txt')])
			self.render("detailedPost.html",lines=lines)
		elif car == "bugatti":
			lines = "".join([ line.rstrip("\n") for line in open('static/bugatti.txt')])
			self.render("detailedPost.html",lines=lines)










#Assigning URLs
def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/detailedpost/([A-Za-z0-9]+)", DetailedPostHandler),
    ],template_path=os.path.join(os.path.dirname(__file__), "templates"),static_path=os.path.join(os.path.dirname(__file__), "static"),debug=True)






if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("live")
    tornado.ioloop.IOLoop.current().start()
