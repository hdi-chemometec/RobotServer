from flask import Flask
import requests
import json

app = Flask(__name__)

robotURL = "http://169.254.85.139:31950"
contentType = 'application/json'
ErrorMessage = "Something went wrong! Status code: "

@app.route('/')
def home():
    return "Hello World!"

# url to use to get list of protocols known to the robot
@app.route('/protocols')
def get_protocols():
    url = robotURL + "/protocols"
    headers = {"opentrons-version": "2", "Content-Type": contentType} #content type is json is a standard
    response = requests.request("GET", url, headers=headers)
    protocols = json.loads(response.text)
    if(response.status_code >= 200 and response.status_code < 300):
        return protocols
    else:
        return_string = ErrorMessage + str(response.status_code)
        return return_string

# url to use when adding a protocol to list? of runs to execute OBS: protocolId is the id of the protocol and should be changed if wished for another protocol
@app.route('/run/<protocol_id>')
def run(protocol_id):
    url = robotURL + "/runs"
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

    response = requests.request("POST", url, headers=headers, data=payload)
    if(response.status_code >= 200 and response.status_code < 300):
        protocol_id = response.json()["data"]["id"]
        return_string = "Your run has the id: " + protocol_id
        return return_string
    else:
        return_string = ErrorMessage + str(response.status_code)
        return return_string

# url to use to execute a protocol
@app.route('/run/<protocol_id>/actions')
def run_action(protocol_id):
    url = robotURL + "/runs/" + protocol_id + "/actions"
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    payload = {
                "data": {
                    "actionType": "play" 
                }
            }
    payload = json.dumps(payload)
    request = requests.request("POST", url, headers=headers, data=payload)
    if(request.status_code >= 200 and request.status_code < 300):
        return_string = "To resume a paused protocol, use the following url: http://localhost:5000/resume/" + protocol_id
        return return_string
    else:
        return_string = ErrorMessage + str(request.status_code)
        return return_string

# url to use to resume a protocol that is paused
@app.route('/resume/<run_id>')
def resume(run_id):
    run_action(run_id)
    return_string = "The protocol has been resumed. If the run is paused again, use the following url: http://localhost:5000/resume/" + run_id + " to resume"
    return return_string

@app.route('/lights')
def lights_status():
    url = robotURL + "/robot/lights"
    headers = {"opentrons-version": "2", "Content-Type": contentType}
    response = requests.request("GET", url, headers=headers)
    if(response.status_code >= 200 and response.status_code < 300):
        return json.loads(response.text)
    else:
        return_string = ErrorMessage + str(response.status_code)
        return return_string

@app.route('/lights/<light_bool>')
def lights(light_bool):
    url = robotURL + "/robot/lights"
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
        return_string = ErrorMessage + str(request.status_code)
        return return_string

if __name__ == '__main__':
    app.run(debug=True)