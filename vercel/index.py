import bot
from flask import Flask
from os import environ

UNIC_URL = '/' + environ['UNIC_URL']

app = Flask(__name__)

@app.route(UNIC_URL)
def run_script():
    return bot.main()

@app.route('/')
def home_page():
    return "Code 200"