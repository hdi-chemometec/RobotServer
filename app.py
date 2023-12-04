from flask import Flask, Response
from flask_cors import CORS
import json

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

contentType = 'application/json'


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

@app.get('/protocols')
def getProtocolsResponse():
    protocols = getProtocols()
    if isinstance(protocols, dict):
        return Response(json.dumps(protocols), status=200, mimetype=contentType)
    else:
        return protocols

@app.get('/runs')
def getRunsResponse():
    runs = getRuns()
    if isinstance(runs, dict):
        return Response(json.dumps(runs), status=200, mimetype=contentType)
    else:
        return runs

@app.post('/runs')
def postRunResponse():
    response = postRun()
    return response

@app.get('/currentRun')
def getCurrentRunResponse():
    currentRun = getCurrentRun()
    if isinstance(currentRun, str):
        return Response(json.dumps(currentRun), status=200, mimetype=contentType)
    else:
        currentRun

@app.get('/runStatus')
def getRunStatusResponse():
    status = getRunStatus()
    if isinstance(status, dict):
        return Response(json.dumps(status), status=200, mimetype=contentType)
    else:
        return status

@app.post('/command')
def postRunActionResponse():
    response = postRunAction()
    return response

### Main ###
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)