#CPSC 449 Project 2
#MicroBlogging service
#Jose Alvarado, Luan Nguyen, Sagar Joshi

import flask
from flask import request, jsonify, g, current_app
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


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
<p>Users microservice</p>'''


#outputs all currently registered users


@app.route('/users/all', methods=['GET'])
def api_all():
    conn = sqlite3.connect('data.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_users = cur.execute('SELECT * FROM USERS').fetchall()

    return jsonify(all_users)


#outputs who a user is following


@app.route('/following', methods=['GET'])
def follow_all():
    userInfo = request.get_json()
    username = userInfo.get('username')

    conn = sqlite3.connect('data.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    follow_users = cur.execute('SELECT * FROM FOLLOW WHERE FK_USER =?', (username)).fetchall()

    return jsonify(follow_users)


#createUser(username, email, password)
#Registers a new user account.


@app.route('/register', methods=['POST'])
def createUser():
    userInfo = request.get_json()
    Username = userInfo.get('username')
    Email = userInfo.get('email')
    password = userInfo.get('password')
    hashed_password = generate_password_hash(password)

    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO USERS VALUES(?,?,?)', (Username, Email, hashed_password))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify(message=Username + ' was added successfully.'), 201


#authenticateUser(username, password)
#Returns true if the supplied password matches the hashed password stored for that username in the database.


@app.route('/login', methods=['POST'])
def authenticateUser():
    userInfo = request.get_json()
    Username = userInfo.get('username')
    password = userInfo.get('password')

    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    userPass = cur.execute('SELECT PASSWORD FROM USERS WHERE PK_USERNAME = ?', [Username]).fetchone()[0]

    if check_password_hash(userPass, password):
        return jsonify(message=Username + ' was authenticated successfully.'), 201
    else:
        return jsonify(message=Username + ' password incorrect' ), 401


#addFollower(username, usernameToFollow)
#Start following a new user.


@app.route('/follow', methods=['PUT'])
def addFollower():
    userInfo = request.get_json()
    username = userInfo.get('username')
    usernameToFollow = userInfo.get('usernameToFollow')

    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO FOLLOW (FOLLOWERS, FK_USER) VALUES(?,?)',(usernameToFollow, username))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify(message=username + ' is now following ' + usernameToFollow), 200


#removeFollower(username, usernameToRemove)
#Stop following a user.


@app.route('/unfollow', methods=['POST'])
def removeFollower():
    userInfo = request.get_json()
    username = userInfo.get('username')
    usernameToRemove = userInfo.get('usernameToRemove')

    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM FOLLOW WHERE FK_USER = ? AND FOLLOWERS = ?',(username, usernameToRemove))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify(message=username + ' is now unfollowing ' + usernameToRemove), 200

# 404 error if page not found

@app.errorhandler(404)
def page_not_found(e):
    return '''<h1>404</h1>
<p>The resource could not be found.</p>''', 404


if __name__ == '__main__':
    app.run()
