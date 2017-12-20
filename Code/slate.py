"""
Project: Project FandRec
Programmed by: David Williams
Last Modified: 11/21/2017
Description: Takes in a frame and finds faces in the picture. If the frame contains a face that has been registered,
			 it will also check next to the face for fingers held up. If the number of fingers is mapped to action to be 
			 taken then a tag will be sent to CoMPES to tell it what to do.
Notes:
	1. The camera client must be running on the camera for it to connect to this server, the server must be running first.



Liscense:
Copyright (c) 2017, FandRec Dev Team
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
	* Redistributions of source code must retain the above copyright
	  notice, this list of conditions and the following disclaimer.
	* Redistributions in binary form must reproduce the above copyright
	  notice, this list of conditions and the following disclaimer in the
	  documentation and/or other materials provided with the distribution.
	* Neither the name of the FandRec Dev Team nor the
	  names of its contributors may be used to endorse or promote products
	  derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL FandRec Dev Team BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
#==============================Imports=======================================
import sys, ujson, cv2, numpy, base64, os, gesture
from pathlib import Path

from multiprocessing import Queue

from twisted.python import log

from twisted.internet import reactor

from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File

from autobahn.twisted.websocket import WebSocketClientFactory, \
	 WebSocketServerFactory, WebSocketClientProtocol, \
	 WebSocketServerProtocol, connectWS, listenWS
from autobahn.twisted.resource import WebSocketResource
from cvo import CVO

#==========================Global Variables==================================
queues = {
	"rawFrame":Queue(),
	"from_tagProc_to_hubClient":Queue()
}

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create(2, 2, 7, 7, 5)
usernames = {}
registered_ids = set()
font = cv2.FONT_HERSHEY_SIMPLEX
opt = "Dropped Frame"
sampleSize = 100
samples = 0
userID = -1
sampleImages = []
compesConnected = False
# targetACU = None
# Cvo = None
targetACU = "lab_cam"
Cvo = CVO("""{"fan":{"Classification":"devices\\household\\HVAC\\fan","Actions":["Turn On","Turn off"],"Defined States":["OFF","ON"],"Current State":"OFF","Last Action":"Turn On"},"light":{"Classification":"devices\\household\\lighting\\desk light","Actions":["Turn On","Turn off"],"Defined States":["OFF","ON"],"Current State":"OFF","Last Action":"Turn On"},"lab_cam":{"Classification":"devices\\audio-visual\\visual\\camera\\webcam","Actions":"NA","Defined States":["User_Jared_Gesture_None","User_Jared_Gesture_1Finger"],"Current State":"User_Jared_Gesture_None","Last Action":"N"},"lab_mic":{"Classification":"devices\\audio-visual\\audio\\microphone\\2-channel","Actions":"NA","Defined States":["Turn off the fan","Turn on the fan"],"Current State":"Turn off the fan","Last Action":"N"}}""".replace("\\", "/"))
commandDict = {}
lastSentTag = ""

#============================Modules=========================================
def detection():
	"""
	Programmed by: David Williams, Aspen Henry, and Slate Hayes
	Description: detection is a state where the server tries to find all the faces in a frame, if a face is registered
				 then it looks for fingers held up next to the face.
	"""
	#STEP 1: Get and Process frame
	# print("Detection!")
	frame = ''
	if not queues["rawFrame"].empty():
		frame = queues["rawFrame"].get_nowait()

		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		faces = face_cascade.detectMultiScale(gray, 1.3, 5)

		for (x, y, w, h) in faces:
			ID, conf = recognizer.predict(cv2.resize(gray[y:y+h, x:x+w], (400, 400)))
			#print("User ID:",ID, "\tconf:", conf)
			# print(conf)
			global registered_ids
			if ID in registered_ids:
				cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 255, 0, 2))
				cv2.rectangle(frame, (x-int(1.5*w), y-int(1.5*h/2)), (x-2, y+int(1.5*(h/2))), (255, 0, 0, 2))
				
				cv2.putText(frame, usernames[ID], (x, y+h+40), font, 2,(255,255,255),1,cv2.LINE_AA)
				fingers = -1
				roi = frame[y-int(1.5*h/2):y+int(1.5*h/2), x-int(1.5*w):x-2]
				fingers = gesture.get_fingers(roi, True)
				
				cv2.putText(frame, str(fingers), (x-int(1.5*w), y+int(1.5*h/2)+5), font, 2, (255,255,255), 1, cv2.LINE_AA)
				tagProcessing(usernames[ID], fingers)
				#print("User ID:",ID,"  Fingers:", fingers)

			else:
				cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 0, 255, 2))
				cv2.putText(frame, "unkown", (x, y+h+40), font, 1,(255,255,255),1,cv2.LINE_AA)
		#STEP 2: Facial Recognition
		#STEP 3: Gesture Recognition
		#STEP 4: Build CoMPES Tag
		#STEP 5: Send processed frame to webpage

	return frame
	
def registration():
	"""
	Programmed by: David Williams, Aspen Henry
	Description: registration is a state where a new user can put there face into the system so they can use the system.
	Notes: 
		1.This state only allows for one face in the frame at a time so the user must be the only one in front of the camera.
	"""
	#STEP 1: Get and Process frame
	# print("Registration!")
	frame = ''
	global samples, sampleSize, userID, recognizer, sampleImages, opt
	if samples >= sampleSize:
		idArray = [userID] * sampleSize
		sampleImages = sampleImages[0:100]

		if Path('./trainingData/trainingData.xml').is_file():
			recognizer.update(sampleImages, numpy.array(idArray))
		else:
			recognizer.train(sampleImages, numpy.array(idArray))
		recognizer.write('./trainingData/trainingData.xml')

		sampleImages = []
		print("Trained!")
		opt = "register"
	elif not queues["rawFrame"].empty():
		frame = queues["rawFrame"].get_nowait()
		
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		faces = face_cascade.detectMultiScale(gray, 1.3, 5)
		if len(faces) > 1:
			pass
		else:
			for (x, y, w, h) in faces:
				samples += 1
				frame = cv2.resize(gray[y:y+h, x:x+w], (400, 400))
				sampleImages.append(frame)

	return frame

def initRecognizer():
	"""
	Programmed by: David Williams
	Description: Trains the recognizer when the server is started, if there is no training data, then it goes strait into
				 registration to create the data.
	"""
	global recognizer, usernames, registered_ids
	if Path('./trainingData/trainingData.xml').is_file():
		recognizer.read('./trainingData/trainingData.xml')

		file = open('usernames.txt', 'r+')
		usernames = {int(e.strip().split("=")[1]): e.strip().split("=")[0] for e in file.readlines()[1:]}
		
		registered_ids = set(usernames.keys())
		file.close()
	else:
		opt = "register"

def getCom(queue):
	"""
	Programmed by: David Williams
	Description: gets the communication from the appropriate queue
	"""
	#gets the communication from the appropriate queue
	try:
		yield queues[queue].get(False)
	except:
		yield ""	
	
def putCom(queue, payload):
	"""
	Programmed by: David Williams
	Description: places the communication into the appropriate queue
	"""
	#places the communication into the appropriate queue
	queues[queue].put(payload, False) #False == no wait on placement

def tagProcessing(name, finger_count):
	"""
	Programmed by: David Williams
	Description: packages the tag to be sent to a CoMPES hub
	"""
	#packages the tag to be sent to a CoMPES Hub
	#Add packaging codes
	global targetACU, commandDict, lastSentTag
	if (targetACU != None) and ((name, finger_count) in commandDict):
		tag = targetACU+",,"+commandDict[(name, finger_count)]
		if lastSentTag != tag:
			lastSentTag = tag
			putCom("from_tagProc_to_hubClient", ujson.dumps((targetACU, tag)))

def cvoProcessing(cvo):
	"""
	Programmed by: David Williams and Jake Thomas
	Description: Takes in the cvo and loades it into the know APU's.
	"""
	global Cvo
	#process a json of the ndf
	#modes: PS-recieve NDF from the PS, Hub-recieve cvo from hub
	#NDF = ujson.loads(NDF) Uncomment this line when using a real NDF
	print(cvo)
	Cvo = CVO(cvo)
	#!- Analysis of CVO -!#

def saveItem(item):
	global commandDict
	c = item.split('|')
	if len(c) == 3:
		commandDict[(c[0], int(c[1]))] = c[2]
		with (open('savedCommands.txt', 'a+')) as f:
			f.write('\n' + item)
	else:
		print("invalid command")

def loadCommands():
	global commandDict
	with (open('savedCommands.txt', 'r+')) as f:
		attrs = [line.split('|') for line in f.read().split('\n')][1:]
		for a in attrs:
			commandDict[(a[0], int(a[1]))] = a[2]

#==========================Web Server========================================
class WebsiteServerProtocol(WebSocketServerProtocol):
	"""
	Programmed by: David Williams and Jake Thomas
	Description: Handles the connections from clients that are requesting to connect the server.
	"""
	
	def __init__(self):
		WebSocketServerProtocol.__init__(self)

	def onConnect(self, request):
		"""
		Programmed by: David Williams
		Description: Prints the web socket request
		"""
		print("WebSocket connection request: {}".format(request.peer))

	def onOpen(self):
		"""
		Programmed by: David Williams
		Description: Sends messages to the client when the connection is open
		"""
		global opt
		self.sendMessage(opt.encode("utf8"))
		self.sendB64String()

	def onMessage(self, data, isBinary):
		"""
		Programmed by: David Williams, Aspen Henry, and Jake Thomas 
		Description: Receives a message from the client, if the message is doregister then it will register the new user.
		"""
		global opt, targetACU
		msg = data.decode("utf8")
		print(msg)
		if msg.startswith("doregister"):
			opt = "doregister"
			print("Training...")
			username = msg.split('|')[1]
			################## Getting Id for the new user ############################################
			file = open('idCounter.txt', 'r+')
			newIdLines = []

			idValue = file.read()
			global userID
			userID = int(idValue)
			newId = int(idValue) + 1

			newIdLines.append(str(newId))
			registered_ids.add(userID)

			file.seek(0)
			file.truncate()

			file.writelines(newIdLines)
			file.close()
			##########################################################################################

			################### Storing Username and ID pair #########################################
			file2 = open('usernames.txt', 'r+')
			file2Contents = file2.readlines()
			file2.close()

			newUserLines = []
			newUser = '\n' + username + '=' + str(idValue)
			newUserLines.append(newUser)
			file3 = open('usernames.txt', 'a')
			file3.writelines(newUserLines)
			file3.close()

			usernames[userID] = username

			global samples
			samples = 0
		elif msg == u"register":
			global Cvo
			opt = "register"
			if Cvo is not None:
				cvoMessage = "cvoMessage|"
				for v in usernames.values():
					cvoMessage += v + ','
				cvoMessage = cvoMessage[:-1]
				cvoMessage += '|'
				for state in Cvo.get_acu_states(targetACU):
					cvoMessage += state + ','
				cvoMessage = cvoMessage[:-1]
				print(cvoMessage)
				self.sendMessage(cvoMessage.encode("utf8"))
		elif msg == u"detect":
			loadCommands()
			opt = "detect"
		elif msg == u"disconnect":
			self.transport.loseConnection()
		elif msg.startswith("sendCompes"):
			global compesConnected
			if not compesConnected:
				hub_address = "ws://146.7.44.166:8084"
				supList = msg.split('|')[1:]
				targetACU = supList[0]
				hub_header = {'acu-id' : supList[0], 'hub-id' : supList[1], 'net-id' : supList[2], 
				  'user-id' : supList[3], 'user-pass' : supList[4], 'hub-access-key' : supList[5]}
				print(hub_header)
				hub_factory = WebSocketClientFactory(hub_address, headers=hub_header)
				hub_factory.protocol = HubClientProtocol
				connectWS(hub_factory)
				compesConnected = True
		elif msg.startswith('assign'):
			saveItem(msg[7:])


	def sendB64String(self):
		"""
		Programmed by: David Williams
		Description: Sets the state of the server and then packages the processed frame to be sent to the webpage
		"""		
		#STEP 1: Get frames from Register or Detection Module
		global opt
		frame = ''
		if opt == "doregister":
			frame = registration()
		elif opt == "detect":
			frame = detection()
		elif opt == "register":
			global queues
			if not queues["rawFrame"].empty():
				frame = queues["rawFrame"].get_nowait()

		if type(frame) != type(''):
			#STEP 2: Package for sending
			frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])[1]
			frame = base64.b64encode(frame)

			self.sendMessage(frame)
		else:
			# print("Error: Frame dropped!")
			self.sendMessage("Dropped Frame".encode("utf8"))
		reactor.callLater(0.01, self.sendB64String)

	def connectionLost(self, reason):
		"""
		Programmed by: David Williams
		Description: Closes the WebSocket and prints that it was closed.
		"""
		WebSocketServerProtocol.connectionLost(self, reason)
		print("Connection was closed.")

#==========================Camera Server=====================================
class CameraServerProtocol(WebSocketServerProtocol):
	"""
	Programmed by: David Williams
	Description: Takes in the frames from the camera client, decompresses it and stores it in the queue.
	"""
	def onConnect(self, request):
		"""
		Programmed by: David Williams
		Description: Prints the connection that was made with the client
		"""
		print("WebSocket connection request: {}".format(request.peer))

	def onOpen(self):
		"""
		Programmed by: David Williams
		Description: Prints the connection that was made with the client
		"""
		self.sendMessage("start capture".encode('utf8'))

	def onMessage(self, data, isBinary):
		"""
		Programmed by: David Williams
		Description: Decodes the image sent from the camera client
		"""
		#STEP 1: Load in, convert, and decompress frame for use
		frame = ujson.loads(data.decode("utf8"))
		frame = numpy.asarray(frame, numpy.uint8)
		frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

		#STEP 2: If the Queue is full, pop an image
		#May want to find optimal qsize to prevent stutter
		if queues["rawFrame"].qsize() >= 15:
			queues["rawFrame"].get_nowait()

		queues["rawFrame"].put_nowait(frame)

		self.sendMessage("send next frame".encode('utf8'))

	def connectionLost(self, reason):
		"""
		Programmed by: David Williams
		Description: Closes the connection when the connection is lost
		"""
		WebSocketServerProtocol.connectionLost(self, reason)
		print("Connection was closed.")

#==========================CoMPES Client=====================================

class HubClientProtocol(WebSocketClientProtocol):
	"""
	Programmed by: David Williams
	Description: Handles the connections to the CoMPES hubs
	"""
	def sendMSG(self):
		"""
		Programmed by: David Williams
		Description: Sends the starting message to the hub
		"""
		#get message from one of the queues
		gen = getCom("from_tagProc_to_hubClient")
		
		#send the message
		msg = next(gen)
		if(msg != ""):
			print(msg)
			self.sendMessage(msg.encode('utf8'))
		reactor.callLater(.05, self.sendMSG)

	def onOpen(self):
		"""
		Programmed by: David Williams
		Description: Starts the sending of the message to the hub
		"""
		self.sendMSG()
		
	def onMessage(self, payload, isBinary):
		"""
		Programmed by: David Williams
		Description: Gets the CVO from CoMPES and starts the processing of it into usable objects
		"""
		#STEP-1: Process the message
		CVO = payload.decode('utf-8').replace("\\", "/")
		
		#STEP-2: Process CVO
		cvoProcessing(CVO)

	def onClose(self, wasClean, code, reason):
		pass

#==========================Slate Main========================================
def main():
	"""
	Programmed by: David Williams
	Description: Starts all of the factories and protocols needed to start the server and all of its functions.
	Notes: 
		1.
		2.
	"""
	log.startLogging(sys.stdout)
	initRecognizer()

	ip_address = "127.0.0.1"
	port_nums = [8090, 8091]
	

	#STEP-1: Start up webpage
	web_factory = WebSocketServerFactory("ws://" + ip_address + ":" + str(port_nums[0]))
	web_factory.protocol = WebsiteServerProtocol
	root = File(".")
	root.putChild(b"ws", WebSocketResource(web_factory))
	site = Site(root)

	#STEP-2: Start up the camera
	cam_factory = WebSocketServerFactory("ws://" + ip_address + ":" + str(port_nums[1]))
	cam_factory.protocol = CameraServerProtocol

	#TEST CODE - PLEASE IGNORE
	#putCom("from_tagProc_to_hubClient", ujson.dumps(("slate_cam",
	#	   "slate_cam,,User_Jared_Gesture_None")))

	#Step-3: Start up the CoMPES PS Client
	
 
	#STEP-5: Setup the reactor
	reactor.listenTCP(port_nums[0], site,
					  interface=ip_address)
	listenWS(cam_factory)
	

	#STEP-6: run
	reactor.run()

if(__name__ == "__main__"):
	main()