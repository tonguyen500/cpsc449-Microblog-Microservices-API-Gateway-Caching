#CPSC 449 Project 2
#MicroBlogging service
#Jose Alvarado, Luan Nguyen, Sagar Joshi

import flask
from flask import Flask, request, jsonify, g, current_app, make_response, Response, abort
import sqlite3, time, datetime
from flask_caching import Cache
from operator import itemgetter
from datetime import datetime, date, timedelta
from flask.logging import create_logger
import logging
from logging.handlers import RotatingFileHandler


DATABASE = 'data.db'

app = Flask(__name__)
app.config.from_object(__name__)
app.config["DEBUG"]= True
app.config['CACHE_DEFAULT_TIMEOUT']=300

cache = Cache(app)

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

    if 'If-Modified-Since' in request.headers:
        date_time_obj = datetime.datetime.strptime(request.headers['If-Modified-Since'], '%a, %d %b %Y %H:%M:%S %Z')
        if (datetime.datetime.now() - date_time_obj).seconds < 300:
            return Response(status=304)

        else:
            conn = sqlite3.connect('data.db')
            conn.row_factory = dict_factory
            cur = conn.cursor()
            recentTweets = cur.execute('SELECT * FROM TWEETS ORDER BY DAY_OF DESC LIMIT 25').fetchall()
            res = make_response(jsonify(recentTweets))
            unix = time.time()
            date = str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S.%f'))

            res.headers.add('Last-Modified', datetime.now())
            res.last_modified = datetime.datetime.now()

            return res
    else:
        conn = sqlite3.connect('data.db')
        conn.row_factory = dict_factory
        cur = conn.cursor()
        recentTweets = cur.execute('SELECT * FROM TWEETS ORDER BY DAY_OF DESC LIMIT 25').fetchall()
        res = make_response(jsonify(recentTweets))
        unix = time.time()
        date = str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S.%f'))

        res.last_modified = datetime.datetime.now()

        return res

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

    is_following_list = []

    homeTimeLine = []
    for each in is_following_list:
        tweetList = list(Username=each)
        cache.set(each, tweetList)
        app.logger.debug(f"homeTimeLine data from db user: {each}") #Method logger has no debug member
    else:
        app.logger.debug(f"homeTimeLine data from cache user: {each}")  #Method logger has no debug member
        homeTimeLine.extend(cache.get(each))
    sortedTimeLine = sorted(homeTimeLine, key=itemgetter('dateto'), reverse=True)
    rsp = Response(jsonify(homeTweets))
    rsp.headers.add('Last-Modified', datetime.now())
    return rsp, 201


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
    if Username is None or tweetText(Username):
        abort(400) #no username or content attached or user does NOT exist

    return jsonify(message= Username + tweetText + ' posted'), 201

# @app.after_request
# def add_headers(resp):
#     resp.headers['Last-Modified']
#     return resp
# 404 error if page not found

@app.errorhandler(404)
def page_not_found(e):
    return '''<h1>404</h1>
<p>The resource could not be found.</p>''', 404


if __name__ == '__main__':
    app.run()
