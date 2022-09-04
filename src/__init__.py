import time, threading, datetime, re

from typing import List

from enum import Enum

from telegram_api import *

class HandlerType(Enum):
	COMMAND = 1
	NORMAL_MESSAGE = 2
	CALLBACK_QUERY = 3
	IGNORED_CALLBACK_QUERY = 4
	IGNORED_MESSAGE = 5

class ParseMode:
	HTML = "HTML"
	MARKDOWN = "Markdown"
	MARKDOWN_V2 = "MarkdownV2"
	NORMAL = None

class TimeoutError(TeleasyError):
	pass

class StopEvent(TeleasyError):
	pass

class TeleasyUtils:

	@staticmethod
	def is_command(text: str) -> bool:
		return bool(re.match(r"^\/[a-zA-Z0-9_]+", text))

	@staticmethod
	def parse_args(arg_str: str) -> List[str]:
		arg_list = list()
		temp_arg = str()
		arg_str = arg_str.strip()
		in_quot = {q: False for q in "\"'`“”"}
		for char in arg_str:
			if char in in_quot and not any([in_quot[k] for k in in_quot.keys() if k != char]):
				in_quot[char] = not in_quot[char]
			elif char == " " and not any(in_quot.values()):
				if temp_arg != "":
					arg_list.append(temp_arg)
					temp_arg = str()
			else:
				temp_arg += char
		if temp_arg:
			arg_list.append(temp_arg)
		if not arg_list:
			return list()
		return arg_list[1:]

	@staticmethod
	def make_easy_inlinekeyboard(buttons: List[List[str]], num_rows: int=1, callbacks: List[str]=None) -> InlineKeyboardMarkup:
		keyboard_list = list()
		temp_list = list()
		for i, button in enumerate(buttons):
			if len(temp_list) == num_rows:
				keyboard_list.append(temp_list)
				temp_list = list()
			temp_list.append(InlineKeyboardButton.make(text=button, callback_data=button if callbacks is None else callbacks[i]))
		if temp_list:
			keyboard_list.append(temp_list)
		keyboard = InlineKeyboardMarkup.make(keyboard_list)
		return keyboard
	
	@staticmethod
	def make_easy_keyboard(buttons: List[List[str]], num_rows: int=1) -> ReplyKeyboardMarkup:
		keyboard_list = list()
		temp_list = list()
		for button in buttons:
			if len(temp_list) == num_rows:
				keyboard_list.append(temp_list)
				temp_list = list()
			temp_list.append(KeyboardButton.make(text=button))
		if temp_list:
			keyboard_list.append(temp_list)
		keyboard = ReplyKeyboardMarkup.make(keyboard_list, one_time_keyboard=True)
		return keyboard

class ChatInstance:

	def __init__(self):
		self.raw: dict = None
		self.update_id: int = None
		self.message: Message = None
		self.callback: CallbackQuery = None
		self.bot: TelegramBot = None
		self.chat: Chat = None
		self.timeout_config = {
			"time": None,
			"callback": None
		}
		self._on_error = None

		# Attributes inherited from Chat (TelegramApiObject)

		self.type: str = None

		self.title: str = None
		self.username: str = None
		self.first_name: str = None
		self.last_name: str = None

	@property
	def id(self) -> int:
		return self.chat.id

	def on_timeout(self, timeout_seconds: int):
		def inner(func):
			self.timeout_config["time"] = timeout_seconds
			self.timeout_config["callback"] = func
		return inner

	def on_error(self, func):
		self._on_error = func

	def wait(self, seconds: float):
		"""same functionality as time.sleep(*args)"""
		time.sleep(seconds)

	def select(self, text: str, options: List[str], columns:int=1, callbacks: List[str]=None, disappering_buttons=True) -> str:
		keyboard = TeleasyUtils.make_easy_inlinekeyboard(options, columns, callbacks)
		message = self.bot.send_message(self.chat, text, reply_markup=keyboard)
		try:
			callback = self.bot.await_callback(self).data
			raise StopEvent
		except StopEvent:
			if disappering_buttons:
				message.edit_reply_keyboard(None)
		return callback

	def input_keyboard(self, text: str, options: List[str], columns:int=1) -> Message:
		keyboard = TeleasyUtils.make_easy_keyboard(options, columns)
		self.bot.send_message(self.chat, text, reply_markup=keyboard)
		return self.bot.await_answer(self, None)

	def reply_to(self, message: Message, text: str, editable=False, **kwargs) -> Message:
		pass

	def reply(self, text: str, editable=False, **kwargs) -> Message:
		pass

	def print(self, text: str, editable=False, **kwargs) -> Message:
		pass

	def write(self, text: str, editable=False, **kwargs) -> Message:
		pass

	def input(self, text: str, **kwargs) -> Message:
		pass

	@property
	def arguments(self) -> List[str]:
		return TeleasyUtils.parse_args(self.message.text)

class Handler:

	def __init__(self, handler_type: str, func, command=None):
		self.func = func
		self.type: int = handler_type

		# optional
		self.command: str = command

	def run(self, chat_instance: ChatInstance, bot: "TelegramBot", *args) -> threading.Thread:
		def threaded_handler_func(chat_instance):
			try:
				if chat_instance == None:
					self.func(None, *args)
					raise StopEvent()
				
				bot.activate_chat(chat_instance.chat.id)
				return_val = self.func(chat_instance, *args)
				if isinstance(return_val, str) and chat_instance._update.has(Message) and return_val:
					bot.send_message(chat_instance.chat, str(return_val))
				raise StopEvent()
			except StopEvent:
				if chat_instance != None:
					bot.deactivate_chat(chat_instance.chat.id)
			except Exception as error:
				if chat_instance != None:
					if chat_instance._on_error:
						bot._run_handler_func(chat_instance._on_error, chat_instance, error)
					elif bot.global_error_handler:
						bot._run_handler_func(bot.global_error_handler, chat_instance, error)
					else:
						raise
				elif bot.global_error_handler:
					bot._run_handler_func(bot.global_error_handler, chat_instance, error)
				else:
					raise error
		new_thread = threading.Thread(target=threaded_handler_func, args=(chat_instance,))
		new_thread.start()
		return new_thread

	def __getitem__(self, key: str) -> any:
		return self.__dict__[key]

class TeleasyBotConfig:

	def __init__(self):
		self.parse_mode: str = None
		self.ignore_command_case: bool = True
		self.console_logging: bool = False
		self.logging_prefix: str = "[TELEGRAM-BOT]"
		self.logging_time_format: str = "[%d/%m/%Y, %H:%M:%S]"

	def set_logging_prefix(self, new_prefix: str) -> None:
		"""default value is \"[TELEGRAM-BOT]\""""
		self.logging_prefix = new_prefix

	def set_logging_time_format(self, new_format: str) -> None:
		"""default value is \"[%m/%d/%Y, %H:%M:%S]\""""
		self.logging_time_format = new_format

	def enable_console_logging(self, new_val=True) -> None:
		"""may be disabled by passing False as argument"""
		self.console_logging = new_val

	def set_parse_mode(self, parse_mode: ParseMode) -> None:
		"""see https://core.telegram.org/bots/api#formatting-options"""
		self.parse_mode = parse_mode

class HandlerException(TeleasyError):
	pass

class HandlerList:

	def __init__(self):
		self.handlers = list()

	def add(self, handler: Handler) -> None:
		if self.contains(handler.type) and handler.type != HandlerType.COMMAND:
			raise HandlerException(f"Handler for type {handler.type} already registered")
		self.handlers.append(handler)

	def get(self, attr_val: any, attr_name="type", ignore_case: bool=True) -> Handler or None:
		if ignore_case:
			for handler in self.handlers:
				if handler[attr_name] == None:
					continue
				if str(handler[attr_name]).lower() == str(attr_val).lower():
					return handler
			return None
		else:
			for handler in self.handlers:
				if handler[attr_name] == attr_val:
					return handler
			return None

	def get_by_command(self, command: str, ignore_case: bool=True) -> Handler or None:
		return self.get(command, "command", ignore_case)

	def contains_command(self, command: str, ignore_case: bool=True) -> bool:
		if ignore_case:
			for handler in self.handlers:
				if handler.command == None:
					continue
				if str(handler.command).lower() == str(command).lower():
					return True
			return False
		else:
			for handler in self.handlers:
				if handler.command == command:
					return True
			return False

	def contains(self, handler_type: int) -> bool:
		for handler in self.handlers:
			if handler.type == handler_type:
				return True
		return False

class TelegramBot:

	def __init__(self, token):
		self.config = TeleasyBotConfig()
		self.api = TelegramAPI(token)
		self.handlers = HandlerList()
		self.awaiting_answers = dict()
		self.awaiting_callbacks = dict()
		self.running = True
		self.global_error_handler = None
		self.global_timeout_time = None
		self.global_timeout_handler = None
		self.global_unknown_command_handler = None
		self.active_chats: List[int] = list()

	def activate_chat(self, chat_id: int) -> None:
		if not chat_id in self.active_chats:
			self.active_chats.append(chat_id)

	def deactivate_chat(self, chat_id: int) -> None:
		if chat_id in self.active_chats:
			self.active_chats.remove(chat_id)

	def on_error(self, func):
		self.global_error_handler = func

	def on_timeout(self, timeout_seconds: int):
		def inner(func):
			self.global_timeout_time = timeout_seconds
			self.global_timeout_handler = func
		return inner

	def on_unknown_command(self, func):
		self.global_unknown_command_handler = func

	def on_normal_message(self, func):
		self.handlers.add(Handler(HandlerType.NORMAL_MESSAGE, func))

	def on_ignored_message(self, func):
		self.handlers.add(Handler(HandlerType.IGNORED_MESSAGE, func))

	def on_ignored_callback_query(self, func):
		self.handlers.add(Handler(HandlerType.IGNORED_CALLBACK_QUERY, func))

	def on_command(self, command: str):
		if command.startswith("/"): command = command[1:]
		return lambda func: self.handlers.add(Handler(HandlerType.COMMAND, func, command))

	def on_callback_query(self, func):
		self.handlers.add(Handler(HandlerType.CALLBACK_QUERY, func))

	def add_handler(self, handler_type: int, func, command=None) -> None:
		new_handler = Handler(handler_type, func, command=command)
		self.handlers.add(new_handler)

	def set_command(self, command: str, func) -> None:
		self.add_handler(HandlerType.COMMAND, func, command=command)

	def set_normal(self, func) -> None:
		self.add_handler(HandlerType.NORMAL_MESSAGE, func)

	def add_handler(self, handler_type: int, func, command:str=None) -> None:
		new_handler = Handler(handler_type, func, command=command)
		self.handlers.add(new_handler)

	def log(self, message, force_print=False) -> None:
		if not self.config.console_logging and not force_print:
			return

		time_str = datetime.datetime.now().strftime(self.config.logging_time_format)
		print(f"{self.config.logging_prefix} {time_str} {message}")

	def logerror(self, message, force_print=False) -> None:
		self.log(f"[ERROR] {message}", force_print)

	def reply_to(self, reply_message: Message, text: str, **kwargs) -> Message:
		return self.send_message(
			chat=reply_message.chat,
			text=text, reply_to_message_id=reply_message.get_id(), **kwargs
		)

	def _run_handler_func(self, func, chat_instance: ChatInstance, *args):
		handler = Handler(HandlerType.NORMAL_MESSAGE, func)
		handler.run(chat_instance, self, *args)

	def update_command_list(self, exceptions=[]):
		hs = [h for h in self.handlers.handlers if h.command and h.command not in exceptions]
		self.api.set_my_commands([
			BotCommand.make(h.command, h.func.__doc__ if h.func.__doc__ else h.command.capitalize())._export() for h in hs
		])
		self.log("Synchronized Command List with Telegram Server")

	def send_message(self, chat: Chat, text: str, editable=False, force_reply=False, placeholder=None, **kwargs) -> Message:
		if not kwargs and not editable and not force_reply: kwargs["reply_markup"] = ReplyKeyboardRemove.make()
		if force_reply: kwargs["reply_markup"] = ForceReply.make(None, placeholder if placeholder else None)
		msg = self.api.send_message(chat_id=chat.id, text=str(text), parse_mode=self.config.parse_mode, **kwargs)
		msg._bot_ref = self
		self.log(f"Sent Message to Chat#{chat.id}")
		return msg

	def await_answer(self, chat_instance: ChatInstance, text: str, placeholder=None, **kwargs) -> Message:
		if text: self.send_message(chat_instance.chat, text, force_reply=True, placeholder=placeholder, **kwargs)
		self.awaiting_answers[chat_instance.chat.id] = None
		start_time = time.time()
		while self.awaiting_answers[chat_instance.chat.id] == None:
			time.sleep(0.2)
			if chat_instance.timeout_config["time"] and time.time() - start_time > chat_instance.timeout_config["time"]:
				self._run_handler_func(chat_instance.timeout_config["callback"], chat_instance)
				del self.awaiting_answers[chat_instance.chat.id]
				raise StopEvent()
			elif self.global_timeout_time and time.time() - start_time > self.global_timeout_time:
				self._run_handler_func(self.global_timeout_handler, chat_instance)
				del self.awaiting_answers[chat_instance.chat.id]
				raise StopEvent()
		result = self.awaiting_answers[chat_instance.chat.id]
		del self.awaiting_answers[chat_instance.chat.id]
		return result

	def await_callback(self, chat_instance: ChatInstance) -> CallbackQuery:
		self.awaiting_callbacks[chat_instance.chat.id] = None
		start_time = time.time()
		while self.awaiting_callbacks[chat_instance.chat.id] == None:
			time.sleep(0.1)
			if chat_instance.timeout_config["time"] and time.time() - start_time > chat_instance.timeout_config["time"]:
				self._run_handler_func(chat_instance.timeout_config["callback"], chat_instance)
				del self.awaiting_callbacks[chat_instance.chat.id]
				raise StopEvent()
			elif self.global_timeout_time and time.time() - start_time > self.global_timeout_time:
				self._run_handler_func(self.global_timeout_handler, chat_instance)
				del self.awaiting_callbacks[chat_instance.chat.id]
				raise StopEvent()
		result = self.awaiting_callbacks[chat_instance.chat.id]
		del self.awaiting_callbacks[chat_instance.chat.id]
		return result

	def make_chat_instance(self, update: Update) -> ChatInstance:
		chat_instance = ChatInstance()
		chat_instance.bot = self
		chat_instance.api = self.api
		chat_instance._update = update
		if update.has(Message):
			chat_instance.chat = update.message.chat
			chat_instance.reply_to = self.reply_to
			chat_instance.reply = lambda text, **kwargs: self.reply_to(update.message, text, **kwargs)
			chat_instance.print = lambda text, **kwargs: self.send_message(update.message.chat, text, **kwargs)
			chat_instance.write = lambda text, **kwargs: self.send_message(update.message.chat, text, **kwargs)
			chat_instance.input = lambda text=None, **kwargs: self.await_answer(chat_instance, text, **kwargs)
		if update.has(CallbackQuery):
			chat_instance.chat = update.callback_query.message.chat
			chat_instance.callback = update.callback_query
		for key, value in chat_instance.chat.__dict__.items():
			chat_instance.__dict__[key] = value
		return chat_instance

	def process_message_update(self, update: Update):
		message = update.message
		chat_instance = self.make_chat_instance(update)
		if message.chat.id in self.awaiting_answers.keys():
			self.log(f"Received Answer in Chat#{chat_instance.chat.id}")
			self.awaiting_answers[message.chat.id] = message
		elif chat_instance.chat.id in self.active_chats:
			if self.handlers.contains(HandlerType.IGNORED_MESSAGE):
				self.log(f"Received Message in active Chat#{chat_instance.chat.id}")
				self.handlers.get(HandlerType.IGNORED_MESSAGE).run(chat_instance, self)
			else:
				self.log(f"Ignoring Message in active Chat#{chat_instance.chat.id}")
		elif message.is_command() and self.handlers.contains_command(message.extract_command(),
		ignore_case=self.config.ignore_command_case):
			self.log(f"Received Command in Chat#{chat_instance.chat.id}")
			self.handlers.get_by_command(message.extract_command(),
				ignore_case=self.config.ignore_command_case).run(chat_instance, self)
		elif message.is_command() and self.global_unknown_command_handler:
			self.log(f"Received Unknown Command in Chat#{chat_instance.chat.id}")
			self._run_handler_func(self.global_unknown_command_handler, chat_instance, message.extract_command())
		elif self.handlers.contains(HandlerType.NORMAL_MESSAGE):
			self.log(f"Received Message in Chat#{chat_instance.chat.id}")
			self.handlers.get(HandlerType.NORMAL_MESSAGE).run(chat_instance, self)

	def process_callback_query_update(self, update: Update):
		chat_instance = self.make_chat_instance(update)
		if chat_instance.chat.id in self.awaiting_callbacks.keys():
			self.log(f"Received Callback-Query Answer in Chat#{chat_instance.chat.id}")
			self.awaiting_callbacks[chat_instance.chat.id] = update.callback_query
		elif chat_instance.chat.id in self.active_chats:
			if self.handlers.contains(HandlerType.IGNORED_CALLBACK_QUERY):
				self.log(f"Received Callback-Query in active Chat#{chat_instance.chat.id}")
				self.handlers.get(HandlerType.IGNORED_CALLBACK_QUERY).run(chat_instance, self)
			else:
				self.log(f"Ignoring Callback-Query in active Chat#{chat_instance.chat.id}")
		elif self.handlers.contains(HandlerType.CALLBACK_QUERY):
			self.log(f"Received Callback-Query in Chat#{chat_instance.chat.id}")
			self.handlers.get(HandlerType.CALLBACK_QUERY).run(chat_instance, self)
		self.api.answer_callback_query(update.callback_query.id)

	def update(self) -> None:
		updates = self.api.getUpdates()
		for update in updates:
			if update.has(Message):
				self.process_message_update(update)
			elif update.has(CallbackQuery):
				self.process_callback_query_update(update)

	def log_feedback(self) -> None:
		"""print some feedback on your current configuration"""
		feedbacks_given = 0
		test_cases = [
			[not self.handlers.contains(HandlerType.NORMAL_MESSAGE),
				"You haven't registered a normal-message handler"],
			[not self.handlers.contains(HandlerType.COMMAND),
				"You haven't registered any commands"],
			[not self.handlers.contains(HandlerType.CALLBACK_QUERY),
				"You haven't registered a callback-query handler"],
			[not self.handlers.contains(HandlerType.IGNORED_MESSAGE),
				"You haven't registered an ignored-message handler"],
			[not self.handlers.contains(HandlerType.IGNORED_CALLBACK_QUERY),
				"You haven't registered an ignored-callback-query handler"],
			[not self.global_unknown_command_handler,
				"You haven't registered an uknown-command handler"],
			[not self.global_error_handler,
				"You haven't registered a global error handler"],
			[not self.global_timeout_handler and self.global_timeout_time != None,
				"You have set a global timeout-time but not a global timeout handler"],
			[not self.handlers.contains_command("start"),
				"You haven't registered a /start command handler"]
		]
		for case, message in test_cases:
			if not case:
				continue
			self.log(f"[FEEDBACK] {message}", True)
			feedbacks_given += 1
		if feedbacks_given == 0:
			self.log(f"[FEEDBACK] Everything seems good!")

	def start(self, interval=0.0) -> None:
		self.log("Started Polling Process")
		while self.running:
			try:
				self.update()
			except Exception as e:
				if self.global_error_handler:
					self._run_handler_func(self.global_error_handler, None, e)
				else:
					self.logerror(f"during polling: {e}")
				time.sleep(1.)
			if interval > 0:
				time.sleep(interval)
		self.log("Stopped Polling Process")
