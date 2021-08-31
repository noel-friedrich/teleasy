# teleasy _1.0.1_
> Creating Telegram Bots made simple

## Table of contents
* [Example](#example)
* [Setup](#setup)
* [Tutorial](#tutorial)
* [Status](#status)

## Example
```python
from teleasy import TelegramBot, UpdateInfo

bot = TelegramBot(<YOUR_TOKEN>)

def say_hello(info: UpdateInfo) -> str:
    return f"hello {info.first_name}"

bot.set_normal(say_hello)

def dialogue_command(info: UpdateInfo) -> str:
    info.respond("Hi!")
    color = info.input("what is your favorite color?")
    food = info.input("and what is your favorite food?")
    return f"Cool!\nColor: {color}\nFood: {food}"
    
bot.set_command("dialogue", dialogue_command) 

bot.start()
```
![Telegram-Chat](https://github.com/noel-friedrich/teleasy/blob/7e1d6d457c0a1bb01cfed4a17b40d4de1979abb2/screenshots/example.PNG "chat")

## Setup

```
pip install teleasy
pip3 install teleasy
```
```
python3 -m pip install teleasy
```
```python
# Now, you can import the relevant Classes using
from teleasy import TelegramBot, UpdateInfo

# or just do
import teleasy
# and access the classes from the 'teleasy' object directly
telegram_bot = teleasy.TelegramBot
update_info = teleasy.UpdateInfo
```

## Tutorial
```python
# first import the relevant classes
from teleasy import TelegramBot, UpdateInfo

# create bot object using your token as parameter
bot = TelegramBot(<YOUR_TOKEN>)

# You can create functions to respond to Messages
# A provided function will be given an UpdateInfo object as
# a parameter to get information about the sender and to
# access bot methods

# let's define our first message handler
def normal_message_handler(info: UpdateInfo):
    return "Hello World!"
    
# as you can see, a message handler can respond to a text by returning
# its answer as a string (or alternatively a list of strings)

# we now need to tell the bot to use our defined handler 
# when it receives a normal text message:
bot.set_normal(normal_message_handler)

# now we need to start the bot
bot.start()

# and it's ready to go! Feel free to copy this code and test it out with your
# API-TOKEN! It should reply to normal messages with "Hello World!"
```
![Telegram-Chat](https://github.com/noel-friedrich/teleasy/blob/7e1d6d457c0a1bb01cfed4a17b40d4de1979abb2/screenshots/example1.PNG "chat")
### command handlers

```python
# we can also define a command handler:

def help_command_handler(info: UpdateInfo):
    return "Welcome to the Help-Function"
    
# now we need to tell the bot to use the handler when it receives a 'help' command
bot.set_command("help", help_command_handler)
```
![Telegram-Chat](https://github.com/noel-friedrich/teleasy/blob/7e1d6d457c0a1bb01cfed4a17b40d4de1979abb2/screenshots/helpfunction.PNG "chat")
### user input

```python
# each telegram message handler will be given its own thread to operate in
# this allows us to get user input very easily by doing so:

def dialogue_command(info: UpdateInfo):
    # the info.input method works like the built-in 'input()' method in python
    color = info.input("What's your favorite color?")
    food = info.input("What's your favorite food?")
    return f"color: {color}\nfood: {food}"
    
bot.set_command("dialogue", dialogue_command)
    
# now we need to tell the bot to use the handler when it receives a 'help' command
bot.set_command("help", help_command_handler)
```
![Telegram-Chat](https://github.com/noel-friedrich/teleasy/blob/7e1d6d457c0a1bb01cfed4a17b40d4de1979abb2/screenshots/dialogue.PNG "chat")

## Status
Project is _IN PROGRESS_
