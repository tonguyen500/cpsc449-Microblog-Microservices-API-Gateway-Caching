cpsc-449 Project 4: API Gateway
Jose Alvarado, Sagar Joshi, Luan Nguyen


## Overview
This project uses the two services that were created in project two and addresses three major problems that it has.
The problems being:
    1. Each service is on a different port (and in production, on a different host)
    2. There is only one instance of each service
    3. While there is an API call to do authentication, none of the other calls are actually authenticated.

These problems are solved by creating an api gateway that wil mediate between users and the services. The gateway 
functions as a reverse proxy, listening on port 5000 and routing all requests to correct microservice needed.
Load balancing is used by starting the gateway with three instances of each microservice and cycling through them
using a round robin method, and if a request fails the server is removed from rotationn.
Authentication is done by using the Flask-BasicAuth extension.

To test with httpie a command should look like
    $ http -a USERNAME:PASSWORD POST http://127.0.0.1:5000/login username=USERNAME password=PASSWORD
    where USERNAME and PASSWORD exist within the database

The files included for submission are:
    The Python source code for gateway and the two microservices (user_api.py, timeline_api.py)
        to start the services run:
            $ foreman start -m gateway=1,users=3,timeline=3,auth=1
    The routes.cfg file containing the routes for the services
    Procfile definitions for each service
    A sql schema file that can be used for the creation of a database if needed
        create with commands:
            $ export FLASK_APP=user_api.py
            $ flask init
        before running foreman start -m gateway=1,users=3,timeline=3,auth=1

No changes were made to the microservice files from project two 
