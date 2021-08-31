import requests, json, time, threading, sys

UpdateInfo = type("UpdateInfo", (), {})

class ConversationInfo:

    def __init__(self, error_handler):
        self.awaiting_input = False
        self.awaiting_answer = False
        self.active_func = False
        self.info_object = None
        self.thread = None
        self.error_handler = error_handler

    def set_error_handler(self, new_handler):
        self.error_handler = new_handler

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

class HandlerThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(HandlerThread, self).__init__(*args, **kwargs)

    def run(self) -> None:
        super(HandlerThread, self).run()

    def join(self, *args, **kwargs) -> None:
        super(HandlerThread, self).join(*args, **kwargs)

CONFIG = "[CONFIG]"
USER = "[USER]"
UPDATE = "[UPDATE]"
ERROR = "[ERROR]"

class TelegramBot:

    def __init__(self, token):
        self.token = token
        self._private_func = None
        self._last_update = None
        self.conversation_infos = dict()
        self._user_data = dict()
        self._reset_cancel()
        self._timeout_msg = "timed out. took too long to respond"
        self._process_running_msg = "failed: you already have an active process"
        self._standart_timeout = 30
        self.commands = {
            self._cancel_command: self._cancel_func
        }
        self._running = True
        self._reset_error_handler()
        self._reset_cancel()
        self.console_logging = False

        # INTERFACE
        self._interface_console_height = 25
        self.log_str = str()
        self.active_interface = False
        self._temp_interaction_count = 0

    def enable_console_logging(self, state=True):
        self.console_logging = state

    def log(self, line, prefix, end="\n"):
        self.log_str += f"{prefix} {line}{end}"
        if self.console_logging == True:
            print(f"{prefix} {line}{end}", end="")
        if self.active_interface:
            console_text = self.log_str
            lines = console_text.split("\n")[:-1]
            if len(lines) > self._interface_console_height:
                curr_lines = lines[-self._interface_console_height:]
                console_text = "\n".join(curr_lines)
            self._console_str_var.set(console_text)

    def set_error(self, new_handler):
        self._error_handler = new_handler

    def _reset_error_handler(self):
        def error_handler(info: UpdateInfo):
            info.respond(f"An Error occured")
        self._error_handler = error_handler

    def _get_args(self, message: str):
        try: arg_str = message.split(" ", 1)[1]
        except: return []
        arg_list = list()
        temp_arg = str()
        in_quotes = {
            '"': False,
            "'": False
        }
        for char in arg_str:
            if not in_quotes["'"] and not in_quotes['"'] and char == " ":
                arg_list.append(temp_arg)
                temp_arg = str()
            elif char == "'" or char == '"':
                in_quotes[char] = not in_quotes[char]
            else:
                temp_arg += char
        arg_list.append(temp_arg)
        return arg_list

    def set_standart_timeout(self, new_timeout: int):
        self._standart_timeout = new_timeout

    def set_process_running_msg(self, msg: str):
        self._process_running_msg = msg

    def set_timeout_msg(self, msg: str):
        self._timeout_msg = msg

    def _reset_cancel(self):
        self._cancel_command = "cancel"
        def cancel_func(info: UpdateInfo):
            info.stop_thread()
            return "Cancelled Active Process"
        self._cancel_func = cancel_func

    def set_cancel_command(self, command: str):
        self._cancel_command = command

    def set_cancel(self, command: str, function):
        self._cancel_command = command
        self._cancel_func = function

    def get_updates(self):
        try:
            args = dict()
            if self._last_update:
                args["offset"] = self._last_update + 1
            pure_result = self._send_request("getUpdates", args=args)
            if pure_result["ok"]:
                for result in pure_result["result"]:
                    self._last_update = result["update_id"]
                return pure_result["result"]
            return None
        except:
            print("[WARNING] Bot cannot reach API (could be caused by temporary timeout)")
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
        if command.startswith("/") and len(command) > 1:
            command = command[1:]
        self.commands[command] = function
        self.log(f'Set Command Handler for "/{command}"', CONFIG)

    def set_normal(self, function):
        self._private_func = function
        self.log(f"Set Normal Message Handler", CONFIG)

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

    def _run_user_func(self, func, info: UpdateInfo, recursive=False):
        conv_infos = self._get_infos(info.chat_id)
        def run():
            conv_infos.active_func = True
            conv_infos.info_object = info
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
            self._clear_infos(info.chat_id)
        if (conv_infos.active_func and info.text != f"/{self._cancel_command}"
            and not recursive):
            info.respond(self._process_running_msg)
        else:
            conv_infos.thread = HandlerThread(target=run)
            conv_infos.thread.start()

    def _get_infos(self, chat_id):
        if chat_id in self.conversation_infos:
            return self.conversation_infos[chat_id]
        self.conversation_infos[chat_id] = ConversationInfo(self._error_handler)
        return self.conversation_infos[chat_id]

    def _clear_infos(self, chat_id):
        if chat_id in self.conversation_infos:
            del self.conversation_infos[chat_id]
            return True
        return False

    def _wait_input(self, chat_id, msg, timeout=None, interval=0.3):
        if not timeout:
            timeout = self._standart_timeout
        if msg:
            self.send_message(chat_id, msg)
        conv_infos = self._get_infos(chat_id)
        conv_infos.awaiting_input = True
        start_time = time.time()
        while conv_infos.awaiting_input:
            time.sleep(interval)
            if not chat_id in self.conversation_infos:
                sys.exit()
            elif time.time() - start_time >= timeout:
                self.log(f"Timeout in Chat {chat_id}", USER)
                self.send_message(chat_id, self._timeout_msg)
                self._clear_infos(chat_id)
                sys.exit()
        return conv_infos.awaiting_answer

    def _stop_thread(self, chat_id):
        return self._clear_infos(chat_id)

    def _wait_type(self, chat_id, seconds, typing=True):
        if typing:
            self._send_request("sendChatAction", {"chat_id": chat_id,"action": "typing"})
        time.sleep(seconds)
    
    def _user_selection(self, chat_id, msg: str, options: list, columns=1, timeout=None, interval=0.3):
        if not timeout:
            timeout = self._standart_timeout
        buttons = list()
        while len(options) > 0:
            button_row = list()
            for i in range(columns):
                if len(options):
                    option = str(options.pop(0))
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
        ui.message_id = str(message_dict["message_id"])
        ui.username = "@" + message_dict["chat"]["username"]
        ui.text = message_dict["text"]
        ui.first_name = message_dict["chat"]["first_name"]
        ui.date = message_dict["date"]
        ui.chat_id = message_dict["chat"]["id"]
        ui.from_bot = message_dict["from"]["is_bot"]
        ui.send_message = self.send_message
        ui.respond = lambda msg, **args: self.send_message(ui.chat_id, msg, **args)
        ui.input = lambda msg, **args: self._wait_input(ui.chat_id, msg, **args)
        ui.get_answer = self._wait_input
        ui.stop_thread = lambda: self._stop_thread(ui.chat_id)
        ui.wait = lambda seconds, **args: self._wait_type(ui.chat_id, seconds, **args)
        ui.select = lambda msg, options, **args: self._user_selection(ui.chat_id, msg, options, **args)
        ui.select_from = self._user_selection
        ui.input_from = self._wait_input
        ui.bot = self

        if ui.text.startswith("/") and len(ui.text) > 0:
            ui.arguments = self._get_args(ui.text)
        else:
            ui.arguments = list()

        if not ui.chat_id in self._user_data:
            self._user_data[ui.chat_id] = UserData({})
        ui.user_data = self._user_data[ui.chat_id]

        conv_infos = self._get_infos(ui.chat_id)
        ui.set_error_handler = conv_infos.set_error_handler
        ui.conversation_info = conv_infos
        
        return ui

    def handle_callback_query(self, update):
        self._temp_interaction_count += 1
        self._send_request("answerCallbackQuery", {
            "callback_query_id": update["callback_query"]["id"]
        })
        data = update["callback_query"]["data"]
        chat_id = update["callback_query"]["from"]["id"]
        conv_infos = self._get_infos(chat_id)
        self.log(f"Received Callback Query from {chat_id}", USER)
        if conv_infos.awaiting_input:
            conv_infos.awaiting_answer = data
            conv_infos.awaiting_input = False
            return

    def handle_message_update(self, update):
        self._temp_interaction_count += 1
        info_object = self._make_info_object(update["message"])
        text = update["message"]["text"]
        trimmed_text = text[:10] + ("..." if len(text) > 10 else "")
        found_command = False
        if text.startswith("/") and len(text) > 1:
            if self._run_command(text[1:], update["message"]):
                self.log(f"Chat {info_object.chat_id} called /{trimmed_text[1:]}", USER)
                found_command = True
        if not(found_command):
            conv_infos = self._get_infos(info_object.chat_id)
            if conv_infos.awaiting_input:
                self.log(f"Received Answer (\"{trimmed_text}\") from {info_object.chat_id}", USER)
                conv_infos.awaiting_answer = info_object.text
                conv_infos.awaiting_input = False
                return
            elif self._private_func:
                self._run_user_func(self._private_func, info_object)
                self.log(f"Received \"{trimmed_text}\" from {info_object.chat_id}", USER)
            else:
                self.log(f"No Normal Message Handler defined", ERROR)

    def loop(self, interval=0.3):
        while self._running:
            time.sleep(interval)
            updates = self.get_updates()
            if updates == None: continue
            for update in updates:
                if "message" in update:
                    self.handle_message_update(update)
                elif "callback_query" in update:
                    self.handle_callback_query(update)

    def _find_thread(self, thread):
        for chat_id, conv in self.conversation_infos.items():
            if conv.thread == thread:
                return chat_id
        return None

    def _config_error_handler(self):
        def thread_error_handler(args):
            chat_id = self._find_thread(args.thread)
            conv = self._get_infos(chat_id)
            if conv.info_object == None:
                return
            conv.info_object.error = {
                "type": args.exc_type,
                "value": args.exc_value,
                "traceback": args.exc_traceback
            }
            conv.error_handler(conv.info_object)
            self._clear_infos(chat_id)
            self.log(f"{args.exc_type} in HandlerThread", ERROR)
            self.log(str(args.exc_value), ERROR)
        threading.excepthook = thread_error_handler

    def start(self, interval=0.3, console_logging=None):
        self.console_logging = console_logging if console_logging != None else self.console_logging
        self._config_error_handler()
        self.loop(interval=interval)

    def start_with_interface(self, interval=0.3, end=True):
        self._config_error_handler()
        bot_thread = HandlerThread(target=lambda: self.loop(interval=interval))
        bot_thread.start()
        self.start_interface()
        if end: self._running = False

    def start_interface(self):
        self.active_interface = True

        import tkinter

        def draw_graph(canvas, data):
            if len(data) < 2: return
            canvas.delete("all")
            canvas_width = int(canvas["width"])
            canvas_height = int(canvas["height"])
            x_point_diff = canvas_width / (len(data) - 1)
            data_max = max(data) if max(data) else 1
            y_point_diff = canvas_height * 0.9 / data_max

            light_grey = "#CCC"
            for i in range(1, data_max):
                y_coord = canvas_height - i * y_point_diff - (canvas_height * 0.05)
                canvas.create_line(0, y_coord, canvas_width, y_coord, width=1, fill=light_grey)
            for i in range(1, len(data) - 1):
                x_coord = i * x_point_diff
                canvas.create_line(x_coord, 0, x_coord, canvas_height, width=1, fill=light_grey)

            for i in range(len(data) - 1):
                x_coord_1 = x_point_diff * i
                x_coord_2 = x_point_diff * (i + 1)
                y_coord_1 = canvas_height - (data[i] * y_point_diff) - (canvas_height * 0.05)
                y_coord_2 = canvas_height - (data[i + 1] * y_point_diff) - (canvas_height * 0.05)
                canvas.create_line(x_coord_1, y_coord_1, x_coord_2, y_coord_2, width=2, fill="#555555")

            canvas.create_text(canvas_width // 2, 10, fill="darkblue", text="User Interactions (last 100s)")

        def keep_updating_graph(Canvas, data):
            interval = 5000
            data.append(self._temp_interaction_count)
            self._temp_interaction_count = 0
            if len(data) > 20:
                data.pop(0)
            draw_graph(Canvas, data)
            if self.active_interface:
                Canvas.after(interval, keep_updating_graph, Canvas, data)

        window = tkinter.Tk()
        window.title("Telegram Bot Monitor")

        self._console_str_var = tkinter.StringVar(window)
        self._console_str_var.set(self.log_str)

        Left_Frame = tkinter.Frame(
            borderwidth=2,
            relief="groove"
        )
        Right_Frame = tkinter.Frame(
            bg="red",
            width=50,
            height=50,
            borderwidth=2,
            relief="groove"
        )

        Console = tkinter.Label(
            Left_Frame,
            width=60,
            height=self._interface_console_height,
            textvariable=self._console_str_var,
            justify=tkinter.LEFT,
            anchor=tkinter.NW
        )
        Console.config(font="Terminal 14")
        Console.pack()

        Canvas = tkinter.Canvas(
            Left_Frame,
            height=150,
            width=Console.winfo_reqwidth()
        )
        Canvas.pack()
        Canvas.after(0, keep_updating_graph, Canvas, [0, 0])

        Left_Frame.pack(side=tkinter.LEFT)

        Console.config(state=tkinter.DISABLED)
        window.mainloop()
        self.active_interface = False