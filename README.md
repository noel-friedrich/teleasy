# teleasy
> Creating Telegram Bots made simple

## Table of contents
* [Example](#example)
* [Screenshots](#screenshots)
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

## Setup

```
pip install teleasy
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
### command handlers

```python
# we can also define a command handler:

def help_command_handler(info: UpdateInfo):
    return "Welcome to the Help-Function"
    
# now we need to tell the bot to use the handler when it receives a 'help' command
bot.set_command("help", help_command_handler)
```

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

### the UpdateInfo object

```python
UpdateInfo.message_id: str # message id of the message that caused the function to run
UpdateInfo.username: str # username of the sender of the message (may be hidden due to privacy setting)
UpdateInfo.text: str # the text of the message it received
UpdateInfo.first_name # first name of sender
UpdateInfo.date: str # date of message send that caused the update
UpdateInfo.chat_id: str # unique identification of the chat the message was sent in
UpdateInfo.from_bot: bool # True if sender is bot, else False
UpdateInfo.send_message(chat_id, msg) # function to send message to any user using the chat_id
UpdateInfo.respond(msg) # function to respond to the message 
UpdateInfo.input(msg, timeout=30) # function to get user input similar to inbuilt 'input()'
                                  # timeout will be called after specified seconds
UpdateInfo.get_answer(msg, timeout=30) # same as UpdateInfo.input
UpdateInfo.stop_thread() # function to stop any existing threads, should only be used in cancel command handler
UpdateInfo.wait(seconds, typing=False) # similar to time.sleep(seconds), will display "typing" for the user while the bot waits
UpdateInfo.select(message, options) # takes in message and list(str) as options, will display them as buttons and return chosen one
UpdateInfo.user_data: teleasy.UserData # UserData object, similar to dictionary, will always be the same for the same user for information to be stored in
```

### an example of a full implementation of a quiz-bot

```python
# import TelegramBot and UpdateInfo Object
from bot import TelegramBot, UpdateInfo

# insert your bot token here
TOKEN = <YOUR_BOT_TOKEN> (str)

# define quiz questions as dict
quiz = {
    "How high is the Eiffel Tower?": {
        "324m": True,
        "224m": False,
        "124m": False,
        "24m": False
    },

    "How far is the moon?": {
        "380km": False,
        "380m": False,
        "380k km": True,
        "38k km": False
    },

    "when was Shakespeare born?": {
        "1564": True,
        "1664": False,
        "1764": False,
        "1864": False
    }
}

def quiz_command(info: UpdateInfo) -> str:
    # initiate the quiz with a short message informing the user
    info.respond("You have initiated the Quiz! Let's go!")

    # prepare count of score, which will be incremented if 
    # the user answers a question correctly
    score_count = 0

    # iterate through all the quiz questions
    for question, answers_dict in quiz.items():
        # get answer options from the iterator "answers_dict"
        answer_options = list(answers_dict.keys())
        # use the info.select method to prompt the user the options
        # the info.select method returns the chosen answer
        answer = info.select(question, answer_options, columns=2)
        # if the chosen answer is true
        if answers_dict[answer] is True:
            # increment the score count
            score_count += 1
    
    # same as info.respond("...")
    return f"Finished!\nYour Score: {score_count}/{len(quiz)}"

# initialize the telegram bot
bot = TelegramBot(TOKEN)

# set a command handler to listen to command "quiz"
bot.set_command("quiz", quiz_command)

# start the telegram bot
bot.start()
```

## Screenshots
![Example screenshot](https://github.com/noel-friedrich/neural/blob/main/neural2884.PNG "Tkinter Visualization of Neural Network")

## Status
Project is _IN PROGRESS_  
_todo list in PROJECT: __Neural Network maker___  
https://github.com/noel-friedrich/neural/projects/1

## Credits
Training Algorithm Code was heavily inspired by https://machinelearningmastery.com/implement-backpropagation-algorithm-scratch-python/
