#CPSC 449 Project 2
#MicroBlogging service
#Jose Alvarado, Luan Nguyen, Sagar Joshi

import flask
from flask import Flask, request, jsonify, g, current_app, make_response, Response, abort, json
import sqlite3, time, datetime
from werkzeug.exceptions import HTTPException, default_exceptions,  Aborter
from flask_caching import Cache
from operator import itemgetter
from datetime import datetime, date, timedelta
from flask.logging import create_logger
import logging
from logging.handlers import RotatingFileHandler

DATABASE = 'data.db'
DEBUG = True

class NotModified(HTTPException):
    code = 304
    description = '<p>Page not modified</p>'

default_exceptions[304] = NotModified
abort = Aborter()
cache = Cache(config={'CACHE_TYPE': 'simple','CACHE_DEFAULT_TIMEOUT': 300})

app = Flask(__name__)
app.config.from_object(__name__)
app.config["DEBUG"]= True
app.config["CACHE_TYPE": "simple"
# app.config['CACHE_DEFAULT_TIMEOUT']=300
#
cache = Cache(app)
# cache.init_app(app)

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

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

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
        date_time_obj = datetime.strptime(request.headers['If-Modified-Since'], '%a, %d %b %Y %H:%M:%S %Z')
        if (datetime.now() - date_time_obj).seconds < 3:
            return Response(status=304)
            #abort(make_response(jsonify(message='Page not modified'), 304))

        else:
            conn = sqlite3.connect('data.db')
            conn.row_factory = dict_factory
            cur = conn.cursor()
            recentTweets = cur.execute('SELECT * FROM TWEETS ORDER BY DAY_OF DESC LIMIT 25').fetchall()
            res = make_response(jsonify(recentTweets))
            unix = time.time()
            date = str(datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S'))

            res.last_modified = datetime.now()

            return res
    else:
        conn = sqlite3.connect('data.db')
        conn.row_factory = dict_factory
        cur = conn.cursor()
        recentTweets = cur.execute('SELECT * FROM TWEETS ORDER BY DAY_OF DESC LIMIT 25').fetchall()
        res = make_response(jsonify(recentTweets))
        unix = time.time()
        date = str(datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S'))

        res.last_modified = datetime.now()

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

    is_following_list = []
    #homeTweets = cur.execute('SELECT TWEET, DAY_OF, FK_USERS FROM TWEETS INNER JOIN FOLLOW ON FOLLOW.FOLLOWERS = TWEETS.FK_USERS WHERE FOLLOW.FK_USER = ? ORDER BY DAY_OF DESC LIMIT 25', (Username)).fetchall()
    
    # returns a list of users following a username
    for user in query_db('SELECT FOLLOWERS FROM FOLLOW WHERE FK_USER = ?', Username):
        if user['FOLLOWERS'] not in is_following_list:
             is_following_list.append((user['FOLLOWERS']))


    #for extracting users information into list form
    homeTimeline = []
    for each in is_following_list:
        if (cache.get(each) == None):
            tweetList = query_db('SELECT * FROM TWEETS WHERE FK_USERS = ? ORDER BY DAY_OF DESC LIMIT 25', each)
            cache.set(each, tweetList)
            app.logger.debug(f"homeTimeLine data from db user:") #Method logger has no debug member
        else:
            app.logger.debug(f"homeTimeLine data from cache user:")
            homeTimeline.extend(cache.get(each))
    res = Response(jsonify(homeTimeline), content_type='application/json')
    res.headers.add('Last-Modified', datetime.now())
    return res
    # return jsonify(homeTweets), 201


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


# @app.after_request
# def add_headers(resp):
#     resp.headers['Last-Modified']
#     return resp
# 404 error if page not found
@app.errorhandler(304)
def page_not_found(e):
    return e, 304

@app.route('/debug')
def debug():
    abort(304)

@app.errorhandler(404)
def page_not_found(e):
    return '''<h1>404</h1>
<p>The resource could not be found.</p>''', 404

#if __name__ == '__main__':
#    app.run()

# Professor's comments:
# 1. The correct response code for HTTP caching is 304, not 340. There should be no payload. 
# 2. The work you're doing with the object cache is useless because you've already run the JOIN statement. 
# a) You shouldn't be running a JOIN statement at all in getHomeTimeline(); you'll only ever be doing the individual queries against FOLLOWERS and TWEETS.
# b) The queries against TWEETS should be skipped if the values are already in cache.
#