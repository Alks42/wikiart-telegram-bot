import bot
from flask import Flask

app = Flask(__name__)

@app.route('/unic-indefecator')
def run_script():
    return bot.main()

@app.route('/')
def home_page():
    return "Code 200"