# an example of a full implementation of a quiz-bot

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
![Telegram-Chat](https://github.com/noel-friedrich/teleasy/blob/7e1d6d457c0a1bb01cfed4a17b40d4de1979abb2/screenshots/quiz.PNG "chat")
