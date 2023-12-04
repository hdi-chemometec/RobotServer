from flask import Flask, Response, request
from flask_cors import CORS
from requests import ConnectionError
import requests
import json
import re #regular expression

from src.functions import connectionCheck, getProtocols, getRuns, postRun, getCurrentRun, getRunStatus, postRunAction

app = Flask(__name__)
CORS(app)

"""
This is a REST API to communicate with the Opentrons robot.

The API is used for:
- to get a list of protocols known to the robot, 
- create a run for the robot, 
- get the current run id,
- get the status of the current run,
- pause or stop a run.
"""

urlStart = 'http://'
robotPORT = ":31950"
contentType = 'application/json'
nodeUrl = 'http://localhost:4000/connect' #Node Server url to check IP address

    
### ROUTES ###

@app.route('/')
def home():
    """Start page for REST API.
    It is used by the Node server to check if Python server is running."""
    
    return Response('Flask server is connected!', status=200, mimetype=contentType)

@app.route('/connect')
def connect():
    """Route to check if the robot is running and if it's IP address is known."""

    connected = connectionCheck()
    return Response(json.dumps(connected), status=200, mimetype=contentType)

# url to use to get list of protocols known to the robot
@app.get('/protocols')
def getProtocolsResponse():
    protocols = getProtocols()
    return Response(json.dumps(protocols), status=200, mimetype=contentType)


@app.get('/runs')
def getRunsResponse():
    runs = getRuns()
    return Response(json.dumps(runs), status=200, mimetype=contentType)

@app.post('/runs')
def postRunResponse():
    response = postRun()
    return response

@app.get('/currentRun')
def getCurrentRunResponse():
    currentRun = getCurrentRun()
    return Response(json.dumps(currentRun), status=200, mimetype=contentType)

@app.get('/runStatus')
def getRunStatusResponse():
    status = getRunStatus()
    return Response(json.dumps(status), status=200, mimetype=contentType)

#this command is used to run/resume, pause or stop a run
@app.post('/command')
def postRunActionResponse():
    response = postRunAction()
    return response

### Main ###
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)