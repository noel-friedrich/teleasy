# Documentation

## Table of contents
* [teleasy.TelegramBot](#teleasy.TelegramBot)

## teleasy.TelegramBot

<p align="center">
    Initializing and Importing
</p>

```python
from teleasy import TelegramBot

# instantiate using bot token:
my_bot = TelegramBot(<API-TOKEN>)
```

<p align="center">
    Functions/Methods
</p>

```python
TelegramBot.set_process_running_msg(new_message: str) -> None
# the process_running_msg will be sent to the user when he
# tries to invoke a new method while another active 
# process is currently running in his chat (he is prompted)
# this method changes the standart text to your new_message string
# standart message is: "failed: you already have an active process"

TelegramBot.set_timeout_msg(new_message: str) -> None
# the timeout_msg will be sent to the user when he hasn't sent
# any answer to a prompt the bot has sent him (e.g. using info.input)
# this method changes the standart text to your new_message string
# standart message is: "timed out. took too long to respond"

TelegramBot.set_cancel_command(new_command: str) -> None
# a user can cancel a prompt that the bot has sent using a
# cancel command. The standart cancel command is: "cancel"
# using this method, you can change the command-string to your liking

TelegramBot.set_cancel(new_command: str, new_function: function) -> None
# set new command_str (same as TelegramBot.set_cancel_command)
# set a new function to be invoked when the user types the cancel_command
# <i> the provided method must contain info.stop_thread() <i>
# this is the standart function that is invoked on the cancel command:
def cancel_func(info: UpdateInfo) -> None:
    info.respond("Cancelled Active Process")
    info.stop_thread()
    
TelegramBot.set_command(command: str, function: function) -> None
# set a new function to be invoked when the bot receives the
# provided command. The function will be given an UpdateInfo object
# as it's parameter

TelegramBot.set_normal(function: function) -> None
# set a function to be invoked when the bot receives a
# non-command text message. The function will be given an UpdateInfo object
# as it's parameter

TelegramBot.send_message(chat_id: str/int, msg: str, parse_mode="": str) -> bool
# will send a text message to the specified chat_id from the telegram bot
# it will return a boolean which represents the success of sending the message
# a message will not go through, if the user hasn't initiated a chat with the bot yet
# ,or for various other reasons that can be found on the official telegram documentation
# see http://sforsuresh.in/telegram-bot-message-formatting for the parse_mode

TelegramBot.start(interval=0.3: float) -> None
# will start the telegram polling process. Each (interval) seconds, the bot
# will check for new updates coming from the api. it will then handle the
# updates appropiately and will do this, until the programm is exitted
# you can, at any time, exit the program safely.
```

<p align="center">
    Other Attributes
</p>

```python
TelegramBot.token
# the bot token provided in TelegramBot.__init__

TelegramBot.commands
# dictionary containing all provided commands and their respective handler-function
# will always contain the cancel function.
```
