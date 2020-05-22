from libs import channel_manager, user_manager
from libs import fleep
import sys
import json
import requests
import time
import websocket
from websocket import create_connection
import urllib
import urllib.parse
import random
import os
import threading
from colorama import Fore, Back, Style
import traceback


class History:
    history = {}

    def update(self, channel, message):

        if not self.history.get(channel.url):
            self.history[channel.url] = []

        self.history[channel.url].append(message)

    def get(self, channel):
        return self.history.get(channel.url)

    def last(self, channel, type=None):

        history = self.history.get(channel.url)

        if history:

            if not type:
                return history[-1]
            for message in reversed(history):
                if message.type.lower() == type.lower():
                    return message

        return None

    def clear(self, channel=None):
        if not channel:
            self.history = {}
        else:
            self.history[channel.url] = []


class Command:

    def __init__(self, message, bot):

        message = message.lstrip(bot.prefix)
        arguments = message.split()
        self.raw = message
        self.name = ""
        self.arguments = ""
        self.arguments_list = []

        if arguments:
            self.name = arguments[0].lower()
            self.arguments_list = arguments[1:]
            self.arguments = " ".join(self.arguments_list)

    def __eq__(self, other):
        if isinstance(other, Command):
            return self.name == other.name.lower()
        elif isinstance(other, str):
            return self.name == other.lower()
        return False


class User:

    def __init__(self, name, user_id, image=None, metadata={}, device=None, data={}):
        self.name = name
        self.id = user_id
        self.image = image
        self.metadata = metadata
        self.device = device
        self.data = data
        self.ts = int(time.time() * 1000)
        self.url = f"https://ifunny.co/user/{name.lower()}"
        self.ifunny_host = "https://api.ifunny.mobi/v4"

    def get_data(self):
        url = f"http://api.ifunny.mobi/v4/users/{self.id}"
        r = requests.get(url, headers={"Authorization": "Basic " + Bot.basicauth}).json()
        if r["status"] == 200:
            data = r["data"]
        else:
            data = {}
        self.data = data

    def write(self, data):
        user_manager.write(self.id, data)

    def read(self):
        data = user_manager.read(self.id)
        data["bal"] = int(data["bal"])
        return data

    def __eq__(self, other):
        return self.id == other.id

    def get_subscriptions(self):
        cursor = ""
        has_next = True
        self.subscriptions = []

        while has_next:

            url = f"{self.ifunny_host}/users/{self.id}/subscriptions?limit=100000&next={cursor}"
            try:
                data = requests.get(url, headers={"Authorization": "Basic " + Bot.basicauth}).json()
            except:
                continue

            if "error" not in data:
                has_next = data["data"]["users"]["paging"]["hasNext"]
                cursor = data["data"]["users"]["paging"]["cursors"]["next"]
                chunk = [user["id"] for user in data["data"]["users"]["items"]]
                self.subscriptions.extend(chunk)

        return self.subscriptions

    def get_session_key(bot, user):

        url = f"{bot.host}/account"
        header = {"Authorization": "Bearer " + bearer}
        data = requests.get(url=url, headers=header).json()

        if not data["status"] == 200:
            return

        messenger_token = data["data"]["messenger_token"]

        ws = create_connection("wss://ws-us-1.sendbird.com/?" + \
                               f"p=Android&pv=22&sv=3.0.55&ai={bot.app_id}&user_id={user.id}&access_token={messenger_token}")

        frame = ws.recv()

        frame_format = frame[:4]
        frame_data = json.loads(frame[4:])
        key = frame_data.get("key")

        return key


class Message:

    def __init__(self, format, data, bot, parent=None):

        self.type = format
        self.author = Frame.parse_user(data)
        self.id = data.get("msg_id")
        self.ts = data.get("ts")
        self.content = ""
        self.channel = None

        if self.type == "FILE":

            self.content = data["url"]
            self.mime = data["type"]
            self.dimensions = (750,) * 2

            if data["thumbnails"]:
                thumb = data["thumbnails"][0]
                self.dimensions = (thumb["width"], thumb["height"])

            self.width, self.height = self.dimensions

        elif self.type == "MESG":

            self.content = data["message"]
            self.command = self.command = Command(self.content, bot)
            self.is_command = False

            if self.content.startswith(bot.prefix):
                self.is_command = True

    def resend(self):

        if isinstance(self.channel, Channel):

            if self.type == "MESG":
                self.channel.send(self.content)

            elif self.type == "FILE":
                self.channel.upload(self.content, self.mime, self.width, self.height)


class Channel:

    def sendowner(self, message):
        self.bot.send_msgowner(self.url, message)

    def __init__(self, data, bot):

        self.bot = bot
        self.is_invited = False
        self.admins = UserList()
        self.data = data
        self.url = data.get("channel_url")
        self.id = data.get("channel_id")
        self.type = data.get("channel_type")
        self.name = data.get("name")

        if data.get("unread_cnt"):
            if data["unread_cnt"].get("custom_types"):
                self.type = list(data["unread_cnt"]["custom_types"].keys())[0]

        if self.type == "chat":
            if data.get("inviter"):
                self.name = data["inviter"]["nickname"]

    def __eq__(self, channel):
        return self.url == channel.url

    def send(self, message):
        self.bot.send_msg(self.url, message)

    def upload(self, data, mime=None, width=750, height=750):
        if isinstance(data, str) and data.startswith("http"):
            self.bot.send_file(self.url, data, mime, width, height)
        else:
            self.bot.upload_file(self.url, data, mime, width, height)

    def join(self):
        return self.bot.join(self.url)

    def kick(self, user):
        return self.bot.kick(user.id, self.url)

    def invite(self, user):
        return self.bot.invite(user.id, self.url)

    def get_admins(self):
        if self.type != "chat":
            self.admins = self.bot.get_admins(self)
        return self.admins

    def admin(self, user):
        self.admins.append(user)
        self.bot.set_admins(self)
        return self.admins

    def unadmin(self, user):
        self.admins.remove(user)
        self.bot.set_admins(self)
        return self.admins

    def get_members(self):
        return self.bot.list_members(self)

    def get_data(self):
        return self.bot.get_channel_data(self)

    def write(self, data):
        channel_manager.write(self.url, data)

    def read(self):
        return channel_manager.read(self.url)


class List:

    def __init__(self, items=[]):
        self.items = list(items)

    def __iter__(self):
        return self.items

    def __len__(self):
        return len(self.items)


class UserList(List):

    def __contains__(self, user: User):
        return user.id in [i.id for i in self.items]

    def append(self, user: User):
        self.items.append(user)

    def remove(self, user: User):
        self.items = [i for i in self.items if i.id != user.id]

    def ids(self):
        return [i.id for i in self.items]


class ChannelList(List):

    def __contains__(self, channel: Channel):
        return channels.url in [i.url for i in self.channels]

    def append(self, channel: Channel):
        self.channels.append(channel)

    def remove(self, channel: Channel):
        self.channels = [i for i in self.channels if i.url != channel.url]

    def urls(self):
        return [i.url for i in self.channels]


class Frame:

    def __init__(self, format, data, bot):

        self.format = format
        self.data = data
        self.channel = Channel(data, bot)
        self.bot = bot
        self.id = data.get("req_id")
        self.ts = int(time.time() * 1000)

        if data.get("ts"):
            self.ts = data["ts"]

    @classmethod
    def parse_user(self, raw_data):

        data = raw_data.get("user")
        if not data:
            if raw_data.get("user_id"):
                data = raw_data

        if data:
            if data.get("nickname"):
                return User(data["nickname"], data["user_id"],
                            data["profile_url"], data["metadata"])
            elif data.get("name"):
                return User(data["name"], data["guest_id"],
                            data["image"], data["metadata"],
                            device=("Android" if raw_data.get("data") else "iOS"))
        return None

class USEV(Frame):
    def __init__(self, format, data, bot):
        super().__init__(format, data, bot)
        print(self.data)

class MESG(Frame):

    def __init__(self, format, data, bot):
        super().__init__(format, data, bot)
        self.message = Message(format, data, bot)
        self.message.channel = self.channel
        bot.message_history.update(self.channel, self.message)


class FILE(Frame):

    def __init__(self, format, data, bot):
        super().__init__(format, data, bot)
        self.message = Message(format, data, bot)
        self.message.channel = self.channel
        bot.message_history.update(self.channel, self.message)


class READ(Frame):

    def __init__(self, format, data, bot):
        super().__init__(format, data, bot)
        self.user = self.parse_user(data)


class SYEV(Frame):

    def __init__(self, format, data, bot):
        super().__init__(format, data, bot)

        invite = data["data"]

        if invite.get("inviter"):
            self.inviter = self.parse_user(invite["inviter"])
        else:
            self.joinee = self.parse_user(invite)

        self.invitees = []

        if invite.get("invitees"):
            for invitee in invite["invitees"]:
                if invitee["user_id"] == bot.me.id:
                    self.channel.is_invited = True
                self.invitees.append(self.parse_user(invitee))

        else:
            self.joinee = self.parse_user(invite)


class LOGI(Frame):

    def __init__(self, format, data, bot):
        super().__init__(format, data, bot)
        self.user = self.parse_user(data)
        self.login_ts = data.get("login_ts")
        self.bot.sessionkey = data.get("key")


class BRDM(Frame):

    def __init__(self, format, data, bot):
        super().__init__(format, data, bot)

        self.data = json.loads(data["data"])
        self.type = self.data["type"]
        self.message = data["message"]
        self.users = []
        # print(self.data)

        if self.type == "CHANNEL_CHANGE":
            self.changes = self.data["changes"]
            if self.data.get("requester") is not None:
                self.requester = self.parse_user(self.data["requester"])

        elif self.type in ("USER_LEAVE", "USER_JOIN"):
            self.reason = self.data.get("reason")
            self.users = [self.parse_user({"user": user}) for user in self.data["users"]]

    # print(self.type, self.users)


class EROR(Frame):

    def __init__(self, format, data, bot):
        super().__init__(format, data, bot)

        self.id = data["req_id"]
        self.message = data["message"]
        self.code = data["code"]


frames = {"LOGI": LOGI, "SYEV": SYEV, "BRDM": BRDM, "READ": READ, "MESG": MESG, "FILE": FILE, "EROR": EROR, "USEV": USEV}


class Bot:
    ifunny_host = "https://api.ifunny.mobi/v4"
    sendbird_host = "https://api-us-1.sendbird.com/v3"
    app_id = "AFB3A55B-8275-4C1E-AEA8-309842798187"
    basicauth = ""
    prefix = ""
    me = ""
    websoc = None
    sessionkey = ""
    auto_join = True

    message_history = History()
    nick = ""
    subscribers = []
    send_attempts = {}
    authorized_users = UserList()
    auth_file = "users/authorized"
    blacklist_file = "users/blacklisted"

    def __init__(self, email=None, password=None, bearer=None, basicauth=None):

        if not basicauth:
            self.make_auth()

        else:
            self.basicauth = basicauth

        if not bearer:
            if email and password:
                self.login(email, password)

        else:
            self.bearer = bearer
            self.get_messenger()

        if os.path.exists(self.auth_file):
            with open(self.auth_file) as f:
                try:
                    self.authorized_users = iFunny.UserList([User("", i) for i in json.load(f)])
                except:
                    pass

    # threading.Thread(target=self.setnick, daemon=True).start()
    # threading.Thread(target=self.loopcolors, daemon=True).start()
    # threading.Thread(target=self.check_subscribers, daemon=True).start()

    def make_auth(self):
        import os, base64, hashlib
        clientID = "MsOIJ39Q28"
        clientSecret = "PTDc3H8a)Vi=UYap"
        hexstring = os.urandom(36).hex().upper()
        hexId = hexstring + '_' + clientID
        hash_decoded = hexstring + ':' + clientID + ':' + clientSecret
        hash_encoded = hashlib.sha1(hash_decoded.encode('utf-8')).hexdigest()
        auth = base64.b64encode(bytes(hexId + ':' + hash_encoded, 'utf-8')).decode()
        print(Fore.MAGENTA + "Basic auth:\n\n" + auth + Style.RESET_ALL)
        print(Fore.MAGENTA + "\nCopy this token to the client and run again" + \
              Style.RESET_ALL)
        print(
            Fore.RED + "It can take a moment for iFunny to register a new basic auth after using it for the first time. Keep trying in that case." + \
            Style.RESET_ALL)
        sys.exit(0)

    def login(self, email, password):

        oauthurl = f"{self.ifunny_host}/oauth2/token"

        header = {"Authorization": "Basic " + self.basicauth}
        payload = {"grant_type": "password",
                   "username": email,
                   "password": password}

        req = requests.post(url=oauthurl, data=payload, headers=header)

        if "invalid_grant" in req.text:
            print(Fore.RED + "Invalid login. Please check your credentials." + req.text + Style.RESET_ALL)
            sys.exit(-1)

        elif "access_token" in req.text:
            gettoken = req.json()
            self.bearer = gettoken["access_token"]
            print(Fore.MAGENTA + "Bearer token: " + self.bearer + Style.RESET_ALL)
            print(Fore.RED + \
                  "Copy your bearer token above and use it to log in next time" + \
                  Style.RESET_ALL)
            sys.exit(0)

        elif "too_many_user_auths" in req.text:
            print(Fore.RED + "Too many auths" + Style.RESET_ALL)
            sys.exit(-1)

        else:
            print(Fore.RED + "Error could not log you in at this moment." + Style.RESET_ALL)
            print(Fore.RED + "If you are using a new basic auth token please try again." + req.text + Style.RESET_ALL)
            sys.exit(-1)

    def get_messenger(self):

        url = f"{self.ifunny_host}/account"
        header = {"Authorization": "Bearer " + self.bearer}
        r = requests.get(url=url, headers=header).json()

        data = r.get("data")

        if r["status"] == 200 and data:

            self.me = User(*self.parse_ifunny_user(data), data=data)
            self.messenger_token = data.get("messenger_token")

            if self.messenger_token:
                self.connect_chat(self.me.id, self.messenger_token)

            else:
                print(Fore.RED + "Messenger token not found" + Style.RESET_ALL)
                sys.exit(-1)

        else:
            print(r)
            sys.exit(-1)

    def connect_chat(self, uid, token):

        try:
            ws = create_connection(
                f"wss://ws-us-1.sendbird.com/?p=Android&pv=22&sv=3.0.55&ai={self.app_id}&user_id={uid}&access_token={token}")
            print(Fore.MAGENTA + "iFunny bot is online" + Style.RESET_ALL)
            self.websoc = ws

        except Exception as ex:
            print(Fore.RED + "Error loggin in to chat" + format(ex) + Style.RESET_ALL)

    def listen(self):

        try:
            if self.websoc is not None:
                frame = self.websoc.recv()
            else:
                raise Exception("Connection dropped. Reconnecting...")

        except:
            traceback.print_exc()
            self.connect_chat(self.me.id, self.messenger_token)
            frame = None

        if not frame: return None

        frame_format = frame[:4]
        frame_data = json.loads(frame[4:])
        frame = frames.get(frame_format)

        if frame:
            try:
                frame = frame(frame_format, frame_data, self)
            except:
                print(frame_format, frame_data)
                traceback.print_exc()
                return None

        return frame

    def get_authorized_users(self):
        return list(self.authorized_users)

    def get_blacklisted_users(self):
        return list(self.blacklisted_users)

    def msg_from(self, channel):
        if channel:
            return self.history[channel]
        return {}

    def send_msg(self, channel, message):

        if channel:

            ts = int(time.time() * 1000)
            req_id = str(ts) + "_" + str(random.randint(1000, 9999))
            message_data = {"channel_url": channel, "message": message, "type": "MESG", "req_id": req_id}
            to_send = "MESG{}\n".format(json.dumps(message_data))

            try:
                self.websoc.send(to_send)
            except:
                return

            channel = Channel(message_data, self)
            message = Message("MESG", message_data, self)
            message.channel = channel
            self.send_attempts[req_id] = message

    def send_msgowner(self, channel, message):

        if channel:
            channel_url = "sendbird_group_channel_414355_9a1298383ca6b09fdbd80059345f5406a7c5002a"
            ts = int(time.time() * 1000)
            req_id = str(ts) + "_" + str(random.randint(1000, 9999))
            message_data = {"channel_url": channel_url, "message": message, "type": "MESG", "req_id": req_id}
            to_send = "MESG{}\n".format(json.dumps(message_data))

            try:
                self.websoc.send(to_send)
            except:
                return

            channel = Channel(message_data, self)
            message = Message("MESG", message_data, self)
            message.channel = channel
            self.send_attempts[req_id] = message

    def send_file(self, channel, file_url, mime=None, width=750, height=750):

        def normalize_wh(width, height):
            modifier = width / 750
            width, height = int(width / modifier), int(height / modifier)
            return width, height

        width, height = normalize_wh(width, height)

        if not mime:

            if file_url.endswith((".jpg", ".jpeg", ".jpe")):
                mime = "image/jpeg"
            elif file_url.endswith(".png"):
                mime = "image/png"
            elif file_url.endswith(".bmp"):
                mime = "image/bmp"
            elif file_url.endswith(".gif"):
                mime = "image/gif"
            elif file_url.endswith(".midi"):
                mime = "audio/midi"
            elif file_url.endswith((".mpeg", ".mp4")):
                mime = "video/mpeg"
            elif file_url.endswith(".oog"):
                mime = "video/oog"
            elif file_url.endswith(".webm"):
                mime = "video/webm"
            elif file_url.endswith(".webp"):
                mime = "image/webp"
            elif file_url.endswith(".wav"):
                mime = "audio/wav"
            elif file_url.endswith(".mp3"):
                mime = "audio/mp3"

            else:

                r = urllib.request.Request(file_url)

                try:

                    image_data = urllib.request.urlopen(r).read(128)
                    mime = fleep.get(image_data).mime

                    if mime:
                        mime = mime[0]
                        if not mime.startswith("image"):
                            self.send_msg(channel, "Invalid image mime. Try again")
                            return
                    else:
                        self.send_msg(channel, "Error getting the image mime")
                        return

                except Exception as ex:
                    self.send_msg(channel, str(ex))
                    return

        if mime:

            try:

                ts = int(time.time() * 1000)
                req_id = str(ts) + "_" + str(random.randint(1000, 9999))

                message_data = {"channel_url": channel, "name": "image",
                                "req_id": req_id,
                                "type": mime,
                                "url": file_url,
                                "thumbnails": [
                                    {"height": height,
                                     "width": width,
                                     "real_height": height,
                                     "real_width": width,
                                     "url": file_url}]}

                self.websoc.send("FILE{}\n".format(json.dumps(message_data)))

                channel = Channel(message_data, self)
                message = Message("FILE", message_data, self)
                message.channel = channel
                self.send_attempts[req_id] = message

            except:
                print(Fore.RED)
                traceback.print_exc()
                print(Style.RESET_ALL)

    def upload_file(self, channel, image_data, mime=None, width=750, height=750):

        headers = {"Session-Key": self.sessionkey}
        files = {"file": image_data}
        payload = {"thumbnail1": f"{width}, {height}",
                   "thumbnail2": f"{int(width / 2)}, {int(height / 2)}",
                   "channel_url": channel}
        url = f"{self.sendbird_host}/storage/file"
        r = requests.post(url, data=payload, files=files, headers=headers).json()

        if not mime:
            mime = fleep.get(image_data).mime
            if mime:
                mime = mime[0]

        if mime:
            self.send_file(channel, r["url"], mime, width, height)
        else:
            self.send_msg(channel, "Error getting the image mime")

    def search_users(self, user):
        url = f"{self.ifunny_host}/search/users?q={user}&limit=1"
        header = {"Authorization": "Basic " + self.basicauth}
        r = requests.get(url, headers=header).json()
        user_list = UserList()
        if r["status"] == 200 and r["data"]["users"]["items"]:
            for data in r["data"]["users"]["items"]:
                user_list.append(User(*self.parse_ifunny_user(data), data=data))
        return user_list

    def user_by_nick(self, user, auth="basic"):
        url = f"{self.ifunny_host}/users/by_nick/{user}"
        header = {"Authorization": "Basic " + self.basicauth}
        if auth == "bearer": header = {"Authorization": "Bearer " + self.bearer}
        r = requests.get(url, headers=header).json()
        if r["status"] == 200:
            data = r["data"]
            return User(*self.parse_ifunny_user(data), data=data)
        return None

    def get_user_data(self, user_id):
        url = f"{self.ifunny_host}/users/{user_id}"
        r = requests.get(url, headers={"Authorization": "Basic " + self.basicauth}).json()
        if r["status"] == 200:
            return r["data"]
        return None

    def user(self, user_id):
        data = self.get_user_data(user_id)
        if data:
            return User(*self.parse_ifunny_user(data), data=data)
        return None

    def parse_ifunny_user(self, data):
        name = data["original_nick"]
        user_id = data["id"]
        image = data.get("photo")
        if image:
            image = image["url"]
        metadata = {}
        return name, user_id, image, metadata

    def setnick(self):

        with open(nick_file) as f:
            self.nick = f.read()

        url = f"{self.sendbird_host}/users/{self.me.id}"

        while True:

            if self.sessionkey:
                headers = {"Session-Key": self.sessionkey}
                payload = json.dumps({"nickname": self.nick})
                try:
                    r = requests.put(url, data=payload, headers=headers).json()
                except:
                    pass

            time.sleep(1)

    def loopcolors(self):

        colors = ["FF00FF", "FF0000", "00FF00", "00BBFF", "FF7F00",
                  "FF033E", "FFFF00", "66FF00", "FF007F", "007CC5"]

        url = f"https://api-us-1.sendbird.com/v3/users/{bot.me}/metadata"

        while True:

            if self.sessionkey:
                headers = {"Session-Key": self.sessionkey}
                payload = json.dumps({"metadata": {"nick_color": color}})
                try:
                    r = requests.put(url, data=payload, headers=headers).json()
                except:
                    pass

            time.sleep(10)

    # this should only be run as a thread
    def check_subscribers(self):

        header = {"Authorization": "Basic " + self.basicauth}

        while True:

            cursor = ""
            has_next = True
            subscribers = UserList()

            while has_next:

                url = f"{self.ifunny_host}/users/{self.me.id}/subscribers?limit=100000&next={cursor}"
                try:
                    data = requests.get(url, headers=header).json()
                except:
                    continue

                if "error" not in data:

                    has_next = data["data"]["users"]["paging"]["hasNext"]
                    cursor = data["data"]["users"]["paging"]["cursors"]["next"]

                    for i in data["data"]["users"]["items"]:
                        subscribers.append(User(i["original_nick"], i["id"], data=i))

            self.subscribers = subscribers
            time.sleep(10)

    def get_channel_data(self, channel):

        header = {"Session-Key": self.sessionkey}
        url = f"{self.sendbird_host}/group_channels/{channel.url}"
        r = requests.get(url, headers=header).json()

        if "error" not in r:
            data = json.loads(r["data"])
            return data

        return {}

    def get_admins(self, channel):

        if channel.type != "chat":
            channel_data = self.get_channel_data(channel)

            if not channel_data or isinstance(channel_data, list) or not channel_data.get("chatInfo"):
                channel_data = {}
                channel_data["chatInfo"]["adminsIdList"] = []

            admins = channel_data["chatInfo"]["adminsIdList"]

        admins = UserList([User("", i) for i in admins])

        return admins

    def set_admins(self, channel):

        channel_data = self.get_channel_data(channel)

        if channel_data:
            channel_data["chatInfo"]["adminsIdList"] = channel.admins.ids()
            self.set_channel_data(channel, channel_data)
            return False

        return channel_data

    def set_channel_data(self, channel, data: dict):

        url = f"{self.sendbird_host}/group_channels/{channel.url}"
        header = {"Session-Key": self.sessionkey}
        payload = {"data": json.dumps(data)}

        channel_data = requests.put(url, data=json.dumps(payload), headers=header).json()


    def kick(self, other_id, channel):
        payload = {"users": other_id}
        header = {"Authorization": "Bearer " + self.bearer}
        url = f"{self.ifunny_host}/chats/{channel}/kicked_users"
        r = requests.put(url, data=payload, headers=header).json()

        if "error" in r:
            return r
        return False

    def invite(self, other_id, channel):
        url = f"{self.sendbird_host}/group_channels/{channel}/invite"
        payload = {"app_id": "AFB3A55B-8275-4C1E-AEA8-309842798187", "user_ids": [other_id]}
        headers = {"Session-Key": self.sessionkey}
        r = requests.post(url, data=json.dumps(payload), headers=headers).json()

        if "error" in r:
            return r["message"]
        return False

    def join(self, channel):
        headers = {"Session-Key": self.sessionkey}
        url = f"{self.sendbird_host}/group_channels/{channel}/accept"
        payload = {"app_id": "AFB3A55B-8275-4C1E-AEA8-309842798187"}
        r = requests.put(url, data=json.dumps(payload), headers=headers).json()

        if "error" in r:
            return r["message"]
        return False

    def list_members(self, channel):

        payload = {"app_id": "AFB3A55B-8275-4C1E-AEA8-309842798187"}
        headers = {"Session-Key": self.sessionkey}

        members = UserList()
        next_token = ""
        init = True

        while next_token or init:

            init = False
            url = f"{self.sendbird_host}/group_channels/{channel.url}/members?limit=100&token={next_token}&member_state_filter=joined_only"
            data = requests.get(url, data=json.dumps(payload), headers=headers).json()
            next_token = data["next"]

            for i in data["members"]:
                members.append(Frame.parse_user(i))

        return members

    def list_channels(self, sort="latest_last_message"):

        channels = ChannelList()

        headers = {"Session-Key": self.sessionkey}
        next_token = ""
        init = True

        while next_token or init:

            init = False
            url = f"{self.sendbird_host}/group_channels?limit=100&order={sort}&token={next_token}"
            data = requests.get(url, headers=headers).json()
            next_token = data["next"]

            for i in data["channels"]:
                channels.append(Channel(i["channel"], self))

        return channels
