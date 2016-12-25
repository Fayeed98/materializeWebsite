import tornado.ioloop # its an import statement,ioloop handles the request response cycle
import tornado.web #it imoprts the web functionality of tornado
import os.path  #used to get the path of any folder or file

# Request handling
class MainHandler(tornado.web.RequestHandler): #this class inherits from tornado.web
    def get(self): #it is used to handle get requests
        self.render("index.html") #renders a html page

class DetailedPostHandler(tornado.web.RequestHandler):
	def get(self,car): #car is parameter which is accepted from the URL
		# File handling code
		if car == "pagani":  #checking if variable car has the string pagani
			lines = "".join([ line.rstrip("\n") for line in open('static/pagani.txt')])
			self.render("detailedPost.html",lines=lines,carname=car.upper(),carimage=1) #lines is a template varibale which will be pased to html page
		elif car == "bugatti":
			lines = "".join([ line.rstrip("\n") for line in open('static/bugatti.txt')])
			self.render("detailedPost.html",lines=lines,carname=car.upper(),carimage=2)

#Assigning URLs
def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/detailedpost/([A-Za-z0-9]+)", DetailedPostHandler),  #we are specifying a regex
    ],template_path=os.path.join(os.path.dirname(__file__), "templates"),static_path=os.path.join(os.path.dirname(__file__), "static"),debug=True)


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("live")
    tornado.ioloop.IOLoop.current().start()
