#
# Simple API gateway in Python
#
# Inspired by <https://github.com/vishnuvardhan-kumar/loadbalancer.py>
#
#   $ python3 -m pip install Flask python-dotenv
#

import sys

import flask
import requests
from flask_basicauth import BasicAuth

from collections import deque

class ModifiableCycle(object):
    def __init__(self, items=()):
        self.deque = deque(items)
    def __iter__(self):
        return self
    def __next__(self):
        if not self.deque:
            raise StopIteration
        item = self.deque.popleft()
        self.deque.append(item)
        return item
    next = __next__

    def delete_prev(self):

        self.deque.pop()


app = flask.Flask(__name__)
app.config.from_envvar('APP_CONFIG')

upstream = app.config['UPSTREAM']   #variable to hold general gateway route

user = app.config['USER_0']     #variable to hold route for first user
user2 = app.config['USER_1']    #variable to hold route for second user
user3 = app.config['USER_2']    #variable to hold route for third user

timeline = app.config['TIMELINES_0']    #variable to hold route for first timeline
timeline2 = app.config['TIMELINES_1']   #variable to hold route for second timeline
timeline3 = app.config['TIMELINES_2']   #variable to hold route for third timeline

auth = app.config['AUTH']  #holds unique route used for authentication

user_endpoints = ['/users/all', '/login', '/register', '/follow', 'unfollow']  #list holding endpoints for user api
timeline_endpoints = ['/homeTimeline', '/publicTimeline', '/postTweet', '/userTimeline']    #list holding endpoints for timeline api

player = [user, user2, user3]                   #list holding the variables with user routes
player2 = [timeline, timeline2, timeline3]      #list holding the variables with timeline routes


user_routes = ModifiableCycle(player)           #used to cycle through the list of user routes
timeline_routes = ModifiableCycle(player2)      #used to cycle through the list of timeline routes

#used to set the input values used for username and password for baisc auth
def credentials(self, username, password):
    r = requests.post(auth + '/login', json={'username': username, 'password': password})
    if r.status_code == 200 or r.status_code == 201:
        return True
    return False

#setting the check credentials equal to what was input
BasicAuth.check_credentials = credentials

basic_auth = BasicAuth(app)

@app.errorhandler(404)
@basic_auth.required
def route_page(err):
    # route = "something"
    try:
        #used for cycling through user routes in round robin style
        for str in user_endpoints:
            if str in flask.request.full_path:
                route = user_routes.__next__()

        #used for cycling through user routes in round robin style
        for str in timeline_endpoints:
            if str in flask.request.full_path:
                route = timeline_routes.__next__()

        response = requests.request(
            flask.request.method,
            route + flask.request.full_path,
            data=flask.request.get_data(),
            headers=flask.request.headers,
            cookies=flask.request.cookies,
            stream=True,
        )
    except requests.exceptions.RequestException as e:
        app.log_exception(sys.exc_info())
        return flask.json.jsonify({
            'method': e.request.method,
            'url': e.request.url,
            'exception': type(e).__name__,
        }), 503

    #if request fails with status code in 500 range then it is removed from circulation
    else:
        if response.status_code >= 500:
            for item in player:
                if item == route:
                    user_routes.delete_prev()
            for item in player2:
                if item == route:
                    timeline_routes.delete_prev()


    headers = remove_item(
        response.headers,
        'Transfer-Encoding',
        'chunked'
    )

    return flask.Response(
        response=response.content,
        status=response.status_code,
        headers=headers,
        direct_passthrough=True,
    )


def remove_item(d, k, v):
    if k in d:
        if d[k].casefold() == v.casefold():
            del d[k]
    return dict(d)
