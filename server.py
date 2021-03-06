import json, types
from   tornado import websocket
import tornado
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import threading 
from jsonTargets 	import *
from target		import Target
from targetIo 		import *
from string  		import *
from games   		import *

import signal 
is_closing = False

global gameserver 
gameserver = None

def signalHandler(signum, frame):
	global is_closing 
	is_closing = True

def tryExit():
	global is_closing, gameserver
	
	if (is_closing):
		print "Shutting down the server...."
			
		print "stopping server!"
		if (gameserver is not None):
			gameserver.disconnect()

		instance = tornado.ioloop.IOLoop.instance()
		instance.stop()
		print "Stopped server...."

# Stackoverflow.com - questions 6131915
class ServerGame(tornado.websocket.WebSocketHandler):
	def check_origin(self, origin):
		return True 

	def open(self):
		global gameserver
		print "*** web socket opened ***"

		self.gameDir 	 = "./games"
		self.gameQuery 	 = "getgames"
		self.gameStart 	 = "startgame"
		self.gameStop    = "stopgame"
		self.gameTargets = "gettargets" 
		self.games 	 = {}

		self.manager 	 = GameManager()
		self.manager.readGames(self.gameDir, 60)

	
		if (gameserver  is not None):
			print "Left over games..."
			try:
	
	
					try:
						gameServer.kill()
					except:
						print "failed."
						pass
			except:
				print "failed"
				pass		
		self.flairGame   = None
		self.gameThread	 = None
		self.gameProc 	 = TargetIo()

		# start the flair game
		self.spawnFlair()

		gameserver  = self

	def on_message(self, message):		
		print "\t", "Message from client: " + message
		data 		= json.loads(lower(message))
		newGame 	= None
		messageOut 	= ""
		if (data.has_key(self.gameQuery)):
			messageOut = u"%s"%(self.manager)
			self.write_message(messageOut)
		elif (data.has_key(self.gameStart)):
			# this part starts a new game...
			gameId 	= data[self.gameStart]
			game 	= self.manager.getGame(gameId)
			skip = False
			
			try:
				if self.flairGame is None:
					print "ignoring game is already in progress"
					skip = True
			except:
				self.flairGame = None
				pass

			if (game is not None and not skip):
				for t in game.targets:
					t.reset()
			  	messageOut 	= ConvertTargetsToJson(game.targets) 
				newGame 	= game
			else:
			  	messageOut = u'{"targets":null}' 

			print "\treplying with", messageOut
			self.write_message(messageOut)
			if (newGame is not None and not skip):
				if (self.gameThread is not None):
					self.kill()
				self.spawn(newGame)
			
		elif (data.has_key(self.gameTargets)):
			print "handling game target request", self.gameTargets
			gameId  = data[self.gameTargets]
			print "retrieving game data", gameId

			game 	= self.manager.getGame(gameId)
			if (game is not None):
				messageOut = ConvertTargetsToJson(game.targets)
			else:
				messageOut = u'{"targets":null}'
			self.write_message(messageOut)

		elif (data.has_key(self.gameStop)):
			print "aborting game..."
			self.kill()
			self.spawnFlair()
			self.flairGame = self.gameThread
			self.write_message(u'{"status": "stopped"}')
		else:
			# this part starts a 
			messageOut = u"You said this: %s" % (message)
			print "\t"*2, ">> Message Out: ", messageOut
			self.write_message(messageOut)
		
	def kill(self):
		'''
		 need to kill the running thread
		'''
		if (self.gameProc is not None):
			self.gameProc.abort()
		
		if (self.gameThread is None):
			return

		self.gameThread.join()
		self.gameThread = None
	def kill2(self, myProc, myThread):
		'''
		 need to kill the running thread
		'''
		if (myProc is not None):
			myProc.abort()
		
		if (myThread is None):
			return

		myThread.join()
		myThread = None

	def disconnect(self):
		self.kill()
		try:
			self.write_message(u'{"status": "disconnect"}')
		except:
			pass
	def spawnFlair(self):
		game = self.manager.getFlairGame()
		self.gameThread = threading.Thread(target=self.gameProc.flair, args=(game, self.notify))
		self.gameThread.start()
		self.flairGame = self.gameThread

	def spawn(self, game):
		# create a new game and spawn 
		# a thread to run 

		self.gameThread = threading.Thread(target=self.gameProc.run, args=(game, self.notify))
		self.gameThread.start()
		

	def on_close(self):
		print "*** web socket closed ***"
		self.kill()
		self.spawnFlair()
	
	def notify(self, targets):
		messageOut = ConvertTargetsToJson(targets)
		print "\t"*2, "Notifying targets hit", messageOut
		self.write_message("%s" % (messageOut))

def startWeb(port, timeout = 60):
	global gameserver
	application = tornado.web.Application([
		(r'/ws', ServerGame),
	])

	signal.signal(signal.SIGINT, signalHandler)
	
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(port)
	
	tornado.ioloop.PeriodicCallback(tryExit, 100).start()
	try:
		tornado.ioloop.IOLoop.instance().start()
	except KeyboardInterrupt:
		print
		print "\tStopping server!"
		instance = tornado.ioloop.IOLoop.instance()
		if (gameserver is not None):
			print "\tKilling Game Server"
			gameserver.disconnect()
		instance.stop()
	
			

if __name__ == "__main__":
	startWeb(4500, timeout = 120)






