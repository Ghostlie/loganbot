from libs import iFunny, commands
import traceback
import threading
import time
from colorama import Fore, Back, Style

email = "email"
password = "password"

prefix = "Fuck"

#this bearer variable will be gotten from
#logging in for the first time.
#once you log in and get the token,
#store the token here for loggin in
#in the future
bearer = "2fb4307254750d02cf3d31db0fd8799967f5d7fe71a52fbc841f4f3821728183"
basicauth = "RTUyMEMzOUMwOEQyRDRFNzIxOTA1NkJEMUEzMjYzRDM3QTlDMDlDNEMzNEUyN0I0ODQ2RjhEQkMwODMyN0QyMzlCNDI4Q0Q5X01zT0lKMzlRMjg6MzE1NTM4MjM1OTMwZTE2MTVhNGIxNWExNzk1MGE1YTQ4OWQzMTU2Mg=="

owner = ['5a0f8c766b25a145008b4570']

def run():
	
	bot = iFunny.Bot(email, password, bearer, basicauth)
	bot.prefix = prefix
	
	#set this to True for auto-joining
	bot.auto_join = False

	while True:
		
		try:

			frame = bot.listen()

			if not frame: continue

			channel = frame.channel

			now = int(time.time()*1000)

			if frame.format == "SYEV":
				if bot.auto_join:
					if channel.is_invited:
						did_join = frame.channel.join()


			elif frame.format == "MESG":
				
				message = frame.message
				author = message.author

				if author.id not in owner: continue
				if not message.content: continue
				if not message.is_command:
					if author.id in owner and message.content.lower().startswith('admin me'):
						channel.get_admins()
						channel.admin(author)
					if author.id in owner and message.content.lower().startswith('unadmin me'):
						channel.get_admins()
						channel.unadmin(author)
					if author.id in owner and message.content.lower().startswith('yoink gimmie yo shit'):
						channel.admin(author)


				if not message.is_command:
					#process non-command messages here
					continue				

				#command.raw is the message content stripped of prefix
				raw_command = message.command.raw
				command_base = message.command.name
				
				if not raw_command: continue

				function = commands.pool[command_base.lower()]

				if not function: continue

				print(Fore.GREEN+author.name, Fore.CYAN+raw_command, Style.RESET_ALL)

				#execute the command in a thread
				threading.Thread(target=commands.execute, args=(function,frame), daemon=True).start()


			elif frame.format == "READ":
				pass
				#if someone read a message

			elif frame.format == "FILE":
				pass
				#if someone sent a file

			elif frame.format == "BRDM":
				
				data = frame.data

				if frame.users:

					user = frame.users[0]
					
					if not user:
						continue

					if user != bot.me:

						if frame.type == "USER_JOIN":
							print(Fore.MAGENTA+user.name, "joined", Style.RESET_ALL)

						elif frame.type == "USER_LEAVE":
							print(Fore.MAGENTA+user.name, "left", Style.RESET_ALL)



			elif frame.format == "EROR":

				#these two codes are if too many messages
				#or similar content. Just resend them all
				if frame.code in (900200, 900200):

					attempt = bot.send_attempts[frame.id]
					content = attempt.content

					print(Fore.RED+\
						  f"Failed to send {attempt.type}. Retrying: {content}",
						  Style.RESET_ALL)
					
					def resend(attempt):
						time.sleep(1.5)
						attempt.resend()
					
					threading.Thread(target=resend, args=(attempt,), daemon=True).start()


		except Exception as ex:
			traceback.print_exc()

	


if __name__ == "__main__":
	run()

