import json, requests, copy, time
from typing import Optional, List

class ApiObject:

	def _get_array_of(self, O: any, parameter_name: str) -> None:
		self.__dict__[parameter_name] = list()
		if parameter_name in self.raw:
			for param in self.raw[parameter_name]:
				new_obj = O(param)
				self.__dict__[parameter_name].append(new_obj)

	def _get_optional(self, O: any, parameter_name: str) -> any:
		return O(self.raw[parameter_name]) if parameter_name in self.raw else None
		
	def _get_optional_bool(self, parameter_name) -> bool:
		return bool(parameter_name in self.raw)

	def to_dict(self, add_none=False) -> dict:
		out_dict = copy.deepcopy(self.__dict__)
		for key, val in out_dict.items():
			if isinstance(val, ApiObject):
				out_dict[key] = val.to_dict(add_none)
			if isinstance(val, list):
				temp_list = list()
				for sub_val in val:
					if isinstance(sub_val, ApiObject):
						temp_list.append(sub_val.to_dict(add_none))
					elif isinstance(sub_val, list):
						temp_temp_list = list()
						for sub_sub_val in sub_val:
							if isinstance(sub_sub_val, ApiObject):
								temp_temp_list.append(sub_sub_val.to_dict(add_none))
							else:
								temp_temp_list.append(sub_sub_val)
						temp_list.append(temp_temp_list)
					else:
						temp_list.append(sub_val)
				out_dict[key] = temp_list
		return {k if k != "from_" else "from": v for k, v in out_dict.items()
												 if (v != None or add_none) and not k in ["raw", "self", "__bot_ref"]}

	def __str__(self) -> str:
		temp_out = f"<teleasy.{type(self).__name__}"
		id = self.get_id()
		if id:
			return f"{temp_out}#{id}>"
		return f"{temp_out}>"

	def __getitem__(self, key, soft=False, replacement=None) -> any:
		if key == "from": key = "from_"
		if key in self.__dict__:
			return self.__dict__[key]
		if soft: return replacement
		raise AttributeError(f"{type(self).__name__} has no '{key}' attribute")

	def has_type(self, search_type: type) -> bool:
		for key, val in self.__dict__.items():
			if isinstance(val, search_type):
				return True
		return False

	def has(self, key: type or str, strict=False) -> bool:
		if type(key) == type: return self.has_type(key)
		has_out = bool((key if key != "from_" or strict else "from") in self.__dict__)
		if has_out is True: return self.__dict__[key] != None
		return False

	@classmethod
	def make(cls, **kwargs) -> "ApiObject":
		return cls(kwargs)

	def get(self, key, replacement=None) -> any:
		return self.__getitem__(key, True, replacement)

	def get_id(self) -> int or str or None:
		for key, val in self.__dict__.items():
			if key.endswith("id"):
				return val
		return None

	def _export(self) -> dict:
		return self.to_dict()

class LoginUrl(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

class User(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.id: int = data["id"]
		self.first_name: str = data["first_name"]

		# optional parameters
		self.is_bot: bool = self._get_optional(bool, "is_bot")
		self.last_name: str = data.get("last_name")
		self.username: str = data.get("username")
		self.language_code: str = data.get("language_code") # https://en.wikipedia.org/wiki/IETF_language_tag

		# returned only in getMe (https://core.telegram.org/bots/api#getme)
		self.can_join_groups: bool = self._get_optional(bool, "can_join_groups")
		self.can_read_all_group_messages = self._get_optional(bool, "can_read_all_group_messages")
		self.supports_inline_queries = self._get_optional(bool, "supports_inline_queries")

class ChatPhoto(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.small_file_id: str = data.get("small_file_id")
		self.small_file_unique_id: str = data.get("small_file_unique_id")
		self.big_file_id: str = data.get("big_file_id")
		self.big_file_unique_id: str = data.get("big_file_unique_id")

class ChatPermissions(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.can_change_info: bool = data.get("can_change_info")
		self.can_pin_messages: bool = data.get("can_pin_messages")
		self.can_invite_users: bool = data.get("can_invite_users")
		self.can_send_messages: bool = data.get("can_send_messages")
		self.can_send_media_messages: bool = data.get("can_send_media_messages")
		self.can_add_web_page_previews: bool = data.get("can_add_web_page_previews")
		self.can_send_polls: bool = data.get("can_send_polls")
		self.can_send_other_messages: bool = data.get("can_send_other_messages")

class ChatInviteLink(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.invite_link: str = data.get("invite_link")
		self.creator: User = User(data.get("creator"))
		self.creates_join_request: bool = data.get("creates_join_request")
		self.is_primary: bool = data.get("is_primary")
		self.is_revoked: bool = data.get("is_revoked")

		# optional parameters
		self.name: str = data.get("name")
		self.expire_date: int = data.get("expire_date")
		self.member_limit: int = data.get("member_limit")
		self.pending_join_request_count: int = data.get("pending_join_request_count")

class ChatMember(ApiObject):
	
	@staticmethod
	def get_type(data) -> type:
		statuses = {
			"member": ChatMemberMember,
			"administrator": ChatMemberAdministrator,
			"restricted": ChatMemberRestricted,
			"owner": ChatMemberOwner,
			"left": ChatMemberLeft,
			"banned": ChatMemberBanned
		}
		return statuses[data["status"]]

class ChatMemberOwner(ChatMember):

	def __init__(self, data):
		self.raw: dict = data

		self.status: str = data.get("status")
		self.user: User = User(data.get("user"))
		self.is_anonymous: bool = data.get("is_anonymous")
		self.custom_title: str = data.get("custom_title")

class ChatMemberMember(ChatMember):

	def __init__(self, data):
		self.raw: dict = data
		
		self.status: str = data.get("status") # always "member"
		self.user: User = User(data.get("user"))

class ChatMemberLeft(ChatMember):

	def __init__(self, data):
		self.raw: dict = data

		self.status: str = data.get("status") # always "left"
		self.user: User = User(data.get("user"))

class ChatMemberBanned(ChatMember):

	def __init__(self, data):
		self.raw: dict = data

		self.status: str = data.get("status") # always "banned"
		self.user: User = User(data.get("user"))

		self.until_date: int = data.get("until_date")

class ChatMemberUpdated(ChatMember):

	def __init__(self, data):
		self.raw: dict = data

		self.chat: Chat = Chat(data.get("chat"))
		self.from_: User = User(data.get("from"))
		self.date: int = data.get("date")
		old_type = ChatMember.get_type(data["old_chat_member"])
		new_type = ChatMember.get_type(data["new_chat_member"])
		self.old_chat_member: ChatMember = old_type(data["old_chat_member"])
		self.new_chat_member: ChatMember = new_type(data["new_chat_member"])

		# optional parameters
		self.invite_link: ChatInviteLink = self._get_optional(ChatInviteLink, "invite_link")

class ChatJoinRequest(ChatMember):

	def __init__(self, data):
		self.raw: dict = data

		self.chat: Chat = Chat(data.get("chat"))
		self.from_: User = User(data.get("from"))
		self.date: int = data.get("date")
		
		# optional parameters
		self.bio: str = data.get("bio")
		self.invite_link: ChatInviteLink = self._get_optional(ChatInviteLink, "invite_link")

class ChatMemberRestricted(ChatMember):

	def __init__(self, data):
		self.raw: dict = data
		
		self.status: str = data.get("status") # always "restricted"
		self.user: User = User(data.get("user"))
		self.is_member: bool = data.get("is_member")
		self.can_change_info: bool = data.get("can_change_info")
		self.can_pin_messages: bool = data.get("can_pin_messages")
		self.can_send_messages: bool = data.get("can_send_messages")
		self.can_send_media_messages: bool = data.get("can_send_media_messages")
		self.can_send_polls: bool = data.get("can_send_polls")
		self.can_send_other_messages: bool = data.get("can_send_other_messages")
		self.can_add_web_page_previews: bool = data.get("can_add_web_page_previews")
		self.until_date: int = data.get("until_date")

class ChatMemberAdministrator(ChatMember):
	
	def __init__(self, data):
		self.raw: dict = data

		self.status: str = data.get("status") # always "administrator"
		self.user: User = User(data.get("user"))
		self.can_be_edited: bool = data.get("can_be_edited")
		self.is_anonymous: bool = data.get("is_anonymous")
		self.can_manage_chat: bool = data.get("can_manage_chat")
		self.can_delete_messages: bool = data.get("can_delete_messages")
		self.can_manage_voice_chats: bool = data.get("can_manage_voice_chats")
		self.can_restrict_members: bool = data.get("can_restrict_members")
		self.can_promote_members: bool = data.get("can_promote_members")
		self.can_change_info: bool = data.get("can_change_info")
		self.can_invite_users: bool = data.get("can_invite_users")
		self.can_post_messages: bool = self._get_optional(bool, "can_post_messages")
		self.can_edit_messages: bool = self._get_optional(bool, "can_edit_messages")
		self.can_pin_messages: bool = self._get_optional(bool, "can_pin_messages")
		self.custom_title: str = data.get("custom_title")

class ChatLocation(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.location: Location = Location(data.get("location"))
		self.address: str = data.get("address")

class BotCommand(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.command: str = data.get("command")
		self.description: str = data.get("description")

	@staticmethod
	def make(command: str, description: str) -> "BotCommand":
		return BotCommand({"command": command, "description": description})

class BotCommandScope(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.type: str = data.get("type")
		self.chat_id: int = data.get("chat_id")
		self.user_id: int = data.get("user_id")

class Chat(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.id: int = data["id"]
		self.type: str = data["type"]
		
		# optional parameters
		self.title: str = data.get("title")
		self.username: str = data.get("username")
		self.first_name: str = data.get("first_name")
		self.last_name: str = data.get("last_name")

		# only returned in getChat (https://core.telegram.org/bots/api#getchat)
		self.photo: ChatPhoto = self._get_optional(ChatPhoto, "photo")
		self.bio: str = data.get("bio")
		self.description: str = data.get("description")
		self.invite_link: str = data.get("invite_link")
		self.pinned_message: Message = self._get_optional(Message, "pinned_message")
		self.permissions: ChatPermissions = self._get_optional(ChatPermissions, "permissions")
		self.slow_mode_delay: int = data.get("slow_mode_delay")
		self.message_auto_delete_time: int = data.get("message_auto_delete_time")
		self.sticker_set_name: str = data.get("sticker_set_name")
		self.can_set_sticker_set: bool = self._get_optional(bool, "can_set_sticker_set")
		self.linked_chat_id: int = data.get("linked_chat_id")
		self.location: ChatLocation = self._get_optional(ChatLocation, "location")

class MessageEntityType:
	MENTION = "mention"
	HASHTAG = "hashtag"
	CASHTAG = "cashtag"
	BOT_COMMAND = "bot_command"
	URL = "url"
	EMAIL = "email"
	PHONE_NUMBER = "phone_number"
	BOLD = "bold"
	ITALIC = "italic"
	UNDERLINE = "underline"
	STRIKETHROUGH = "strikethrough"
	CODE = "code"
	PRE = "pre"
	TEXT_LINK = "text_link"
	TEXT_MENTION = "text_mention"

class MessageEntity(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.type: str = data["type"]
		self.offset: int = data["offset"]
		self.length: int = data["length"]

		# optional parameters
		self.url: str = data.get("url")
		self.user: User = self._get_optional(User, "user")
		self.language: str = data.get("language")

	def __len__(self):
		return self.length

class Animation(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.file_id: str = data["file_id"]
		self.file_unique_id: str = data["file_unique_id"]
		self.width: int = data["width"]
		self.height: int = data["height"]
		self.duration: int = data["duration"]
		
		# optional parameters
		self.thumb: PhotoSize = self._get_optional(PhotoSize, "thumb")
		self.file_name: str = data.get("file_name")
		self.mime_type: str = data.get("mime_type")
		self.file_size: int = data.get("file_size")

class Audio(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.file_id: str = data["file_id"]
		self.file_unique_id: str = data["file_unique_id"]
		self.duration: int = data["duration"]

		# optional parameters
		self.performer: str = data.get("performer")
		self.title: str = data.get("title")
		self.file_name: str = data.get("file_name")
		self.mime_type: str = data.get("mime_type")
		self.file_size: int = data.get("file_size")
		self.thumb: PhotoSize = self._get_optional(PhotoSize, "thumb")

class Document(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.file_id: str = data["file_id"]
		self.file_unique_id: str = data["file_unique_id"]
		self.duration: int = data["duration"]

		# optional parameters
		self.file_name: str = data.get("file_name")
		self.mime_type: str = data.get("mime_type")
		self.file_size: int = data.get("file_size")
		self.thumb: PhotoSize = self._get_optional(PhotoSize, "thumb")

class PhotoSize(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.file_id: str = data["file_id"]
		self.file_unique_id: str = data["file_unique_id"]
		self.width: int = data["width"]
		self.height: int = data["height"]
		self.file_size: int = data.get("file_size") # in bytes

class Sticker(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

class Video(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.file_id: str = data["file_id"]
		self.file_unique_id: str = data["file_unique_id"]
		self.duration: int = data["duration"]
		self.width: int = data["width"]
		self.height: int = data["height"]

		# optional parameters
		self.file_name: str = data.get("file_name")
		self.mime_type: str = data.get("mime_type")
		self.file_size: int = data.get("file_size")
		self.thumb: PhotoSize = self._get_optional(PhotoSize, "thumb")

class VideoNote(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.file_id: str = data["file_id"]
		self.file_unique_id: str = data["file_unique_id"]
		self.duration: int = data["duration"]
		self.length: int = data["length"]

		# optional parameters
		self.file_size: int = data.get("file_size")
		self.thumb: PhotoSize = self._get_optional(PhotoSize, "thumb")

	def __len__(self):
		return self.length

class Voice(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.file_id: str = data["file_id"]
		self.file_unique_id: str = data["file_unique_id"]
		self.duration: int = data["duration"]

		# optional parameters
		self.mime_type: str = data.get("mime_type")
		self.file_size: int = data.get("file_size")

class Dice(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.emoji: str = data["emoji"]
		self.value: int = data["value"]

class Game(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

class PollType:
	REGULAR = "regular"
	QUIZ = "quiz"

class Poll(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.id: str = data["id"]
		self.question: str = data["question"]
		self.options: list[PollOption] = data["total_voter_count"]
		self.is_closed: bool = data["is_closed"]
		self.is_anonymous: bool = data["is_anonymous"]
		self.type: str = data["type"]
		self.allows_multiple_answers: bool = data["allows_multiple_answers"]

		# optional parameters
		self.correct_option_id: int = data.get("correct_option_id")
		self.explanation: str = data.get("explanation")
		self.explanation_entities: list[MessageEntity] = list()
		self._get_array_of(MessageEntity, "explanation_entities")
		self.open_period: int = data.get("open_period")
		self.close_date: int = data.get("close_date")

class PollOption(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.text: str = data["text"]
		self.voter_count: int = data["voter_count"]

class PollAnswer(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.poll_id: str = data["poll_id"]
		self.user: User = User(data["user"])
		self.option_ids: list[int] = list()
		self._get_array_of(int, "option_ids")

class Venue(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.location: Location = Location(data["location"])
		self.title: str = data["title"]
		self.address: str = data["address"]

		# optional parameters
		self.foursquare_id: str = data.get("foursquare_id")
		self.foursquare_type: str = data.get("foursquare_type")
		self.google_place_id: str = data.get("google_place_id")
		self.google_place_type: str = data.get("google_place_type")

class InputMedia(ApiObject):
	pass

class InputMediaPhoto(InputMedia):

	def __init__(self, data):
		self.raw: dict = data

		self.type = "photo"
		self.media: str = data.get("media")
		self.caption: str = data.get("caption")
		self.parse_mode: str = data.get("parse_mode")
		self.caption_entities: list[MessageEntity] = list()
		self._get_array_of(MessageEntity, "caption_entities")

class InputMediaVideo(InputMedia):

	def __init__(self, data):
		self.raw: dict = data

		self.type = "video"
		self.media: str = data.get("media")
		self.thumb: str = data.get("thumb")
		self.caption: str = data.get("caption")
		self.parse_mode: str = data.get("parse_mode")
		self.caption_entities: list[MessageEntity] = list()
		self._get_array_of(MessageEntity, "caption_entities")
		self.width: int = data.get("width")
		self.height: int = data.get("height")
		self.duration: int = data.get("duration")
		self.supports_streaming: bool = self._get_optional(bool, "supports_streaming")

class InputMediaVideo(InputMedia):

	def __init__(self, data):
		self.raw: dict = data

		self.type = "animation"
		self.media: str = data.get("media")
		self.thumb: str = data.get("thumb")
		self.caption: str = data.get("caption")
		self.parse_mode: str = data.get("parse_mode")
		self.caption_entities: list[MessageEntity] = list()
		self._get_array_of(MessageEntity, "caption_entities")
		self.width: int = data.get("width")
		self.height: int = data.get("height")
		self.duration: int = data.get("duration")

class InputMediaAudio(InputMedia):

	def __init__(self, data):
		self.raw: dict = data

		self.type = "audio"
		self.media: str = data.get("media")
		self.thumb: str = data.get("thumb")
		self.caption: str = data.get("caption")
		self.parse_mode: str = data.get("parse_mode")
		self.caption_entities: list[MessageEntity] = list()
		self._get_array_of(MessageEntity, "caption_entities")
		self.performer: int = data.get("performer")
		self.title: int = data.get("title")
		self.duration: int = data.get("duration")

class InputMediaDocument(InputMedia):

	def __init__(self, data):
		self.raw: dict = data

		self.type = "document"
		self.media: str = data.get("media")
		self.thumb: str = data.get("thumb")
		self.caption: str = data.get("caption")
		self.parse_mode: str = data.get("parse_mode")
		self.caption_entities: list[MessageEntity] = list()
		self._get_array_of(MessageEntity, "caption_entities")
		self.disable_content_type_detection = self._get_optional(bool, "disable_content_type_detection")

class Location(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.longitude: float = data["longitude"]
		self.latitude: float = data["latitude"]

		# optional parameters
		self.horizontal_accuracy: float = data.get("horizontal_accuracy")
		self.live_period: int = data.get("live_period")
		self.heading: int = data.get("heading")
		self.proximity_alert_radius: int = data.get("proximity_alert_radius")

class Contact(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.phone_number: str = data["phone_number"]
		self.first_name: str = data["first_name"]
		
		# optional parameters
		self.last_name: str = data.get("last_name")
		self.user_id: int = data.get("user_id")
		self.vcard: str = data.get("vcard")

class MessageAutoDeleteTimerChanged(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

class Invoice(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

class SuccessfulPayment(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

class PassportData(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

class ProximityAlertTriggered(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.traveler: User = User(data["traveler"])
		self.watcher: User = User(data["watcher"])
		self.distance: int = data["distance"]

class VoiceChatScheduled(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.start_date: int = data["start_date"]

class VoiceChatStarted(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

class VoiceChatEnded(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.duration: int = data["duration"]

class VoiceChatParticipantsInvited(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.users: list[User] = list()
		self._get_array_of(User, "users")

class CallbackGame(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

class InlineKeyboardButton(ApiObject):
	"""https://core.telegram.org/bots/api#inlinekeyboardbutton"""

	def __init__(self, data):
		self.raw: dict = data

		self.text: str = data["text"]
		
		# optional parameters
		self.url: str = data.get("url")
		self.login_url: LoginUrl = self._get_optional(LoginUrl, "login_url")
		self.callback_data: str = data.get("callback_data")
		self.switch_inline_query: str = data.get("switch_inline_query")
		self.switch_inline_query_current_chat: str = data.get("switch_inline_query_current_chat")
		self.callback_game: CallbackGame = self._get_optional(CallbackGame, "callback_game")
		self.pay: bool = self._get_optional(bool, "pay")

	@staticmethod
	def make(text: str, url: Optional[str]=None, login_url: Optional[LoginUrl]=None,
			callback_data: Optional[str]=None, switch_inline_query: Optional[str]=None,
			switch_inline_query_current_chat: Optional[str]=None, callback_game: Optional[CallbackGame]=None,
			pay: Optional[bool]=None):
		self = InlineKeyboardButton({"text": text})
		self.__dict__ = locals()
		return self

class InlineKeyboardMarkup(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.inline_keyboard: list[list[InlineKeyboardButton]] = list()
		for row in data["inline_keyboard"]:
			self.inline_keyboard.append([InlineKeyboardButton(b) for b in row])

	@staticmethod
	def make(buttons: List[List[InlineKeyboardButton]]):
		self = InlineKeyboardMarkup({"inline_keyboard": list()})
		self.inline_keyboard = buttons
		return self

class KeyboardButtonPollType(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		# optional parameters
		self.type: str = data.get("type")

class ReplyKeyboardRemove(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.remove_keyboard = True
		
		# optional parameters
		self.selective = self._get_optional(bool, "selective")

	@staticmethod
	def make(selective:bool=None):
		return ReplyKeyboardRemove({"selective": selective})

class KeyboardButton(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.text: str = data["text"]

		# optional parameters
		self.request_contact: bool = self._get_optional(bool, "request_contact")
		self.request_location: bool = self._get_optional(bool, "request_location")
		self.request_poll: KeyboardButtonPollType = self._get_optional(KeyboardButtonPollType, "request_poll")

	@staticmethod
	def make(text: str, request_contact: Optional[bool]=None, request_location: Optional[bool]=None,
			request_poll: Optional[KeyboardButtonPollType]=None):
		self = KeyboardButton({"text": text})
		self.__dict__ = locals()
		return self

class ReplyKeyboardMarkup(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.keyboard: list[list[KeyboardButton]] = list()
		for button_row in data["keyboard"]:
			self.keyboard.append([KeyboardButton(b) for b in button_row])
		
		# optional parameters
		self.resize_keyboard: bool = self._get_optional(bool, "resize_keyboard")
		self.one_time_keyboard: bool = self._get_optional(bool, "one_time_keyboard")
		self.input_field_placeholder: str = data.get("input_field_placeholder")
		self.selective: bool = self._get_optional(bool, "selective")

	@staticmethod
	def make(keyboard: List[List[KeyboardButton]], resize_keyboard: Optional[bool]=None,
			one_time_keyboard: Optional[bool]=None, input_field_placeholder: Optional[str]=None,
			selective: Optional[bool]=None):
		self = ReplyKeyboardMarkup({"keyboard": list()})
		self.__dict__ = locals()
		return self

class CallbackQuery(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.id: str = data["id"]
		self.from_: User = User(data["from"])
		self.chat_instance: str = data.get("chat_instance")

		# optional parameters
		self.message: Message = self._get_optional(Message, "message")
		self.inline_message_id: str = data.get("inline_message_id")
		self.data: str = data.get("data")
		self.game_short_name: str = data.get("game_short_name")

class ForceReply(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.force_reply = True
		
		# optional parameters
		self.input_field_placeholder: str = data.get("input_field_placeholder")
		self.selective: bool = self._get_optional(bool, "selective")

	@staticmethod
	def make(selective:bool=None, input_field_placeholder: Optional[str]=None):
		return ForceReply({"selective": selective, "input_field_placeholder": input_field_placeholder})

class File(ApiObject):
	"""https://core.telegram.org/bots/api#file"""

	def __init__(self, data):
		self.raw: dict = data

		self.file_id: str = data["file_id"]
		self.file_unique_id: str = data["file_unique_id"]
		
		# optional parameters
		self.file_path: str = data.get("file_path")
		self.file_size: int = data.get("file_size")

		# short parameters
		# self.id: str = self.file_id
		# self.unique_id: str = self.file_unique_id
		# self.path: str = self.file_path
		# self.size: int = self.file_size

class UserProfilePhotos(ApiObject):

	def __init__(self, data):
		self.raw: dict = data

		self.total_count: int = data["total_count"]
		self.photos: list[list[PhotoSize]] = list()
		
		for photo in data["photos"]:
			photosize_list: list[PhotoSize] = list()
			for photosize in photo:
				photosize_list.append(PhotoSize(photosize))
			self.photos.append(photosize_list)

class TeleasyError(Exception):
	pass

class TelegramAPIError(TeleasyError):
	pass

class MessageEditError(TeleasyError):
	pass

class MessageDeleteError(TeleasyError):
	pass

class Message(ApiObject):
	"""https://core.telegram.org/bots/api#message"""

	def __init__(self, data):
		self.raw: dict = data

		self.message_id: int = data["message_id"]
		self.date: int = data["date"]
		self.chat: Chat = Chat(data["chat"])

		self._bot_ref = None

		# optional parameters
		self.from_: User = self._get_optional(User, "from")
		self.sender_chat: Chat = self._get_optional(Chat, "sender_chat")
		self.forward_from: User = self._get_optional(User, "forward_from")
		self.forward_from_chat: Chat = self._get_optional(Chat, "forward_from_chat")
		self.forward_from_chat_id: int = data.get("forward_from_chat_id")
		self.forward_signature: str = data.get("forward_signature")
		self.forward_sender_name: str = data.get("forward_sender_name")
		self.forward_date: int = data.get("forward_date")
		self.reply_to_message: Message = self._get_optional(Message, "reply_to_message")
		self.via_bot: User = self._get_optional(User, "via_bot")
		self.edit_date: int = data.get("edit_date")
		self.media_group_id: str = data.get("media_group_id")
		self.author_signature: str = data.get("author_signature")
		self.text: str = data.get("text")
		self.entities: list[MessageEntity] = list()
		self._get_array_of(MessageEntity, "entities")
		self.animation: Animation = self._get_optional(Animation, "animation")
		self.audio: Audio = self._get_optional(Audio, "audio")
		self.document: Document = self._get_optional(Document, "document")
		self.photo: list[PhotoSize] = list()
		self._get_array_of(PhotoSize, "photo")
		self.sticker: Sticker = self._get_optional(Sticker, "sticker")
		self.video: Video = self._get_optional(Video, "video")
		self.video_note: VideoNote = self._get_optional(VideoNote, "video_note")
		self.voice: Voice = self._get_optional(Voice, "voice")
		self.caption: str = data.get("caption")
		self.caption_entities: list[MessageEntity] = list()
		self._get_array_of(MessageEntity, "caption_entities")
		self.contact: Contact = self._get_optional(Contact, "contact")
		self.dice: Dice = self._get_optional(Dice, "dice")
		self.game: Game = self._get_optional(Game, "game")
		self.poll: Poll = self._get_optional(Poll, "poll")
		self.venue: Venue = self._get_optional(Venue, "venue")
		self.location: Location = self._get_optional(Location, "location")
		self.new_chat_members: list[User] = list()
		self._get_array_of(User, "new_chat_members")
		self.left_chat_member: User = self._get_optional(User, "left_chat_member")
		self.new_chat_title: str = data.get("new_chat_title")
		self.new_chat_photo: list[PhotoSize] = list()
		self._get_array_of(PhotoSize, "new_chat_photo")
		self.delete_chat_photo: bool = self._get_optional(bool, "delete_chat_photo")
		self.group_chat_created: bool = self._get_optional(bool, "group_chat_created")
		self.supergroup_chat_created: bool = self._get_optional(bool, "supergroup_chat_created")
		self.channel_chat_created: bool = self._get_optional(bool, "channel_chat_created")
		self.message_auto_delete_timer_changed: MessageAutoDeleteTimerChanged = self._get_optional(MessageAutoDeleteTimerChanged, "message_auto_delete_timer_changed")
		self.migrate_to_chat_id: int = data.get("migrate_to_chat_id")
		self.migrate_from_chat_id: int = data.get("migrate_from_chat_id")
		self.pinned_message: Message = self._get_optional(Message, "pinned_message")
		self.invoice: Invoice = self._get_optional(Invoice, "invoice")
		self.successful_payment: SuccessfulPayment = self._get_optional(SuccessfulPayment, "successful_payment")
		self.connected_website: str = data.get("connected_website")
		self.passport_data: PassportData = self._get_optional(PassportData, "passport_data")
		self.proximity_alert_triggered: ProximityAlertTriggered = self._get_optional(ProximityAlertTriggered, "proximity_alert_triggered")
		self.voice_chat_scheduled: VoiceChatScheduled = self._get_optional(VoiceChatScheduled, "voice_chat_scheduled")
		self.voice_chat_started: VoiceChatStarted = self._get_optional(VoiceChatStarted, "voice_chat_started")
		self.voice_chat_ended: VoiceChatEnded = self._get_optional(VoiceChatEnded, "voice_chat_ended")
		self.voice_chat_participants_invited: VoiceChatParticipantsInvited = self._get_optional(VoiceChatParticipantsInvited, "voice_chat_participants_invited")
		self.reply_markup: InlineKeyboardMarkup = self._get_optional(InlineKeyboardMarkup, "reply_markup")

	def is_command(self):
		return len(self.entities) > 0 and self.entities[0].type == MessageEntityType.BOT_COMMAND and self.entities[0].offset == 0

	def extract_command(self):
		if len(self.text) > 0:
			return self.text[1:].split(" ")[0]
		return ""

	def __str__(self):
		if self.text: return self.text
		return super().__str__()

	@property
	def is_editable(self):
		return bool(self._bot_ref)

	def edit(self, new_text, **kwargs):
		if not self.is_editable:
			raise MessageEditError("Tried editing non-editable Message")
		self._bot_ref.api.edit_message_text(new_text, chat_id=self.chat.id, message_id=self.message_id, **kwargs)

	def edit_reply_keyboard(self, new_reply_keyboard: Optional[InlineKeyboardMarkup]=None, **kwargs):
		if not self.is_editable:
			raise MessageEditError("Tried editing non-editable Message")
		self._bot_ref.api.edit_message_reply_markup(chat_id=self.chat.id, message_id=self.message_id, reply_markup=new_reply_keyboard)

	def delete(self):
		if not self.is_editable:
			raise MessageDeleteError("Tried deleting non-editable Message")
		self._bot_ref.api.delete_message(chat_id=self.chat.id, message_id=self.message_id)

	def __eq__(self, other: object) -> bool:
		if isinstance(other, str):
			return self.text == other
		elif isinstance(other, Message):
			return self.message_id == other.message_id
		return super().__eq__(other)

class Update(ApiObject):
	"""https://core.telegram.org/bots/api#update"""

	def __init__(self, data):
		self.raw: dict = data

		self.update_id: int = data["update_id"]
		
		# optional parameters
		self.message: Message = self._get_optional(Message, "message")
		self.edited_message: Message = self._get_optional(Message, "edited_message")
		self.channel_post: Message = self._get_optional(Message, "channel_post")
		self.edited_channel_post: Message = self._get_optional(Message, "edited_channel_post")
		self.callback_query: CallbackQuery = self._get_optional(CallbackQuery, "callback_query")
		self.poll: Poll = self._get_optional(Poll, "poll")
		self.poll_answer: PollAnswer = self._get_optional(PollAnswer, "poll_answer")
		self.my_chat_member: ChatMemberUpdated = self._get_optional(ChatMemberUpdated, "my_chat_member")
		self.chat_member: ChatMemberUpdated = self._get_optional(ChatMemberUpdated, "chat_member")
		self.chat_join_request: ChatJoinRequest = self._get_optional(ChatJoinRequest, "chat_join_request")

class TelegramAPI:

	def __init__(self, token: str):
		self.token: str = token
		self.offset: int = 0

	def set_bot(self, bot):
		self._bot_ref = bot

	def call(self, func_name: str, args=dict()) -> dict:
		url = f"https://api.telegram.org/bot{self.token}/{func_name}"
		args = {k: v for k, v in args.items() if v is not None}
		for k, v in args.items():
			if isinstance(v, ApiObject):
				args[k] = json.dumps(v._export())
			if not isinstance(args[k], str):
				args[k] = json.dumps(args[k])
		for _ in range(10):
			try:
				content = requests.get(url, params=args).content
				if content == "True":
					return True
				result = json.loads(content)
				if result["ok"]:
					return result["result"]
				else:
					raise TelegramAPIError((
						f"\"{func_name}\": "
						f"{result['description']} "
						f"[Error Code {result['error_code']}]"
					))
			except Exception as e:
				if isinstance(e, requests.RequestException):
					time.sleep(1)
				else:
					raise e
		raise TelegramAPIError("Request failed")

	def getUpdates(self) -> List[Update]:
		args = dict()
		if self.offset: args["offset"] = self.offset + 1
		data = self.call("getUpdates", args=args)
		results: list = [r for r in data if r["update_id"] > self.offset]
		if results:
			self.offset = results[-1]["update_id"]
			return [Update(result) for result in results]
		return list()

	def __getattr__(self, attr):
		if attr in self.__dict__:
			return self.__dict__[attr]
		return lambda **kwargs: self.call(attr, kwargs)

	# BOT API METHODS

	def get_me(self) -> User:
		"""A simple method for testing your bot's authentication token. Requires no parameters. Returns basic information about the bot in form of a User object."""
		return User(self.call("getMe"))

	def log_out(self):
		"""Use this method to log out from the cloud Bot API server before launching the bot locally. You must log out the bot before running it locally, otherwise there is no guarantee that the bot will receive updates. After a successful call, you can immediately log in on a local server, but will not be able to log in back to the cloud Bot API server for 10 minutes. Returns True on success. Requires no parameters."""
		return self.call("logOut")

	def close(self):
		"""Use this method to close the bot instance before moving it from one local server to another. You need to delete the webhook before calling this method to ensure that the bot isn't launched again after server restart. The method will return error 429 in the first 10 minutes after the bot is launched. Returns True on success. Requires no parameters."""
		return self.call("close")

	def send_message(self,
		chat_id: int or str,
		text: str,
		parse_mode: Optional[str]=None,
		entities: Optional[List[MessageEntity]]=None,
		disable_web_page_preview: Optional[bool]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None) -> Message:
		"""Use this method to send text messages. On success, the sent Message is returned."""
		return Message(self.call("sendMessage", {k: v for k, v in locals().items() if k != "self"}))

	def forward_message(self,
		chat_id: int or str,
		from_chat_id: int or str,
		message_id: int,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None):
		"""Use this method to forward messages of any kind. Service messages can't be forwarded. On success, the sent Message is returned."""
		return self.call("forwardMessage", {k: v for k, v in locals().items() if k != "self"})

	def copy_message(self,
		chat_id: int or str,
		from_chat_id: int or str,
		message_id: int,
		caption: Optional[str]=None,
		parse_mode: Optional[str]=None,
		caption_entities: Optional[List[MessageEntity]]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to copy messages of any kind. Service messages and invoice messages can't be copied. The method is analogous to the method forwardMessage, but the copied message doesn't have a link to the original message. Returns the MessageId of the sent message on success."""
		return self.call("copyMessage", {k: v for k, v in locals().items() if k != "self"})

	def send_photo(self,
		chat_id: int or str,
		photo: str,
		caption: Optional[str]=None,
		parse_mode: Optional[str]=None,
		caption_entities: Optional[List[MessageEntity]]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send photos. On success, the sent Message is returned."""
		return self.call("sendPhoto", {k: v for k, v in locals().items() if k != "self"})

	def send_audio(self,
		chat_id: int or str,
		audio: str,
		caption: Optional[str]=None,
		parse_mode: Optional[str]=None,
		caption_entities: Optional[List[MessageEntity]]=None,
		duration: Optional[int]=None,
		performer: Optional[str]=None,
		title: Optional[str]=None,
		thumb: Optional[str]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .MP3 or .M4A format. On success, the sent Message is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future."""
		return self.call("sendAudio", {k: v for k, v in locals().items() if k != "self"})

	def send_document(self,
		chat_id: int or str,
		document: str,
		thumb: Optional[str]=None,
		caption: Optional[str]=None,
		parse_mode: Optional[str]=None,
		caption_entities: Optional[List[MessageEntity]]=None,
		disable_content_type_detection: Optional[bool]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send general files. On success, the sent Message is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future."""
		return self.call("sendDocument", {k: v for k, v in locals().items() if k != "self"})

	def send_video(self,
		chat_id: int or str,
		video: str,
		duration: Optional[int]=None,
		width: Optional[int]=None,
		height: Optional[int]=None,
		thumb: Optional[str]=None,
		caption: Optional[str]=None,
		parse_mode: Optional[str]=None,
		caption_entities: Optional[List[MessageEntity]]=None,
		supports_streaming: Optional[bool]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send video files, Telegram clients support mp4 videos (other formats may be sent as Document). On success, the sent Message is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future."""
		return self.call("sendVideo", {k: v for k, v in locals().items() if k != "self"})

	def send_animation(self,
		chat_id: int or str,
		animation: str,
		duration: Optional[int]=None,
		width: Optional[int]=None,
		height: Optional[int]=None,
		thumb: Optional[str]=None,
		caption: Optional[str]=None,
		parse_mode: Optional[str]=None,
		caption_entities: Optional[List[MessageEntity]]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent Message is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future."""
		return self.call("sendAnimation", {k: v for k, v in locals().items() if k != "self"})

	def send_voice(self,
		chat_id: int or str,
		voice: str,
		caption: Optional[str]=None,
		duration: Optional[int]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS (other formats may be sent as Audio or Document). On success, the sent Message is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future."""
		return self.call("sendVoice", {k: v for k, v in locals().items() if k != "self"})

	def send_video_note(self,
		chat_id: int or str,
		video_note: str,
		duration: Optional[int]=None,
		length: Optional[int]=None,
		thumb: Optional[str]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent Message is returned."""
		return self.call("sendVideoNote", {k: v for k, v in locals().items() if k != "self"})

	def send_media_group(self,
		chat_id: int or str,
		media: List[InputMediaAudio],
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None):
		"""Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of Messages that were sent is returned."""
		return self.call("sendMediaGroup", {k: v for k, v in locals().items() if k != "self"})

	def send_location(self,
		chat_id: int or str,
		latitude: float,
		longitude: float,
		horizontal_accuracy: Optional[float]=None,
		live_period: Optional[int]=None,
		heading: Optional[int]=None,
		proximity_alert_radius: Optional[int]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send point on the map. On success, the sent Message is returned."""
		return self.call("sendLocation", {k: v for k, v in locals().items() if k != "self"})

	def edit_message_live_location(self,
		longitude: float,
		latitude: float,
		chat_id: Optional[int or str]=None,
		message_id: Optional[int]=None,
		inline_message_id: Optional[str]=None,
		horizontal_accuracy: Optional[float]=None,
		heading: Optional[int]=None,
		proximity_alert_radius: Optional[int]=None,
		reply_markup: Optional[InlineKeyboardMarkup]=None):
		"""Use this method to edit live location messages. A location can be edited until its live_period expires or editing is explicitly disabled by a call to stopMessageLiveLocation. On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned."""
		return self.call("editMessageLiveLocation", {k: v for k, v in locals().items() if k != "self"})

	def stop_message_live_location(self,
		chat_id: Optional[int or str]=None,
		message_id: Optional[int]=None,
		inline_message_id: Optional[str]=None,
		reply_markup: Optional[InlineKeyboardMarkup]=None):
		"""Use this method to stop updating a live location message before live_period expires. On success, if the message is not an inline message, the edited Message is returned, otherwise True is returned."""
		return self.call("stopMessageLiveLocation", {k: v for k, v in locals().items() if k != "self"})

	def send_venue(self,
		chat_id: int or str,
		latitude: float,
		longitude: float,
		title: str,
		address: str,
		foursquare_id: Optional[str]=None,
		foursquare_type: Optional[str]=None,
		google_place_id: Optional[str]=None,
		google_place_type: Optional[str]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send information about a venue. On success, the sent Message is returned."""
		return self.call("sendVenue", {k: v for k, v in locals().items() if k != "self"})

	def send_contact(self,
		chat_id: int or str,
		phone_number: str,
		first_name: str,
		last_name: Optional[str]=None,
		vcard: Optional[str]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send phone contacts. On success, the sent Message is returned."""
		return self.call("sendContact", {k: v for k, v in locals().items() if k != "self"})

	def send_poll(self,
		chat_id: int or str,
		question: str,
		options: List[str],
		is_anonymous: Optional[bool]=None,
		type: Optional[str]=None,
		allows_multiple_answers: Optional[bool]=None,
		correct_option_id: Optional[int]=None,
		explanation: Optional[str]=None,
		explanation_parse_mode: Optional[str]=None,
		explanation_entities: Optional[List[MessageEntity]]=None,
		open_period: Optional[int]=None,
		close_date: Optional[int]=None,
		is_closed: Optional[bool]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send a native poll. On success, the sent Message is returned."""
		return self.call("sendPoll", {k: v for k, v in locals().items() if k != "self"})

	def send_dice(self,
		chat_id: int or str,
		emoji: Optional[str]=None,
		disable_notification: Optional[bool]=None,
		protect_content: Optional[bool]=None,
		reply_to_message_id: Optional[int]=None,
		allow_sending_without_reply: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply]=None):
		"""Use this method to send an animated emoji that will display a random value. On success, the sent Message is returned."""
		return self.call("sendDice", {k: v for k, v in locals().items() if k != "self"})

	def send_chat_action(self,
		chat_id: int or str,
		action: str):
		"""Use this method when you need to tell the user that something is happening on the bot's side. The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status). Returns True on success."""
		return self.call("sendChatAction", {k: v for k, v in locals().items() if k != "self"})

	def get_user_profile_photos(self,
		user_id: int,
		offset: Optional[int]=None,
		limit: Optional[int]=None):
		"""Use this method to get a list of profile pictures for a user. Returns a UserProfilePhotos object."""
		return self.call("getUserProfilePhotos", {k: v for k, v in locals().items() if k != "self"})

	def get_file(self,
		file_id: str):
		"""Use this method to get basic info about a file and prepare it for downloading. For the moment, bots can download files of up to 20MB in size. On success, a File object is returned. The file can then be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>, where <file_path> is taken from the response. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling getFile again."""
		return self.call("getFile", {k: v for k, v in locals().items() if k != "self"})

	def ban_chat_member(self,
		chat_id: int or str,
		user_id: int,
		until_date: Optional[int]=None,
		revoke_messages: Optional[bool]=None):
		"""Use this method to ban a user in a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc., unless unbanned first. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns True on success."""
		return self.call("banChatMember", {k: v for k, v in locals().items() if k != "self"})

	def unban_chat_member(self,
		chat_id: int or str,
		user_id: int,
		only_if_banned: Optional[bool]=None):
		"""Use this method to unban a previously banned user in a supergroup or channel. The user will not return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. By default, this method guarantees that after the call the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat they will also be removed from the chat. If you don't want this, use the parameter only_if_banned. Returns True on success."""
		return self.call("unbanChatMember", {k: v for k, v in locals().items() if k != "self"})

	def restrict_chat_member(self,
		chat_id: int or str,
		user_id: int,
		permissions: ChatPermissions,
		until_date: Optional[int]=None):
		"""Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate administrator rights. Pass True for all permissions to lift restrictions from a user. Returns True on success."""
		return self.call("restrictChatMember", {k: v for k, v in locals().items() if k != "self"})

	def promote_chat_member(self,
		chat_id: int or str,
		user_id: int,
		is_anonymous: Optional[bool]=None,
		can_manage_chat: Optional[bool]=None,
		can_post_messages: Optional[bool]=None,
		can_edit_messages: Optional[bool]=None,
		can_delete_messages: Optional[bool]=None,
		can_manage_voice_chats: Optional[bool]=None,
		can_restrict_members: Optional[bool]=None,
		can_promote_members: Optional[bool]=None,
		can_change_info: Optional[bool]=None,
		can_invite_users: Optional[bool]=None,
		can_pin_messages: Optional[bool]=None):
		"""Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Pass False for all boolean parameters to demote a user. Returns True on success."""
		return self.call("promoteChatMember", {k: v for k, v in locals().items() if k != "self"})

	def set_chat_administrator_custom_title(self,
		chat_id: int or str,
		user_id: int,
		custom_title: str):
		"""Use this method to set a custom title for an administrator in a supergroup promoted by the bot. Returns True on success."""
		return self.call("setChatAdministratorCustomTitle", {k: v for k, v in locals().items() if k != "self"})

	def ban_chat_sender_chat(self,
		chat_id: int or str,
		sender_chat_id: int):
		"""Use this method to ban a channel chat in a supergroup or a channel. Until the chat is unbanned, the owner of the banned chat won't be able to send messages on behalf of any of their channels. The bot must be an administrator in the supergroup or channel for this to work and must have the appropriate administrator rights. Returns True on success."""
		return self.call("banChatSenderChat", {k: v for k, v in locals().items() if k != "self"})

	def unban_chat_sender_chat(self,
		chat_id: int or str,
		sender_chat_id: int):
		"""Use this method to unban a previously banned channel chat in a supergroup or channel. The bot must be an administrator for this to work and must have the appropriate administrator rights. Returns True on success."""
		return self.call("unbanChatSenderChat", {k: v for k, v in locals().items() if k != "self"})

	def set_chat_permissions(self,
		chat_id: int or str,
		permissions: ChatPermissions):
		"""Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the can_restrict_members administrator rights. Returns True on success."""
		return self.call("setChatPermissions", {k: v for k, v in locals().items() if k != "self"})

	def export_chat_invite_link(self,
		chat_id: int or str):
		"""Use this method to generate a new primary invite link for a chat; any previously generated primary link is revoked. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the new invite link as String on success."""
		return self.call("exportChatInviteLink", {k: v for k, v in locals().items() if k != "self"})

	def create_chat_invite_link(self,
		chat_id: int or str,
		name: Optional[str]=None,
		expire_date: Optional[int]=None,
		member_limit: Optional[int]=None,
		creates_join_request: Optional[bool]=None):
		"""Use this method to create an additional invite link for a chat. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. The link can be revoked using the method revokeChatInviteLink. Returns the new invite link as ChatInviteLink object."""
		return self.call("createChatInviteLink", {k: v for k, v in locals().items() if k != "self"})

	def edit_chat_invite_link(self,
		chat_id: int or str,
		invite_link: str,
		name: Optional[str]=None,
		expire_date: Optional[int]=None,
		member_limit: Optional[int]=None,
		creates_join_request: Optional[bool]=None):
		"""Use this method to edit a non-primary invite link created by the bot. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the edited invite link as a ChatInviteLink object."""
		return self.call("editChatInviteLink", {k: v for k, v in locals().items() if k != "self"})

	def revoke_chat_invite_link(self,
		chat_id: int or str,
		invite_link: str):
		"""Use this method to revoke an invite link created by the bot. If the primary link is revoked, a new link is automatically generated. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the revoked invite link as ChatInviteLink object."""
		return self.call("revokeChatInviteLink", {k: v for k, v in locals().items() if k != "self"})

	def approve_chat_join_request(self,
		chat_id: int or str,
		user_id: int):
		"""Use this method to approve a chat join request. The bot must be an administrator in the chat for this to work and must have the can_invite_users administrator right. Returns True on success."""
		return self.call("approveChatJoinRequest", {k: v for k, v in locals().items() if k != "self"})

	def decline_chat_join_request(self,
		chat_id: int or str,
		user_id: int):
		"""Use this method to decline a chat join request. The bot must be an administrator in the chat for this to work and must have the can_invite_users administrator right. Returns True on success."""
		return self.call("declineChatJoinRequest", {k: v for k, v in locals().items() if k != "self"})

	def set_chat_photo(self,
		chat_id: int or str,
		photo: str):
		"""Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns True on success."""
		return self.call("setChatPhoto", {k: v for k, v in locals().items() if k != "self"})

	def delete_chat_photo(self,
		chat_id: int or str):
		"""Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns True on success."""
		return self.call("deleteChatPhoto", {k: v for k, v in locals().items() if k != "self"})

	def set_chat_title(self,
		chat_id: int or str,
		title: str):
		"""Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns True on success."""
		return self.call("setChatTitle", {k: v for k, v in locals().items() if k != "self"})

	def set_chat_description(self,
		chat_id: int or str,
		description: Optional[str]=None):
		"""Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns True on success."""
		return self.call("setChatDescription", {k: v for k, v in locals().items() if k != "self"})

	def pin_chat_message(self,
		chat_id: int or str,
		message_id: int,
		disable_notification: Optional[bool]=None):
		"""Use this method to add a message to the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns True on success."""
		return self.call("pinChatMessage", {k: v for k, v in locals().items() if k != "self"})

	def unpin_chat_message(self,
		chat_id: int or str,
		message_id: Optional[int]=None):
		"""Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns True on success."""
		return self.call("unpinChatMessage", {k: v for k, v in locals().items() if k != "self"})

	def unpin_all_chat_messages(self,
		chat_id: int or str):
		"""Use this method to clear the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns True on success."""
		return self.call("unpinAllChatMessages", {k: v for k, v in locals().items() if k != "self"})

	def leave_chat(self,
		chat_id: int or str):
		"""Use this method for your bot to leave a group, supergroup or channel. Returns True on success."""
		return self.call("leaveChat", {k: v for k, v in locals().items() if k != "self"})

	def get_chat(self,
		chat_id: int or str):
		"""Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a Chat object on success."""
		return self.call("getChat", {k: v for k, v in locals().items() if k != "self"})

	def get_chat_administrators(self,
		chat_id: int or str):
		"""Use this method to get a list of administrators in a chat. On success, returns an Array of ChatMember objects that contains information about all chat administrators except other bots. If the chat is a group or a supergroup and no administrators were appointed, only the creator will be returned."""
		return self.call("getChatAdministrators", {k: v for k, v in locals().items() if k != "self"})

	def get_chat_member_count(self,
		chat_id: int or str):
		"""Use this method to get the number of members in a chat. Returns Int on success."""
		return self.call("getChatMemberCount", {k: v for k, v in locals().items() if k != "self"})

	def get_chat_member(self,
		chat_id: int or str,
		user_id: int):
		"""Use this method to get information about a member of a chat. Returns a ChatMember object on success."""
		return self.call("getChatMember", {k: v for k, v in locals().items() if k != "self"})

	def set_chat_sticker_set(self,
		chat_id: int or str,
		sticker_set_name: str):
		"""Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success."""
		return self.call("setChatStickerSet", {k: v for k, v in locals().items() if k != "self"})

	def delete_chat_sticker_set(self,
		chat_id: int or str):
		"""Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success."""
		return self.call("deleteChatStickerSet", {k: v for k, v in locals().items() if k != "self"})

	def answer_callback_query(self,
		callback_query_id: str,
		text: Optional[str]=None,
		show_alert: Optional[bool]=None,
		url: Optional[str]=None,
		cache_time: Optional[int]=None):
		"""Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to the user as a notification at the top of the chat screen or as an alert. On success, True is returned."""
		return self.call("answerCallbackQuery", {k: v for k, v in locals().items() if k != "self"})

	def set_my_commands(self,
		commands: List[BotCommand],
		scope: Optional[BotCommandScope]=None,
		language_code: Optional[str]=None):
		"""Use this method to change the list of the bot's commands. See https://core.telegram.org/bots#commands for more details about bot commands. Returns True on success."""
		return self.call("setMyCommands", {k: v for k, v in locals().items() if k != "self"})

	def delete_my_commands(self,
		scope: Optional[BotCommandScope]=None,
		language_code: Optional[str]=None):
		"""Use this method to delete the list of the bot's commands for the given scope and user language. After deletion, higher level commands will be shown to affected users. Returns True on success."""
		return self.call("deleteMyCommands", {k: v for k, v in locals().items() if k != "self"})

	def get_my_commands(self,
		scope: Optional[BotCommandScope]=None,
		language_code: Optional[str]=None):
		"""Use this method to get the current list of the bot's commands for the given scope and user language. Returns Array of BotCommand on success. If commands aren't set, an empty list is returned."""
		return self.call("getMyCommands", {k: v for k, v in locals().items() if k != "self"})

	def edit_message_text(self,
		text: str,
		chat_id: Optional[int or str]=None,
		message_id: Optional[int]=None,
		inline_message_id: Optional[str]=None,
		parse_mode: Optional[str]=None,
		entities: Optional[List[MessageEntity]]=None,
		disable_web_page_preview: Optional[bool]=None,
		reply_markup: Optional[InlineKeyboardMarkup]=None):
		"""Use this method to edit text and game messages. On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned."""
		return self.call("editMessageText", {k: v for k, v in locals().items() if k != "self"})

	def edit_message_caption(self,
		chat_id: Optional[int or str]=None,
		message_id: Optional[int]=None,
		inline_message_id: Optional[str]=None,
		caption: Optional[str]=None,
		parse_mode: Optional[str]=None,
		caption_entities: Optional[List[MessageEntity]]=None,
		reply_markup: Optional[InlineKeyboardMarkup]=None):
		"""Use this method to edit captions of messages. On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned."""
		return self.call("editMessageCaption", {k: v for k, v in locals().items() if k != "self"})

	def edit_message_media(self,
		media: InputMedia,
		chat_id: Optional[int or str]=None,
		message_id: Optional[int]=None,
		inline_message_id: Optional[str]=None,
		reply_markup: Optional[InlineKeyboardMarkup]=None):
		"""Use this method to edit animation, audio, document, photo, or video messages. If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo or a video otherwise. When an inline message is edited, a new file can't be uploaded; use a previously uploaded file via its file_id or specify a URL. On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned."""
		return self.call("editMessageMedia", {k: v for k, v in locals().items() if k != "self"})

	def edit_message_reply_markup(self,
		chat_id: Optional[int or str]=None,
		message_id: Optional[int]=None,
		inline_message_id: Optional[str]=None,
		reply_markup: Optional[InlineKeyboardMarkup]=None):
		"""Use this method to edit only the reply markup of messages. On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned."""
		return self.call("editMessageReplyMarkup", {k: v for k, v in locals().items() if k != "self"})

	def delete_message(self,
		chat_id: int or str,
		message_id: int) -> None:
		"""Use this method to delete a message, including service messages, with the following limitations: - A message can only be deleted if it was sent less than 48 hours ago. - A dice message in a private chat can only be deleted if it was sent more than 24 hours ago. - Bots can delete outgoing messages in private chats, groups, and supergroups. - Bots can delete incoming messages in private chats. - Bots can't be deleted from channel chats. - Otherwise, if the bot is an administrator in a group or a supergroup and it can delete messages of up to 50 people it can do so. Returns True on success."""
		return self.call("deleteMessage", {k: v for k, v in locals().items() if k != "self"})
