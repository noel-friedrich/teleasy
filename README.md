# teleasy _1.0.4_
> Creating Telegram Bots Made Simple  
> [PyPi Page](https://pypi.org/project/teleasy)

## Table of contents
* [Example](#example)
* [Setup](#setup)
* [Wiki](https://github.com/noel-friedrich/teleasy/wiki)
* [Introduction](#introduction)
* [Status](#status)

## Example
```python
from teleasy import TelegramBot, UpdateInfo

bot = TelegramBot(<YOUR_TOKEN>)

@bot.on_normal_message
def on_normal_message(chat: ChatInstance):
    chat.print(f"hello {chat.first_name}")

@bot.on_command("/input")
def input_example(chat: ChatInstance):
    color = chat.input("what's your favorite color?")
    chat.print(f"Your favorite color is {color}")

bot.start()
```
![Telegram-Chat](https://github.com/noel-friedrich/teleasy/blob/main/screenshots/primary-example.png?raw=true "chat")

> See [Examples-Folder](https://github.com/noel-friedrich/teleasy/tree/main/examples) for more

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
```
> see [Installation Help \(Wiki\)](https://github.com/noel-friedrich/teleasy/wiki#installation-help) for more Help

## Introduction

```python
# first import the relevant classes
from teleasy import TelegramBot, ChatInstance

# create bot object using your token as parameter
bot = TelegramBot(<YOUR_TOKEN>)

# let's define our first message handler that will respond
# to all messages with "Hello, World!"

@bot.on_normal_message
# tell the bot to use the following function
# when encountering normal messages
def normal_message_handler(chat: ChatInstance):
    # every handler will be passed a custom ChatInstance
    # this object contains information about the message
    # and may be used to get user input
    chat.print("Hello World!")
    
# handlers are run in parallel using multithreading to enable
# very easy handling of user input

# now we need to start the bot
bot.start()

# and it's ready to go! Feel free to copy this code and try it out
```
![Telegram-Chat](https://github.com/noel-friedrich/teleasy/blob/7e1d6d457c0a1bb01cfed4a17b40d4de1979abb2/screenshots/example1.PNG "chat")
### command handlers

```python
# we can also define command handlers:

@bot.on_command("/help") # optional "/" in front of command name
def help_command_handler(chat: ChatInstance):
    chat.print("Welcome to the Help-Function")
```
![Telegram-Chat](https://github.com/noel-friedrich/teleasy/blob/7e1d6d457c0a1bb01cfed4a17b40d4de1979abb2/screenshots/helpfunction.PNG "chat")
### user input

```python
# each telegram message handler will be given its own thread to operate in
# this allows us to get user input very easily by doing so:

@bot.on_command("dialogue")
def dialogue_command_handler(chat: ChatInstance):
    # the chat.input method works like the built-in 'input()' method in python
    color = chat.input("What's your favorite color?")
    food = chat.input("What's your favorite food?")
    chat.print(f"color: {color}\nfood: {food}")
```
![Telegram-Chat](https://github.com/noel-friedrich/teleasy/blob/7e1d6d457c0a1bb01cfed4a17b40d4de1979abb2/screenshots/dialogue.PNG "chat")

## Status
Project is _IN PROGRESS_
