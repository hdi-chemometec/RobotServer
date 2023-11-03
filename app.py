from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from requests import ConnectionError
import requests
import json
import re

app = Flask(__name__)
CORS(app)

urlStart = 'http://'
robotPORT = ":31950"
contentType = 'application/json'
nodeUrl = 'http://localhost:4000/connect'

IP_ADDRESS = ""

#List and functions for protocols:
protocol_list = []
protocol_ids = []

def get_protocol_list():
    return protocol_list

def set_protocol_list(list):
    if(len(list) == 0):
        return Response(json.dumps({'Error': 'No protocols found'}), status=404, mimetype=contentType)
    global protocol_list
    protocol_list = set_protocol_ids(list)
    return protocol_list

def set_protocol_ids(json_list):
    global protocol_ids
    protocol_ids = []
    #add all ids of protocols to a list
    try:
        for i in range(len(json_list["data"])):
            protocol_ids.append(json_list["data"][i]["id"])
            protocol_ids.append(json_list["data"][i]["files"][0]["name"])
        return protocol_ids
    except KeyError as e:
        return Response(json.dumps({'Error': '{e}'.format(e=e)}), status=404, mimetype=contentType)

def get_protocol_ids():
    return protocol_ids


#list of runs and it's functions:
runs_list = []
current_run = ""

def get_runs_list():
    return runs_list

def set_runs_list(temp_runs):
    global runs_list
    runs_list = temp_runs
    global current_run
    try:
        current_run = temp_runs["links"]["current"]["href"]
        current_run = current_run.split("/runs/")
        current_run = current_run[1]
    except KeyError: #this happens if there is no current run
        current_run = ""

def get_current_run():
    return current_run

def set_current_run(temp_value):
    if(temp_value == ""):
        return Response(json.dumps({'error': 'No run found'}), status=404, mimetype=contentType)
    global current_run
    current_run = temp_value


# function to check if the connection to the robot is working and Node server is running
def connection_check():
    try:
        robot_request = requests.get(nodeUrl)
        if(robot_request.status_code == 200):
            result = json.loads(robot_request.text)
            global IP_ADDRESS
            IP_ADDRESS = result["data"]
            match = re.search(r'^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$', result["data"]) #regular expression for IP address
            if(match == None):
                print("No IP address found")
                return False
            else:
                print("IP address found" + IP_ADDRESS)
                return True
        else:
            print("No IP address found")
            return False
    except ConnectionError as e:
        print(e + "error in connection_check")
        return False

@app.route('/')
def home():
    return Response('Flask server is connected!', status=200, mimetype=contentType)

@app.route('/connect')
def connect():
    connected = connection_check()
    return Response('{connected}'.format(connected=connected), status=200, mimetype=contentType)

@app.get('/lights')
def get_lights():
    url = urlStart + IP_ADDRESS + robotPORT + "/robot/lights"
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    robot_request = requests.request("GET", url, headers=headers)
    if(robot_request.status_code == 200):
        return Response(json.dumps({'light': json.loads(robot_request.text)}), status=200, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'Something went wrong'}), status=robot_request.status_code, mimetype=contentType)

@app.post('/lights')
def post_light():
    try:
        obj = request.get_data()
        obj = json.loads(obj)
        light_bool = obj['light']
    except KeyError:
        return Response(json.dumps({'error': 'No key found'}), status=404, mimetype=contentType)
    url = urlStart + IP_ADDRESS + robotPORT + "/robot/lights"
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    payload = {
                "on": ""
            }
    payload["on"] = light_bool
    payload = json.dumps(payload)
    robot_request = requests.request("POST", url, headers=headers, data=payload)
    if(robot_request.status_code == 200):
        return Response(json.dumps({'light': json.loads(robot_request.text)}), status=200, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'Internal Server Error'}), status=500, mimetype=contentType)

# url to use to get list of protocols known to the robot
@app.get('/protocols')
def get_protocols():
    url = urlStart + IP_ADDRESS + robotPORT + "/protocols"
    headers = {"opentrons-version": "2", "Content-Type": contentType} #content type is json is a standard
    robot_request = requests.request("GET", url, headers=headers)
    protocols = json.loads(robot_request.text)
    if(robot_request.status_code == 200):
        set_protocol_list(protocols)
        return Response(json.dumps(protocols), status=200, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'No protocols found'}), status=robot_request.status_code, mimetype=contentType)

#gets json with all runs. the last one should be current if current=true
@app.get('/runs')
def get_runs():
    url = urlStart + IP_ADDRESS + robotPORT + "/runs"
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    robot_request = requests.request("GET", url, headers=headers)
    runs = json.loads(robot_request.text)
    if(robot_request.status_code == 200):
            set_runs_list(runs)
            return Response(json.dumps(runs), status=200, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'No runs found'}), status=robot_request.status_code, mimetype=contentType)

@app.post('/runs')
def post_run():
    get_protocols()
    try:
        protocol_list = get_protocol_list()
        obj = request.get_data()
        obj = json.loads(obj)
        protocol_id = obj['protocol_id']
    except KeyError:
        return Response(json.dumps({'error': 'No protocol with that id found'}), status=404, mimetype=contentType)
    if(protocol_id not in protocol_list):
        return Response(json.dumps({'error': 'Protocol not found'}), status=404, mimetype=contentType)
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
    payload["data"]["protocolId"] = protocol_id
    payload = json.dumps(payload)

    robot_request = requests.request("POST", url, headers=headers, data=payload)
    if(robot_request.status_code == 201):
        return_string = robot_request.json()["data"]["id"]
        set_current_run(return_string)
        return Response(json.dumps({'message': 'Run created', 'runId': '{return_string}'.format(return_string=return_string)}), status=201, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'Run was not created'}), status=robot_request.status_code, mimetype=contentType)
    

@app.get('/runStatus')
def run_status():
    if(get_current_run() == ""):
        return Response(json.dumps({'error': 'No current run'}), status=404, mimetype=contentType)
    url = urlStart + IP_ADDRESS + robotPORT + "/runs/" + get_current_run()
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    robot_request = requests.request("GET", url, headers=headers)
    if(robot_request.status_code == 200):
        try:
            status = robot_request.json()["data"]["status"]
        except KeyError:
            return Response(json.dumps({'error': 'No current run'}), status=404, mimetype=contentType)
        return Response(status, status=200, mimetype=contentType)
    else:
        return Response(json.dumps({'error': '{error}'.format(error=robot_request)}), status=robot_request.status_code, mimetype=contentType)

@app.post('/execute')
def run_action():
    if(run_status() == "succeeded" or run_status() == "stopped"):
        return Response(json.dumps({'error': 'Run has already been executed'}), status=403, mimetype=contentType)
    url = urlStart + IP_ADDRESS + robotPORT + "/runs/" + get_current_run() + "/actions"
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    payload = {
                "data": {
                    "actionType": "play" 
                }
            }
    payload = json.dumps(payload)
    robot_request = requests.request("POST", url, headers=headers, data=payload)
    if(robot_request.status_code == 201):
        return Response(json.dumps({'message': 'To resume a paused protocol, use the following url: http://localhost:5000/execute/'}), status=201, mimetype=contentType)
    else:
        return Response(json.dumps({'error': '{error}'.format(error=robot_request)}), status=robot_request.status_code, mimetype=contentType)

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)