import requests, json, time, threading, sys

UpdateInfo = type("UpdateInfo", (), {})

class UserData:

    def __init__(self, attrs):
        self._attrs = attrs
        self._undefined_value = None

    def __setitem__(self, key, value):
        self._attrs[key] = value

    def __getitem__(self, key):
        if key in self._attrs:
            return self._attrs[key]
        return self._undefined_value

    def set(self, key, value):
        self._attrs[key] = value

    def get(self, key):
        return self[key]

    def isset(self, key):
        return bool(key in self._attrs)

    def set_undefined(self, new_value):
        self._undefined_value = new_value

class TelegramBot:

    def __init__(self, token):
        self.token = token
        self.private_func = None
        self._last_update = None
        self._awaiting_input = list()
        self._awaiting_answers = dict()
        self._active_threads = dict()
        self._user_data = dict()
        self._reset_cancel()
        self._timeout_msg = "timed out. took too long to respond"
        self._process_running_msg = "failed: you already have an active process"
        self.commands = {
            self._cancel_command: self._cancel_func
        }

    def set_process_running_msg(self, msg: str):
        self._process_running_msg = msg

    def set_timeout_msg(self, msg: str):
        self._timeout_msg = msg

    def _reset_cancel(self):
        self._cancel_command = "cancel"
        def cancel_func(info: UpdateInfo):
            info.respond("Cancelled Active Process")
            info.stop_thread()
        self._cancel_func = cancel_func

    def set_cancel_command(self, command: str):
        self._cancel_command = command

    def set_cancel(self, command: str, function):
        self._cancel_command = command
        self._cancel_func = function

    def get_updates(self):
        args = dict()
        if self._last_update:
            args["offset"] = self._last_update + 1
        pure_result = self._send_request("getUpdates", args=args)
        if pure_result["ok"]:
            for result in pure_result["result"]:
                self._last_update = result["update_id"]
            return pure_result["result"]
        return None

    def _send_request(self, function, args=dict()):
        base = "https://api.telegram.org/bot"
        url = f"{base}{self.token}/{function}"
        if args:
            url += "?"
            for key, item in args.items():
                url += f"{key}={item}&"
            url = url[:-1]
        response = requests.get(url)
        return json.loads(response.content)

    def set_command(self, command, function):
        self.commands[command] = function

    def set_normal(self, function):
        self.private_func = function

    def _run_command(self, command_text, message):
        for command, user_func in self.commands.items():
            if command == command_text:
                info_object = self._make_info_object(message)
                self._run_user_func(user_func, info_object)
                return True
        return False

    def send_message(self, chat_id: str, msg: str, parse_mode="") -> bool:
        result = self._send_request("sendMessage", {
            "chat_id": str(chat_id),
            "text": str(msg),
            "parse_mode": str(parse_mode)
        })
        if result["ok"]:
            return True
        return False

    def _run_user_func(self, func, info):
        def run():
            result = func(info)
            if type(result) == list:
                for message in result:
                    self.send_message(
                        info.chat_id,
                        message
                    )
            elif result != None:
                self.send_message(
                    info.chat_id,
                    result
                )
            del self._active_threads[info.chat_id]
        if info.chat_id in self._active_threads and info.text != f"/{self._cancel_command}":
            info.respond(self._process_running_msg)
        else:
            self._active_threads[info.chat_id] = threading.Thread(target=run)
            self._active_threads[info.chat_id].start()

    def _del_waiting(self, chat_id):
        if chat_id in self._awaiting_input:
            c_index = self._awaiting_input.index(chat_id)
            self._awaiting_input.pop(c_index)
            return True
        return False

    def _wait_input(self, chat_id, msg, timeout=30, interval=0.3):
        if msg:
            self.send_message(chat_id, msg)
        self._awaiting_input.append(chat_id)
        start_time = time.time()
        while chat_id in self._awaiting_input:
            time.sleep(interval)
            if not chat_id in self._active_threads:
                self._del_waiting(chat_id)
                del self._active_threads[chat_id]
                sys.exit()
            if time.time() - start_time >= timeout:
                self._del_waiting(chat_id)
                self.send_message(chat_id, self._timeout_msg)
                del self._active_threads[chat_id]
                sys.exit()
        return self._awaiting_answers[chat_id]

    def _stop_thread(self, chat_id):
        if chat_id in self._active_threads:
            del self._active_threads[chat_id]
            return True
        return False

    def _wait_type(self, chat_id, seconds, typing=True):
        if typing:
            self._send_request("sendChatAction", {"chat_id": chat_id,"action": "typing"})
        time.sleep(seconds)
    
    def _user_selection(self, chat_id, msg: str, options: list, columns=1, timeout=30, interval=0.3):
        buttons = list()
        while len(options) > 0:
            button_row = list()
            for i in range(columns):
                if len(options):
                    option = options.pop(0)
                    button = {"text": option, "callback_data": option}
                    button_row.append(button)
            buttons.append(button_row)
        json_buttons = json.dumps({"inline_keyboard": buttons})
        output = self._send_request("sendMessage", {
            "chat_id": chat_id,
            "text": msg,
            "reply_markup": json_buttons
        })
        return self._wait_input(chat_id, None, timeout=timeout, interval=0.3)

    def _make_info_object(self, message_dict):
        ui = UpdateInfo()
        ui.message_id = message_dict["message_id"]
        ui.username = "@" + message_dict["chat"]["username"]
        ui.text = message_dict["text"]
        ui.first_name = message_dict["chat"]["first_name"]
        ui.date = message_dict["date"]
        ui.chat_id = message_dict["chat"]["id"]
        ui.from_bot = message_dict["from"]["is_bot"]
        ui.send_message = self.send_message
        ui.respond = lambda msg, **args: self.send_message(ui.chat_id, msg, **args)
        ui.input = lambda msg, **args: self._wait_input(ui.chat_id, msg, **args)
        ui.get_answer = ui.input
        ui.stop_thread = lambda: self._stop_thread(ui.chat_id)
        ui.wait = lambda seconds, **args: self._wait_type(ui.chat_id, seconds, **args)
        ui.select = lambda msg, options, **args: self._user_selection(ui.chat_id, msg, options, **args)

        if not ui.chat_id in self._user_data:
            self._user_data[ui.chat_id] = UserData(dict())
        ui.user_data = self._user_data[ui.chat_id]
        return ui

    def handle_callback_query(self, update):
        self._send_request("answerCallbackQuery", {
            "callback_query_id": update["callback_query"]["id"]
        })
        data = update["callback_query"]["data"]
        chat_id = update["callback_query"]["from"]["id"]
        if chat_id in self._awaiting_input:
            self._awaiting_answers[chat_id] = data
            self._del_waiting(chat_id)
            return

    def handle_message_update(self, update):
        info_object = self._make_info_object(update["message"])
        text = update["message"]["text"]
        found_command = False
        if text.startswith("/") and len(text) > 1:
            if self._run_command(text[1:], update["message"]):
                found_command = True
        if self.private_func and not(found_command):
            if info_object.chat_id in self._awaiting_input:
                self._awaiting_answers[info_object.chat_id] = info_object.text
                self._del_waiting(info_object.chat_id)
                return
            self._run_user_func(self.private_func, info_object)

    def start(self, interval=0.3):
        while True:
            time.sleep(interval)
            updates = self.get_updates()
            if updates == None: continue
            for update in updates:
                if "message" in update:
                    self.handle_message_update(update)
                elif "callback_query" in update:
                    self.handle_callback_query(update)