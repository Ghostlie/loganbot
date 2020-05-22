from libs import google
import random
import requests
import json
import traceback
import time
import os
import math
from colorama import Fore, Back, Style
import threading

header = {'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}

owner = ['5a0f8c766b25a145008b4570']



class commands_container(type):
	
	commands = {}
	
	@classmethod
	def add(self, aliases, function):
		if isinstance(aliases, str): aliases = [aliases]
		assert isinstance(aliases, list), f"Function {function.__name__} aliases must be str or list of strings"
		for alias in aliases:
			assert not self.commands.get(alias), f"Function {function.__name__} already exists for {alias}"
			self.commands[alias] = function
			
	def __getitem__(self, index):
		return self.commands.get(index)
	
class pool(metaclass=commands_container): pass

def command(*args, **kwargs): 
	def decorator(function):
		aliases = []
		if name := kwargs.get("name"):
			aliases.append(name)
		else:
			aliases.append(function.__name__)
		if kwargs.get("aliases"):
			aliases.extend(kwargs["aliases"])
		pool.add(aliases, function) 
		return function
	return decorator


def execute(function, ctx):
	try: function(ctx)
	except: traceback.print_exc()
		
		
def user_or_other(ctx, specific_other=None):
	
	channel = ctx.channel
	message = ctx.message
	author = message.author
	other = message.command.arguments
	
	if not specific_other:
		specific_other = other
	
	if other:
	
		other = ctx.bot.user_by_nick(specific_other)

		if not other:
			channel.send("I couldn't find that user! 😕")
			False
			
		return other
	
	else:
		author.get_data()
		return author
	
	
	
def nick_by_id(bot, id_list):
	
	nick_list = []
	tasks = []
	
	def request_data(user_id, container):
		other_user = bot.user(user_id)
		if other_user: user_nick = other_user.name
		else: user_nick = "<unknown user>"
		container.append(user_nick)
	
	for user_id in id_list:
		task = threading.Thread(target=request_data, args=(user_id,nick_list))
		task.start()
		tasks.append(task)
		
	[task.join() for task in tasks]
		
	return nick_list


def paginate(data, page=1, limit=30):
	max_page = math.ceil(len(data)/limit)
	page = min(max(int(page), 1), max_page)
	chunk = data[(page-1)*limit:page*limit]
	return chunk, page, max_page


help_msg = """
This is where you write your help message

:)
"""

@command(aliases = ["commands"], name = "help")
def _help(ctx):
	
	channel = ctx.channel
	message = ctx.message
	author = message.author
	category = message.command.arguments.lower()

	if category == "admin":
		msg = admin_help
	else:
		msg = help_msg

	channel.send(msg)

	
@command()
def say(ctx):
	ctx.channel.send(ctx.message.command.arguments)
	

@command()
def ping(ctx):
	channel = ctx.channel
	message = ctx.message
	author = message.author
	latency = int(time.time()*1000)-message.ts
	
	channel.send(f"Pong! {latency}ms")


@command(aliases = ["add"])
def invite(ctx):
	channel = ctx.channel
	message = ctx.message
	other = message.command.arguments

	if " " in other:
		channel.send("Specify only one user")
		return
	if channel.type == "chat":
		channel.send("I cannot invite people to a dm")
		return
	other_user = user_or_other(ctx)
	if not other_user:
		return
	response = channel.invite(other_user)
	if not response:
		channel.send(f"{other_user.name} was invited")
	else:
		channel.send(response)


@command()
def admins(ctx):
	channel = ctx.channel
	channel.get_admins()
	admin_nicks = list(sorted(nick_by_id(ctx.bot, channel.admins.ids()), key=str.lower))
	admin_list = "\n".join(admin_nicks)
	channel.send(f"The admins are: \n\n{admin_list}")

@command()
def admin(ctx, mode="add"):
	channel = ctx.channel
	message = ctx.message
	author = message.author
	other = message.command.arguments
	channel.get_admins()
	other_user = user_or_other(ctx)

	if channel.type == "chat":
		return

	if author.id not in owner:
		channel.send("No.")
		return
	else:
		channel.admin(other_user)
		channel.send(f"{other_user.name} is now admin")


@command()
def unadmin(ctx, mode="remove"):
	channel = ctx.channel
	message = ctx.message
	author = message.author
	other = message.command.arguments

	channel.get_admins()
	other_user = user_or_other(ctx)
	channel.unadmin(other_user)
	channel.send(f"{other_user.name} has been unadmined")


@command()
def kick(ctx, mode="remove"):
	channel = ctx.channel
	message = ctx.message
	author = message.author
	other = message.command.arguments
	channel.get_admins()
	other_user = user_or_other(ctx)
	if author.id in owner:
		channel.admin(author)
	channel.kick(other_user)


@command()
def colorme(ctx):
	channel = ctx.channel
	message = ctx.message
	author = message.author
	color = message.command.arguments.strip("#").upper()
	if author.id not in owner:
		return channel.send("No")
	if len(color) != 6:
		return channel.send("That is not a valid color")
	url = f"https://api-us-1.sendbird.com/v3/users/{author.id}/metadata"
	headers = {"Session-Key": '1bcf7a6dcf160d2d313cfdf8b70348eb46a93e5b'}
	payload = json.dumps({"metadata": {"nick_color": color}})
	r = requests.put(url, data=payload, headers=headers).json()
	if "error" in r:
		r = requests.post(url, data=payload, headers=headers).json()
	channel.send("Color successfully updated")


@command()
def pfpme(ctx):
	channel = ctx.channel
	message = ctx.message
	author = message.author
	image_url = message.command.arguments
	if author.id not in owner:
		channel.send("No")
		return
	if not image_url.startswith("http"):
		other_user = user_or_other(ctx)
		if not other_user:
				return
		image_url = other_user.image
	url = f"https://api-us-1.sendbird.com/v3/users/{author.id}"
	headers = {"Session-Key": '1bcf7a6dcf160d2d313cfdf8b70348eb46a93e5b'}
	payload = json.dumps({"profile_url": image_url})
	r = requests.put(url, data=payload, headers=headers)
	channel.send(f"{author.name}'s chat profile picture has been changed")


@command()
def alts(ctx):
	channel = ctx.channel
	message = ctx.message
	author = message.author
	me = ctx.bot.me
	other = message.command.arguments
	host = ctx.bot.ifunny_host
	if author.id not in owner:
		return
	if channel.type != "chat":
		return
	if not other:
		channel.send("huh")
		return
	other_user = user_or_other(ctx)
	if not other_user:
		return
	channel.send("ight.")
	header = {"Authorization": "Bearer " + ctx.bot.bearer}
	block_url = f"{host}/users/my/blocked/{other_user.id}?type=installation"
	get_blocked_url = f"{host}/users/{me}/blocked/data"
	block_response = requests.put(block_url, headers=header).text
	r = requests.get(get_blocked_url, headers=header).json()
	r = requests.delete(block_url, headers=header)
