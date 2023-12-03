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
- get the status of the current run and run/resume, 
- pause or stop a run.
"""

urlStart = 'http://'
robotPORT = ":31950"
contentType = 'application/json'
nodeUrl = 'http://localhost:4000/connect' #Node Server url to check IP address

IP_ADDRESS = ""

#List and functions for protocols:
protocolList = []
protocolIds = []

def getProtocolList():
    return protocolList

def setProtocolList(list):
    if(len(list) == 0):
        return Response(json.dumps({'Error': 'No protocols found'}), status=404, mimetype=contentType)
    global protocolList
    protocolList = setProtocolIds(list)
    return protocolList

def getProtocolIds():
    return protocolIds

def setProtocolIds(jsonList):
    global protocolIds
    protocolIds = [] # this is to erase the old ids

    #add all ids of protocols to a list
    try:
        for i in range(len(jsonList["data"])):
            protocolIds.append(jsonList["data"][i]["id"])
            protocolIds.append(jsonList["data"][i]["files"][0]["name"])
        return protocolIds
    except KeyError as e:
        return Response(json.dumps({'Error': '{e}'.format(e=e)}), status=404, mimetype=contentType)

#list of runs and it's functions:
#runsList = []
currentRun = ""

#def getRunsList():
#    return runsList

#def setRunsList(tempRuns):
#    global runsList
#    runsList = tempRuns
#    try:
#        tempCurrentRun = tempRuns["links"]["current"]["href"]
#        tempCurrentRun = tempCurrentRun.split("/runs/")
#        setCurrentRun(tempCurrentRun[1])
#    except KeyError: #this happens if there is no current run
#        setCurrentRun("")

def getCurrentRun():
    return currentRun

def setCurrentRun(tempValue):
    if(tempValue == ""):
        return Response(json.dumps({'error': 'No run found'}), status=404, mimetype=contentType)
    global currentRun
    currentRun = tempValue


def connectionCheck():
    """
    Function to check if the connection to the robot is working by fetching the IP address from the Node server.
    
    It is used by the connect route."""

    try:
        robotRequest = requests.get(nodeUrl)
        if(robotRequest.status_code == 200):
            result = json.loads(robotRequest.text)
            global IP_ADDRESS
            IP_ADDRESS = result["data"]
            match = re.search(r'^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$', result["data"]) #regular expression for IP address
            if(match == None):
                return False #no IP address found
            else:
                return True #IP address found
        else:
            return False #no IP address found
    except ConnectionError:
        return False #error in connection, no IP address found
    except:
        return False #error, no IP address found
    
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

    url = urlStart + IP_ADDRESS + robotPORT + "/protocols"
    headers = {"opentrons-version": "2", "Content-Type": contentType} #content type is json is a standard

    #robotProtocolRequest
    try:
        robotProtocolRequest = requests.request("GET", url, headers=headers)
    except requests.exceptions.InvalidURL:
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)
    protocols = json.loads(robotProtocolRequest.text)

    if(robotProtocolRequest.status_code == 200): #if successful set the protocolList
        setProtocolList(protocols)
        return Response(json.dumps(protocols), status=200, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'No protocols found'}), status=200, mimetype=contentType)

@app.post('/runs')
def post_run():
    """Route to create a run for the robot."""

    getProtocols() #Check if protocol_id exists 
    try:
        tempProtocolList = getProtocolList()
        obj = request.get_data()
        obj = json.loads(obj)
        tempProtocolId = obj['protocol_id']
    except KeyError:
        return Response(json.dumps({'error': 'No id found in body request'}), status=200, mimetype=contentType)
    if(tempProtocolId not in tempProtocolList):
        return Response(json.dumps({'error': 'Protocol not found in protocol list'}), status=200, mimetype=contentType)

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
        returnString = robotRequest.json()["data"]["id"]
        setCurrentRun(returnString)
        return Response(json.dumps({'message': 'Run created', 'runId': '{returnString}'.format(returnString=returnString)}), status=201, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'Run was not created'}), status=200, mimetype=contentType)

@app.get('/runStatus')
def runStatus():
    """Route to get the status of the current run."""

    if(getCurrentRun() == ""):
        return Response(json.dumps({'error': 'No current run'}), status=200, mimetype=contentType)
    url = urlStart + IP_ADDRESS + robotPORT + "/runs/" + getCurrentRun()
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
    url = urlStart + IP_ADDRESS + robotPORT + "/runs/" + getCurrentRun() + "/actions"
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    
    try:
        robotRequest = requests.request("POST", url, headers=headers, data=payload)
    except requests.exceptions.InvalidURL:
        return Response(json.dumps({'error': 'No connection to robot'}), status=200, mimetype=contentType)
    
    if(robotRequest.status_code == 201):
        return Response(json.dumps({'message': 'To resume a paused protocol, use the following url: http://localhost:5000/execute/'}), status=201, mimetype=contentType)
    else:
        return Response(json.dumps({'error': '{error}'.format(error=robotRequest)}), status=200, mimetype=contentType)

### Main ###
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)