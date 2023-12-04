from flask import Flask, Response, request
from flask_cors import CORS
from requests import ConnectionError
import requests
import json
import re #regular expression

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

def connectionCheck():
    """
    Function to check if the connection to the robot is working by fetching the IP address from the Node server.
    It is used by the \connect endpoint."""

    try:
        robotRequest = requests.get(nodeUrl)
        if(robotRequest.status_code == 200):
            result = json.loads(robotRequest.text)
            IP_ADDRESS = result["data"]
            match = re.search(r'^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$', result["data"]) #regular expression for IP address
            if(match == None):
                return "False"
            else:
                return IP_ADDRESS #IP address found
        else:
            return "False"
    except ConnectionError:
        return "False"
    except:
        return "False"
    
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
    return Response('{connected}'.format(connected=connected), status=200, mimetype=contentType)

# url to use to get list of protocols known to the robot
@app.get('/protocols')
def getProtocols():
    """Route to get list of protocols known to the robot."""

    IP_ADDRESS = connectionCheck()
    if(IP_ADDRESS == "False"):
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)

    url = urlStart + IP_ADDRESS + robotPORT + "/protocols"
    headers = {"opentrons-version": "2", "Content-Type": contentType}

    #robotProtocolRequest
    try:
        robotProtocolRequest = requests.request("GET", url, headers=headers)
    except requests.exceptions.InvalidURL:
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)
    protocols = json.loads(robotProtocolRequest.text)

    if(robotProtocolRequest.status_code == 200):
        return Response(json.dumps(protocols), status=200, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'No protocols found'}), status=200, mimetype=contentType)

@app.post('/runs')
def post_run():
    """Route to create a run for the robot."""
    IP_ADDRESS = connectionCheck()
    if(IP_ADDRESS == "False"):
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)

    try:
        obj = request.get_data()
        obj = json.loads(obj)
        tempProtocolId = obj['protocol_id']
    except KeyError:
        return Response(json.dumps({'error': 'No id found in body request'}), status=200, mimetype=contentType)

    url = urlStart + IP_ADDRESS + robotPORT + "/runs"
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    payload = {
        "data": {
            "protocolId": "",
            "labwareOffsets": [
                {
                    "definitionUri": "opentrons/opentrons_96_tiprack_300ul/1",
                    "location": {
                        "slotName": "1"
                },
                "vector": {
                    "x": 0.29999999999999893,
                    "y": 0.9000000000000057,
                    "z": 0.0
                    }
                }
            ]
        }
    }
    payload["data"]["protocolId"] = tempProtocolId
    payload = json.dumps(payload)

    try:
        robotRequest = requests.request("POST", url, headers=headers, data=payload)
    except requests.exceptions.InvalidURL:
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)
    
    if(robotRequest.status_code == 201):
        createdRunId = robotRequest.json()["data"]["id"]
        return Response(json.dumps({'message': 'Run created', 'runId': '{createdRunId}'.format(createdRunId=createdRunId)}), status=201, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'Run was not created'}), status=200, mimetype=contentType)

@app.get('/currentRun')
def getCurrentRun():
    """Route to get the current run id"""
    IP_ADDRESS = connectionCheck()
    if(IP_ADDRESS == "False"):
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)

    url = urlStart + IP_ADDRESS + robotPORT + "/runs"
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    protocolRequest = requests.request("GET", url, headers=headers )

    if(protocolRequest.status_code == 200):
        protocolRequest = protocolRequest.json()
    else:
        return Response(json.dumps({'error': 'No runs found'}), status=200, mimetype=contentType)

    try:
        tempCurrentRun = protocolRequest["links"]["current"]["href"]
        tempCurrentRun = tempCurrentRun.split("/runs/")
        currentRun = tempCurrentRun[1]
    except KeyError: #this happens if there is no current run
        currentRun = ""

    return Response(json.dumps(currentRun), status=200, mimetype=contentType)

@app.get('/runStatus')
def runStatus():
    """Route to get the status of the current run."""
    IP_ADDRESS = connectionCheck()
    if(IP_ADDRESS == "False"):
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)

    currentRunRequest = getCurrentRun()
    if(currentRunRequest.status_code == 200):
        currentRun = currentRunRequest.json
        if(currentRun == ""):
            return Response(json.dumps({'error': 'No current run'}), status=200, mimetype=contentType)

    url = urlStart + IP_ADDRESS + robotPORT + "/runs/" + currentRun
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    
    try:
        robotRequest = requests.request("GET", url, headers=headers)
    except requests.exceptions.InvalidURL:
        return Response(json.dumps({'error': 'No IP to robot found'}), status=200, mimetype=contentType)
    except requests.exceptions.ConnectionError:
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)

    if(robotRequest.status_code == 200):
        try:
            status = robotRequest.json()["data"]["status"]
            return Response(status, status=200, mimetype=contentType)
        except KeyError:
            return Response(json.dumps({'error': 'No current run'}), status=200, mimetype=contentType)
    else:
        return Response(json.dumps({'error': '{error}'.format(error=robotRequest)}), status=200, mimetype=contentType)

#this command is used to run/resume, pause or stop a run
@app.post('/command')
def runAction():
    """Route to run/resume, pause or stop a run."""
    IP_ADDRESS = connectionCheck()
    if(IP_ADDRESS == "False"):
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)

    try:
        obj = request.get_data()
        obj = json.loads(obj)
        command = obj['command']
    except KeyError:
        return Response(json.dumps({'error': 'No command found'}), status=200, mimetype=contentType)
    except requests.exceptions.ConnectionError:
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)

    if(runStatus() == "succeeded" or runStatus() == "stopped"):
        return Response(json.dumps({'error': 'Run has already been executed'}), status=200, mimetype=contentType)

    if(command == "play"):
        payload = {
            "data": {
                "actionType": "play" 
            }
        }
    elif(command == 'pause'):
        payload = {
            "data": {
                "actionType": "pause" 
            }
        }
    else:
        payload = {
            "data": {
                "actionType": "stop" 
            }
        }
    payload = json.dumps(payload)

    currentRunRequest = getCurrentRun()
    if(currentRunRequest.status_code == 200):
        currentRun = currentRunRequest.json
        if(currentRun == ""):
            return Response(json.dumps({'error': 'No current run'}), status=200, mimetype=contentType)

    url = urlStart + IP_ADDRESS + robotPORT + "/runs/" + currentRun + "/actions"
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    
    try:
        robotRequest = requests.request("POST", url, headers=headers, data=payload)
    except requests.exceptions.InvalidURL:
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)
    
    if(robotRequest.status_code == 201):
        return Response(json.dumps({'message': '{command}'.format(command=command)}), status=201, mimetype=contentType)
    else:
        return Response(json.dumps({'error': '{error}'.format(error=robotRequest.reason)}), status=200, mimetype=contentType)

### Main ###
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)