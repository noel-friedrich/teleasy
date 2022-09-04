# an example of a full implementation of a quiz-bot

```python
# import TelegramBot and ChatInstance Object
from teleasy import TelegramBot, ChatInstance

# insert your bot token here
TOKEN = "2125143963:AAGzdnKFp9XKPcZgXiHGfPZz2XEAY8egigI"

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

# initialize the telegram bot
bot = TelegramBot(TOKEN)

@bot.on_normal_message
def normal_message(chat: ChatInstance):
    chat.print("hi! Use /quiz to play the quiz!")

@bot.on_command("/start")
def start_command(chat: ChatInstance):
    chat.print("Welcome to the quiz bot!")
    chat.print("Use /quiz to start the quiz")

@bot.on_command("/quiz")
def quiz_command(chat: ChatInstance):
    chat.print("You have initiated the Quiz! Let's go!")

    score_count = 0

    for question, answers_dict in quiz.items():

        answer_options = list(answers_dict.keys())
        # use the chat.select method to prompt the user the options
        # the chat.select method returns the chosen answer
        answer = chat.select(question, answer_options, columns=2)
        # if the chosen answer is true
        if answers_dict[answer] is True:
            # increment the score count
            score_count += 1
    
    # same as chat.print(*args)
    return f"Finished!\nYour Score: {score_count}/{len(quiz)}"

# start the telegram bot
bot.start()
```
![Telegram-Chat](https://github.com/noel-friedrich/teleasy/blob/7e1d6d457c0a1bb01cfed4a17b40d4de1979abb2/screenshots/quiz.PNG "chat")
