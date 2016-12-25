import tornado.web
import tornado.httpserver
import tornado.options
import tornado.ioloop
import tornado.websocket
import tornado.httpclient
from tornado import gen
import os.path
import os
import json
import requests
import time
import datetime
import psycopg2
import uuid
import smtplib
import hashlib
import base64
import random
import string

postgres = psycopg2.connect(dbname="ramdb", host="localhost", user="postgres", password="")
cursor = postgres.cursor()

from tornado.options import define, options, parse_command_line
define('port',default=8000,type=int)

class IndexHandler(tornado.web.RequestHandler):
	def get(self):
		self.write("Working!")



class CreateTemplateHandler(tornado.web.RequestHandler):
	def get(self):
		self.render('index.html')


class WSHandler(tornado.websocket.WebSocketHandler):
	def check_origin(self, origin):
		return True

	def open(self):
		# load all the html and js here.
		print("Connection Opened")

	def on_message(self, message):
		messageReceived = json.loads(message)
		messageLabel = messageReceived['messageLabel']

		if messageLabel == "login":
			email = messageReceived['email']
			password = messageReceived['password']
			password = password.encode('UTF-8')
			role = messageReceived['role']
			hashedPass = hashlib.md5(password).hexdigest()

			if role == "caregiver":
				try:
					cursor.execute("""
						SELECT caregiver_id,first_name FROM ram_caregivers WHERE email=%s AND password=%s
						""",(email,hashedPass))
					caregiver_details = cursor.fetchone()
					print(caregiver_details)
					caregiver_id = caregiver_details[0]
					caregiver_name = caregiver_details[1]

					try:
						cursor.execute("""
							SELECT patient_id,first_name,last_name,profile_pic FROM ram_patients WHERE caregiver_id=%s
							""",(caregiver_id,))
						patientDetails = cursor.fetchall()
					except Exception as e:
						print("In except of Login SELECT",e)
					messageToSendToClient = {"messageLabel":"login","creator_id":caregiver_id,"creator_name":caregiver_name,"status":"success","patients":patientDetails}
					self.write_message(json.dumps(messageToSendToClient))

				except Exception as e:
					print("In except of Login",e)








		elif messageLabel == "signup":
			name = messageReceived['name']
			email = messageReceived['email']
			password = messageReceived['password']
			password = password.encode('UTF-8')
			hashedPass = hashlib.md5(password).hexdigest()
			role = messageReceived['role']

			if role == 'caregiver':
				categories = ['default_personal_memory','default_math','default_verbal','default_daily_routine','default_food','default_clothes','default_default']

				try:
					cursor.execute("""
						INSERT INTO ram_caregivers(doctor_id,first_name,email,password,role) VALUES(%s,%s,%s,%s,%s) RETURNING caregiver_id

						""",('1',name,email,hashedPass,role))
					postgres.commit();
					caregiver_id = cursor.fetchone()[0]

					for catName in categories:
						try:
							cursor.execute("""
								INSERT INTO ram_categories(creator_id,creator_role,category_name) VALUES(%s,%s,%s)
								""",(caregiver_id,'caregiver',catName))
							postgres.commit()

						except Exception as e:
							print("In except of Inserting Categories",e)


					messageToSendToClient = {"messageLabel":"signup","creator_id":caregiver_id,"creator_name":name}
					self.write_message(json.dumps(messageToSendToClient))

				except Exception as e:
					postgres.rollback()
					print("In except of signup",e)








		elif messageLabel == "patientProfileOne":
			print("In patientProfileOne")
			caregiver_name = messageReceived['caregiver_name']
			caregiver_phone = messageReceived['caregiver_phone']
			primary_caregiver = messageReceived['primary_caregiver']

			creator_id = messageReceived['creator_id']

			patient_name = messageReceived['patient_name']
			patient_name = patient_name.split(' ')
			first_name,last_name = patient_name
			patientProfileImage = messageReceived['patientProfileImage']

			questions = [{"question":"What is your name?","answer":patient_name,"type":"text"}] # Insert Questions Individually - Loop through the list and insert.

			# use creator_id and nameOfTemplate to insert the questions into it.

			try:
				cursor.execute("""
					INSERT INTO ram_patients(doctor_id,caregiver_id,first_name,last_name,profile_pic) VALUES(%s,%s,%s,%s,%s) RETURNING patient_id
					""",("1",creator_id,first_name,last_name,patientProfileImage))
				patient_id = cursor.fetchone()[0]

				try:
					cursor.execute("""
						SELECT category_id FROM ram_categories WHERE creator_id=%s AND category_name=%s
						""",(creator_id,'default_personal_memory'))
					category_id = cursor.fetchone()[0]

					try:
						cursor.execute("""
							INSERT INTO ram_templates(category_id,patient_id,creator_id,creator_role,template_name) VALUES(%s,%s,%s,%s,%s) RETURNING template_id
							""",(category_id,patient_id,creator_id,'caregiver','Patient Info'))
						postgres.commit()
						template_id = cursor.fetchone()[0]

						for i in questions:

							try:
								cursor.execute("""
									INSERT INTO ram_questions(template_id,questions,creator_id,patient_id,section) VALUES(%s,%s,%s,%s,%s)
									""",(template_id,json.dumps(i),creator_id,patient_id,"personal"))
								postgres.commit()
							except Exception as e:
								postgres.rollback()
								print("In except of patientProfileOne INNER MOST INSERT ",e)

						self.write_message(json.dumps({"messageLabel":"patient_info","patient_id":patient_id,"template_id":template_id}))
					except Exception as e:
						postgres.rollback()
						print("In except of patientProfileOne INSERT OPERATION",e)


				except Exception as e:
					print("In except of patientProfileOne",e)
			except Exception as e:
				print("In outermost except of patientProfileOne",e)






			# save to DB as template in personal memory

		elif messageLabel == "patientProfileTwo":
			print("In patientProfileTwo")
			patient_birth_place = messageReceived['patient_birth_place']
			patient_phone = messageReceived['patient_phone']
			patient_birth_date = messageReceived['patient_birth_date']
			patient_age = messageReceived['patient_age']
			patient_place = messageReceived['patient_place']
			gender = messageReceived['gender']
			languages =  messageReceived['languages']

			creator_id = messageReceived['creator_id']
			patient_id = messageReceived['patient_id']

			template_id = messageReceived['template_id']

			questions = [{"question":"Where were you born?","answer":patient_birth_place,"type":"text"},{"question":"What is your birthdate?","answer":patient_birth_date,"type":"text"},{"question":"How old are you?","answer":patient_age,"type":"text"},{"question":"Where do you live now?","answer":patient_place,"type":"text"},{"question":"Which languages do you speak?","answer":languages,"type":"multiple"}]

			try:
				cursor.execute("""
					UPDATE ram_patients SET age=%s,phone=%s,dob=%s,gender=%s,role=%s WHERE patient_id=%s

					""",(patient_age,patient_phone,patient_birth_date,gender,'patient',patient_id))



				try:
					cursor.execute("""
						SELECT category_id FROM ram_categories WHERE creator_id=%s AND category_name=%s
						""",(creator_id,'default_personal_memory'))
					category_id = cursor.fetchone()[0]

					for i in questions:
						try:
							cursor.execute("""
								INSERT INTO ram_questions(template_id,questions,creator_id,patient_id,section) VALUES(%s,%s,%s,%s,%s)
								""",(template_id,json.dumps(i),creator_id,patient_id,'personal'))
							postgres.commit()
						except Exception as e:
							postgres.rollback()
							print("In except of patientProfileTwo INNER MOST INSERT ",e)


				except Exception as e:
					print("In except of patientProfileTwo",e)

			except Exception as e:
				print("In UPDATE except of patientProfileTwo",e)









			# save to DB as template in personal memory

		elif messageLabel == "patientProfileThree":
			print("In patientProfileThree")
			patient_qualification =  messageReceived['patient_qualification']
			patient_city_of_work = messageReceived['patient_city_of_work']
			patient_company_name = messageReceived['patient_company_name']
			patient_designation = messageReceived['patient_designation']
			schools = messageReceived['schools']
			creator_id = messageReceived['creator_id']
			patient_id = messageReceived['patient_id']

			questions = [{"question":"What is your latest degree?","answer":patient_qualification,"type":"text"},{"question":"Where do you work/used to work ?","answer":patient_city_of_work,"type":"text"},{"question":"Name the company you work/used to work in ______","answer":patient_company_name,"type":"text"},{"question":"What is/(was) your latest designation?","answer":patient_designation,"type":"text"},{"question":"Which schools have you attended?","answer":schools,"type":"multiple"}]



			try:
				cursor.execute("""
					SELECT category_id FROM ram_categories WHERE creator_id=%s AND category_name=%s
					""",(creator_id,'default_personal_memory'))
				category_id = cursor.fetchone()[0]

				try:
					cursor.execute("""
						INSERT INTO ram_templates(category_id,patient_id,creator_id,creator_role,template_name) VALUES(%s,%s,%s,%s,%s) RETURNING template_id
						""",(category_id,patient_id,creator_id,'caregiver','Work Info'))
					postgres.commit()
					template_id = cursor.fetchone()[0]

					for i in questions:
						try:
							cursor.execute("""
									INSERT INTO ram_questions(template_id,questions,creator_id,patient_id,section) VALUES(%s,%s,%s,%s,%s)
									""",(template_id,json.dumps(i),creator_id,patient_id,'personal'))
							postgres.commit()
						except Exception as e:
							postgres.rollback()
							print("In except of patientProfileThree INNER MOST INSERT ",e)
				except Exception as e:
					postgres.rollback()
					print("In except of patientProfileThree INSERT OPERATION",e)


			except Exception as e:
				print("In except of patientProfileThree",e)











			# save to DB as template in personal memory

		elif messageLabel == "patientProfileFour":
			print("In patientProfileFour")
			patient_children = messageReceived['patient_children']
			patient_spouse_name = messageReceived['patient_spouse_name']
			children = messageReceived['children']
			creator_id = messageReceived['creator_id']
			patient_id = messageReceived['patient_id']

			questions = [{"question":"How many children do you have?","answer":patient_children,"type":"text"},{"question":"What is your spouse's name?","answer":patient_spouse_name,"type":"text"}]

			for i in children:
				i = json.loads(i)
				patient_child_name = i['patient_child_name']
				patient_child_relation = i['patient_child_relation']
				patient_child_city = i['patient_child_city']
				patient_child_image = i['patient_child_image']

				question = {"question":"is my ______?","answer":patient_child_relation,"type":"text","image":patient_child_image}
				questions.append(question)
				question2 = {"question":"Where does %s live?"%patient_child_name,"answer":patient_child_city,"type":"text"}
				questions.append(question2)
				question3 = {"question":"Who is this?","answer":patient_child_name,"type":"text","image":patient_child_image}
				questions.append(question3)




			try:
				cursor.execute("""
					SELECT category_id FROM ram_categories WHERE creator_id=%s AND category_name=%s
					""",(creator_id,'default_personal_memory'))
				category_id = cursor.fetchone()[0]

				try:
					cursor.execute("""
						INSERT INTO ram_templates(category_id,patient_id,creator_id,creator_role,template_name) VALUES(%s,%s,%s,%s,%s) RETURNING template_id
						""",(category_id,patient_id,creator_id,'caregiver','Children & Spouse'))
					postgres.commit()
					template_id = cursor.fetchone()[0]

					for i in questions:


						try:
							cursor.execute("""
									INSERT INTO ram_questions(template_id,questions,creator_id,patient_id,section) VALUES(%s,%s,%s,%s,%s)
									""",(template_id,json.dumps(i),creator_id,patient_id,'family'))
							postgres.commit()
						except Exception as e:
							postgres.rollback()
							print("In except of patientProfileFour INNER MOST INSERT ",e)
				except Exception as e:
					postgres.rollback()
					print("In except of patientProfileFour INSERT OPERATION",e)


			except Exception as e:
				print("In except of patientProfileFour",e)











			# save to DB as template in personal memory
		elif messageLabel == "patientProfileFive":
			print("In patientProfileFive")
			patient_father = messageReceived['patient_father']
			patient_mother = messageReceived['patient_mother']
			siblings = messageReceived['siblings']
			creator_id = messageReceived['creator_id']
			patient_id = messageReceived['patient_id']

			questions = [{"question":"What is your Father's name?","answer":patient_father,"type":"text"},{"question":"What is your Mother's name?","answer":patient_mother,"type":"text"}]





			for i in siblings:
				i = json.loads(i)
				patient_sibling_name = i['patient_sibling_name']
				patient_sibling_relation = i['patient_sibling_relation']
				patient_sibling_city = i['patient_sibling_city']
				patient_sibling_image = i['patient_sibling_image']

				question = {"question":"%s is my ______?"%patient_sibling_name,"answer":patient_sibling_relation,"type":"text","image":patient_sibling_image}
				questions.append(question)
				question2 = {"question":"Where does %s live?"%patient_sibling_name,"answer":patient_sibling_city,"type":"text"}
				questions.append(question2)
				question3 = {"question":"Who is this?","answer":patient_sibling_name,"type":"text","image":patient_sibling_image}
				questions.append(question3)


			try:
				cursor.execute("""
					SELECT category_id FROM ram_categories WHERE creator_id=%s AND category_name=%s
					""",(creator_id,'default_personal_memory'))
				category_id = cursor.fetchone()[0]

				try:
					cursor.execute("""
						INSERT INTO ram_templates(category_id,patient_id,creator_id,creator_role,template_name) VALUES(%s,%s,%s,%s,%s) RETURNING template_id
						""",(category_id,patient_id,creator_id,'caregiver','Parents & Siblings'))
					postgres.commit()
					template_id = cursor.fetchone()[0]

					for i in questions:

						try:
							cursor.execute("""
									INSERT INTO ram_questions(template_id,questions,creator_id,patient_id,section) VALUES(%s,%s,%s,%s,%s)
									""",(template_id,json.dumps(i),creator_id,patient_id,'family'))
							postgres.commit()
						except Exception as e:
							postgres.rollback()
							print("In except of patientProfileFive INNER MOST INSERT ",e)
				except Exception as e:
					postgres.rollback()
					print("In except of patientProfileFive INSERT OPERATION",e)


			except Exception as e:
				print("In except of patientProfileFive",e)









			# save to DB as template in personal memory

		elif messageLabel == "patientProfileSix":
			print("In patientProfileSix")
			friends = messageReceived['friends']
			creator_id = messageReceived['creator_id']
			patient_id = messageReceived['patient_id']

			questions = []


			for i in friends:
				i = json.loads(i)
				patient_friend_name = i['patient_friend_name']
				patient_friend_relation = "Friend"
				patient_friend_city = i['patient_friend_city']
				patient_friend_image = i['patient_friend_image']

				question = {"question":"%s is my ______?"%patient_friend_name,"answer":patient_friend_relation,"type":"text"}
				questions.append(question)
				question2 = {"question":"Where does %s live?"%patient_friend_name,"answer":patient_friend_city,"type":"text"}
				questions.append(question2)
				question3 = {"question":"Who is this?","answer":patient_friend_name,"type":"text","image":patient_friend_image}
				questions.append(question3)


			try:
				cursor.execute("""
					SELECT category_id FROM ram_categories WHERE creator_id=%s AND category_name=%s
					""",(creator_id,'default_personal_memory'))
				category_id = cursor.fetchone()[0]

				try:
					cursor.execute("""
						INSERT INTO ram_templates(category_id,patient_id,creator_id,creator_role,template_name) VALUES(%s,%s,%s,%s,%s) RETURNING template_id
						""",(category_id,patient_id,creator_id,'caregiver','Friends'))
					postgres.commit()
					template_id = cursor.fetchone()[0]

					for i in questions:
						try:
							cursor.execute("""
									INSERT INTO ram_questions(template_id,questions,creator_id,patient_id,section) VALUES(%s,%s,%s,%s,%s)
									""",(template_id,json.dumps(i),creator_id,patient_id,'friends'))
							postgres.commit()
						except Exception as e:
							postgres.rollback()
							print("In except of patientProfileSix INNER MOST INSERT ",e)
				except Exception as e:
					postgres.rollback()
					print("In except of patientProfileSix INSERT OPERATION",e)


			except Exception as e:
				print("In except of patientProfileSix",e)







			# save to DB as template in personal memory

		elif messageLabel == "showTemplatesOfCategory":
			print("In showTemplatesOfCategory")
			categoryNameFromClient = messageReceived['categoryNameFromClient']
			creator_id = messageReceived['creator_id']


			try:
				cursor.execute("""
					SELECT category_id FROM ram_categories WHERE creator_id=%s AND category_name=%s
					""",(creator_id,categoryNameFromClient))
				category_id = cursor.fetchone()[0]

				try:
					cursor.execute("""
						SELECT template_id,template_name FROM ram_templates WHERE category_id=%s
						""",(category_id,))
					templateDetails = cursor.fetchall()
					print(templateDetails)



					messageToSendToClient = {"messageLabel":"showTemplatesOfCategory","templateDetails":templateDetails,"categoryName":categoryNameFromClient}
					self.write_message(json.dumps(messageToSendToClient))
				except Exception as e:
					print("In except of showTemplatesOfCategory SELECT",e)

			except Exception as e:
				print("In except of showTemplatesOfCategory",e)







			# get the templates of this particular category from the db and send them back to the client

		elif messageLabel == "showQuestionsOfTemplate":
			print("In showQuestionsOfTemplate")
			templateIdFromClient = messageReceived['templateIdFromClient']

			try:
				cursor.execute("""
					SELECT question_id,questions FROM ram_questions WHERE template_id=%s

					""",(templateIdFromClient,))
				questionData = cursor.fetchall()


				messageToSendToClient = {"messageLabel":"showQuestionsOfTemplate","questions":questionData}
				self.write_message(json.dumps(messageToSendToClient))

			except Exception as e:
				print("In except of showQuestionsOfTemplate ",e)

		elif messageLabel == "showQuestionsOfTemplate2":
			print("In showQuestionsOfTemplate")
			templateIdFromClient = messageReceived['templateIdFromClient']

			try:
				cursor.execute("""
					SELECT question_id,questions FROM ram_questions WHERE template_id=%s

					""",(templateIdFromClient,))
				questionData = cursor.fetchall()


				messageToSendToClient = {"messageLabel":"showQuestionsOfTemplate2","questions":questionData}
				self.write_message(json.dumps(messageToSendToClient))

			except Exception as e:
				print("In except of showQuestionsOfTemplate ",e)

		elif messageLabel == "updateQuestion":
			print(" In updateQuestion")
			question_id = messageReceived['question_id']
			question = messageReceived['question']
			answer = messageReceived['answer']
			typeOfQuestion = messageReceived['typeOfQuestion']
			try:
				image = messageReceived['image']
				questionsDict = {"question":question,"answer":answer,"type":typeOfQuestion,"image":image}
			except:
				questionsDict = {"question":question,"answer":answer,"type":typeOfQuestion}

			try:
				cursor.execute("""
					UPDATE ram_questions SET questions=%s WHERE question_id=%s
					""",(json.dumps(questionsDict),question_id))
				postgres.commit()
			except Exception as e:
				postgres.rollback()
				print("In except of updateQuestion",e)

		elif messageLabel == "createNewTemplate":
			print("in createNewTemplate",messageReceived)
			creator_id = messageReceived['creator_id']
			patient_id = messageReceived['patient_id']
			category_name = messageReceived['category_name']
			template_name = messageReceived['template_name']


			try:
				cursor.execute("""
						SELECT category_id FROM ram_categories WHERE creator_id=%s AND category_name=%s
						""",(creator_id,category_name))
				category_id = cursor.fetchone()[0]
				print("category_id",category_id)

				try:
					cursor.execute("""
						INSERT INTO ram_templates(category_id,patient_id,creator_id,creator_role,template_name) VALUES(%s,%s,%s,%s,%s) RETURNING template_id
						""",(category_id,patient_id,creator_id,'caregiver',template_name))
					postgres.commit()
					template_id = cursor.fetchone()[0]
					self.write_message(json.dumps({"messageLabel":"createNewTemplate","template_id":template_id}))

				except Exception as e:
					postgres.rollback()
					print("In except of createNewTemplate INSERT",e)
			except Exception as e:
				print("In outermost except of createNewTemplate",e)

		elif messageLabel == "addQuestion":
			print("In addQuestion")
			creator_id = messageReceived['creator_id']
			patient_id = messageReceived['patient_id']
			template_id = messageReceived['template_id']
			question = messageReceived['question']

			try:
				cursor.execute("""
								INSERT INTO ram_questions(template_id,questions,creator_id,patient_id,section) VALUES(%s,%s,%s,%s,%s)
							""",(template_id,json.dumps(question),creator_id,patient_id,"examination"))
				postgres.commit()
			except Exception as e:
				postgres.rollback()
				print("In except addQuestion",e)
		elif messageLabel == "bringQuestions":
			print("In bringQuestions")
			patient_id = messageReceived['patient_id']

			try:
				cursor.execute("""
					SELECT questions FROM ram_questions WHERE patient_id=%s
					""",(patient_id,))
				questions = cursor.fetchall()
				messageToSendToClient = {"messageLabel":"bringQuestions","questions":questions}
				self.write_message(json.dumps(messageToSendToClient))
			except:
				print("In except of bringQuestions")












	def on_close(self):
		print("Connection Closed")












handlers = [
    (r'/ws',WSHandler),
    (r'/',IndexHandler),
    (r'/createtemplate',CreateTemplateHandler),



]

if __name__ == "__main__":
    parse_command_line()
    # template path should be given here only unlike handlers
    app = tornado.web.Application(handlers, template_path=os.path.join(os.path.dirname(__file__), "templates"),
                                  static_path=os.path.join(os.path.dirname(__file__), "static"),cookie_secret="61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=", debug=True)
    http_server = tornado.httpserver.HTTPServer(app)
    options.port = 8000
    http_server.listen(options.port)
    print("Live at %s"%options.port)
    loop = tornado.ioloop.IOLoop.instance()
    loop.start()
