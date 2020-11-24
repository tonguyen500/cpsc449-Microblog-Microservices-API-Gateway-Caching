#foreman start -m gateway=1,users=3,timeline=3,auth=1
gateway:env FLASK_APP=gateway flask run -p $PORT              #starts the gateway service which allows other services to run on port 5000
users: env FLASK_APP=user_api.py flask run -p $PORT           #starts the users service which deals with all the user api calls on port 5100
timeline: env FLASK_APP=timeline_api.py flask run -p $PORT    #starts the timeline service which deals with all the timeline api calls on port 5200
auth: env FLASK_APP=user_api.py flask run -p $PORT            #starts a service for authorization so that it has its own service and wont need one of the others on port 5300
