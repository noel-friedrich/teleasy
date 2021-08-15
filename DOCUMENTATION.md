# Documentation

## Table of contents
* [Example](#example)
* [Setup](#setup)
* [Tutorial](#tutorial)
* [Status](#status)

## teleasy.TelegramBot

```python
from teleasy import TelegramBot

# instantiate using bot token:
my_bot = TelegramBot(<API-TOKEN>)
```

### Functions/Methods

```python
TelegramBot.set_process_running_msg(new_message: str)
# the process_running_msg will be sent to the user when he
# tries to invoke a new method while another active 
# process is currently running in his chat (he is prompted)
# this method changes the standart text to your new_message string
# standart message is: "failed: you already have an active process"

TelegramBot.set_timeout_msg(new_message: str)
# the timeout_msg will be sent to the user when he hasn't sent
# any answer to a prompt the bot has sent him (e.g. using info.input)
# this method changes the standart text to your new_message string
# standart message is: "timed out. took too long to respond"

TelegramBot.set_cancel_command(new_command: str)
# a user can cancel a prompt that the bot has sent using a
# cancel command. The standart cancel command is: "cancel"
# using this method, you can change the command-string to your liking
```

(not finished yet)
