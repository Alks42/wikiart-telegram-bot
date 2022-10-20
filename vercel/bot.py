"""
WikiART API request Limits
API calls: 10 requests per 2.5 seconds
Images downloading: 20 requests per second
Max requests per hour: 400
Max sessions per hour: 10
"""

import requests
import json
from random import choice, sample
from telebot import TeleBot, types
from urllib import parse
from os import environ, replace
from faunadb import query as q
from faunadb.client import FaunaClient

API_ACCESS_KEY = environ['API_ACCESS_KEY']
API_SECRET_KEY = environ['API_SECRET_KEY']
FAUNA_SECRET = environ['FAUNA_SECRET']
CHAT_ID = environ['CHAT_ID']  # telegram chat_id, int
TOKEN = environ['TOKEN']
BASE_URL = 'https://www.wikiart.org/en/'


def get_artist():
    # since there is no way to modify files in versel im using fauna db instead
    # also note that fauna db does not support python 3.10
    client = FaunaClient(f'{FAUNA_SECRET}')
    dump_artists = client.query(q.paginate(q.match(q.index("grab_all")), size=175))
    exclude = {}
    for artist in dump_artists["data"]:
        artist = client.query(q.get(q.ref(q.collection("dump"), artist.id())))['data']
        exclude = exclude | artist

    with open('impressionists.json', 'r') as f:
        all_artists = json.load(f).items()

    artist = choice([{name: artist_id} for name, artist_id in all_artists if artist_id not in exclude.values()])

    if len(exclude) != len(all_artists) - 1:
        client.query(
             q.create('dump', {'data': artist})
        )
    else:
        for artist in dump_artists["data"]:
            client.query(
                q.delete(q.ref(q.collection("dump"), artist.id()))
            )

    return artist


def get_details(artist: dict):
    key = requests.get(f'{BASE_URL}Api/2/login?accessCode={API_ACCESS_KEY}&secretCode={API_SECRET_KEY}').json()[
        'SessionKey']

    # --------------------- get artist details ---------------------
    url = f'{BASE_URL}{list(artist)[0]}'
    info = requests.get(f'{url}?json=2&authSessionKey={key}').json()
    name, portrait, title, bio = info['artistName'], info['image'], info['wikipediaUrl'], ''

    if title and 'en.wikipedia.org' in title:
        link = parse.unquote(title).split('#')[0].replace('wiki/', 'w/api.php?titles=')
        params = {'format': 'json',
                  'action': 'query',
                  'redirects': True,
                  'prop': 'extracts',
                  'exintro': '',
                  'explaintext': ''}
        bio = list(requests.get(link, params).json()['query']['pages'].values())
        if 'missing' not in bio:
            bio = bio[0]['extract'].split('\n')[0]

    # --------------------- get artist paintings -------------------
    req = requests.get(f'{BASE_URL}Api/2/PaintingsByArtist?id={list(artist.values())[0]}&authSessionKey={key}').json()
    paintings = sample([d['image'] for d in req['data']], k=7)
    return name, portrait, bio, url, paintings


def send_message(*args):
    name, portrait, bio, url, paintings = args
    caption = f'[{name}]({url})\n\n{bio}' if url else f'{name}\n\n{bio}'
    bot = TeleBot(TOKEN)
    bot.send_photo(CHAT_ID, portrait, caption, parse_mode='markdown')
    bot.send_media_group(CHAT_ID, [types.InputMediaPhoto(p) for p in paintings])


def main():
    artist = get_artist()
    params = get_details(artist)
    send_message(*params)
    return "status-code: 200"
