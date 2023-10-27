from flask import Flask, Response
from requests import ConnectionError
import requests
import json
import re

app = Flask(__name__)

urlStart = 'http://'
robotPORT = ":31950"
contentType = 'application/json'
nodeUrl = 'http://localhost:80/connect'

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
        return Response(json.dumps({'Error': '{error}'.format(error=e)}), status=404, mimetype=contentType)

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
        request = requests.get(nodeUrl)
        if(request.status_code >= 200 and request.status_code < 300):
            result = json.loads(request.text)
            global IP_ADDRESS
            IP_ADDRESS = result["data"]
            match = re.search(r'^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$', result["data"]) #regular expression for IP address
            if(match == None):
                return False
            else:
                return True
        else:
            return False
    except ConnectionError as e:
        print(e)
        return False

@app.route('/')
def home():
    connected = connection_check()
    get_protocols()
    get_runs()
    get_current_run()
    return "Hello from Flask server!" + " Node server is current connected? " +str(connected)
    

# url to use to get list of protocols known to the robot
@app.route('/protocols')
def get_protocols():
    if (connection_check() == True):
        url = urlStart + IP_ADDRESS + robotPORT + "/protocols"
        headers = {"opentrons-version": "2", "Content-Type": contentType} #content type is json is a standard
        request = requests.request("GET", url, headers=headers)
        protocols = json.loads(request.text)
        if(request.status_code == 200):
            set_protocol_list(protocols)
            return protocols
        else:
            return Response(json.dumps({'error': 'No protocols found'}), status=request.status_code, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'Internal Server Error'}), status=500, mimetype=contentType)

#gets json with all runs. the last one should be current if current=true
@app.route('/runs')
def get_runs():
    if(connection_check() == True):
        url = urlStart + IP_ADDRESS + robotPORT + "/runs"
        headers = {"opentrons-version": "2", "Content-Type": contentType}
        request = requests.request("GET", url, headers=headers)
        runs = json.loads(request.text)
        if(request.status_code == 200):
                set_runs_list(runs)
                return runs
        else:
            return Response(json.dumps({'error': 'No runs found'}), status=request.status_code, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'Internal Server Error'}), status=500, mimetype=contentType)

     
#Create a new run with a protocol id
#It returns an id for the run
# url to use when adding a protocol to list of runs to execute OBS: protocolId is the id of the protocol and should be changed if wished for another protocol, e.g. pick_up.py
# test 4cc224a7-f47c-40db-8eef-9f791c689fab
@app.route('/runs/<protocol_id>')
def run(protocol_id):
    if (connection_check() == True):
        get_protocols()
        protocol_list = get_protocol_list()
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

        request = requests.request("POST", url, headers=headers, data=payload)
        if(request.status_code == 201):
            return_string = request.json()["data"]["id"]
            set_current_run(return_string)
            return Response(json.dumps({'message': 'Run created', 'runId': '{return_string}'.format(return_string=return_string)}), status=201, mimetype=contentType)
        else:
            return Response(json.dumps({'error': '{error}'.format(error=request)}), status=request.status_code, mimetype=contentType)
    else:
        return Response(json.dumps({'error': 'Internal Server Error'}), status=500, mimetype=contentType)
    

@app.route('/runStatus/')
def run_status():
     if (connection_check() == True):
        url = urlStart + IP_ADDRESS + robotPORT + "/runs/" + get_current_run()
        headers = {"opentrons-version": "2", "Content-Type": contentType}
        request = requests.request("GET", url, headers=headers)
        if(request.status_code >= 200 and request.status_code < 300):
            status = request.json()["data"]["status"]
            return status
        else:
            return Response(json.dumps({'error': '{error}'.format(error=request)}), status=request.status_code, mimetype=contentType)


# url to use to execute a protocol
@app.route('/execute/')
def run_action():
    if (connection_check() == True):
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
        request = requests.request("POST", url, headers=headers, data=payload)
        if(request.status_code >= 200 and request.status_code < 300):
            return Response(json.dumps({'message': 'To resume a paused protocol, use the following url: http://localhost:5000/execute/'}), status=200, mimetype=contentType)
        else:
            return Response(json.dumps({'error': '{error}'.format(error=request)}), status=request.status_code, mimetype=contentType)

@app.route('/lights')
def lights_status():
    if (connection_check() == True):
        url = urlStart + IP_ADDRESS + robotPORT + "/robot/lights"
        headers = {"opentrons-version": "2", "Content-Type": contentType}
        request = requests.request("GET", url, headers=headers)
        if(request.status_code >= 200 and request.status_code < 300):
            return json.loads(request.text)
        else:
            return Response(json.dumps({'error': 'Something went wrong'}), status=request.status_code, mimetype=contentType)

    else:
        return Response(json.dumps({'error': 'Internal Server Error'}), status=500, mimetype=contentType)

@app.route('/lights/<light_bool>')
def lights(light_bool):
    if(connection_check() == True):
        url = urlStart + IP_ADDRESS + robotPORT + "/robot/lights"
        headers = {"opentrons-version": "2", "Content-Type": contentType}
        payload = {
                    "on": ""
                }
        payload["on"] = light_bool
        payload = json.dumps(payload)
        request = requests.request("POST", url, headers=headers, data=payload)
        if(request.status_code >= 200 and request.status_code < 300):
            if(light_bool == "true"):
                return_string = "Lights are now on"
            else:
                return_string = "Lights are now off"
            return return_string
        else:
            return Response(json.dumps({'error': 'Internal Server Error'}), status=500, mimetype=contentType)

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)