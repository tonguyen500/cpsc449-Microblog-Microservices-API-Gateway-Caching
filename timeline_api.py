#CPSC 449 Project 2
#MicroBlogging service
#Jose Alvarado, Luan Nguyen, Sagar Joshi

import flask
from flask import request, jsonify, g, current_app
import sqlite3, time, datetime


DATABASE = 'data.db'
DEBUG = True


app = flask.Flask(__name__)
app.config.from_object(__name__)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = dict_factory
    return g.db

# initialize database

@app.cli.command('init')
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.teardown_appcontext
def close_db(e=None):
    if e is not None:
        print(f'Closing db: {e}')
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.route('/', methods=['GET'])
def home():
    return '''<h1>MicroBlogging</h1>
<p>A microblogging service similar to twitter.</p>
<p>Timeline microservice</p>'''


#getUserTimeline(username)
#Returns recent tweets from a user.


@app.route('/userTimeline', methods=['GET'])
def getUserTimeline():
    userInfo = request.get_json()
    Username = userInfo.get('username')

    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    userTimeline = cur.execute('SELECT * FROM TWEETS WHERE FK_USERS = ? ORDER BY DAY_OF DESC LIMIT 25', (Username)).fetchall()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify(userTimeline), 201


#getPublicTimeline()
#Returns recent tweets from all users.


@app.route('/publicTimeline', methods=['GET'])
def getPublicTimeline():
    conn = sqlite3.connect('data.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    recentTweets = cur.execute('SELECT * FROM TWEETS ORDER BY DAY_OF DESC LIMIT 25').fetchall()

    return jsonify(recentTweets), 201


#getHomeTimeline(username)
#Returns recent tweets from all users that this user follows.


@app.route('/homeTimeline', methods=['GET'])
def getHomeTimeline():
    userInfo = request.get_json()
    Username = userInfo.get('username')

    conn = sqlite3.connect('data.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    homeTweets = cur.execute('SELECT TWEET, DAY_OF, FK_USERS FROM TWEETS INNER JOIN FOLLOW ON FOLLOW.FOLLOWERS = TWEETS.FK_USERS WHERE FOLLOW.FK_USER = ? ORDER BY DAY_OF DESC LIMIT 25', (Username)).fetchall()

    return jsonify(homeTweets), 201


#postTweet(username, text)
#Post a new tweet.


@app.route('/postTweet', methods=['POST'])
def postTweet():
    unix = time.time()
    date = str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S'))
    tweetInfo = request.get_json()
    Username = tweetInfo.get('username')
    tweetText = tweetInfo.get('tweet')

    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO TWEETS (FK_USERS, TWEET, DAY_OF) VALUES(?,?,?)', (Username, tweetText, date))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify(message= Username + tweetText + ' posted'), 201

# 404 error if page not found

@app.errorhandler(404)
def page_not_found(e):
    return '''<h1>404</h1>
<p>The resource could not be found.</p>''', 404


if __name__ == '__main__':
    app.run()
