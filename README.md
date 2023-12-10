# Robot Flask Server

<!-- TOC -->

- [Robot Flask Server](#robot-flask-server)
- [Introduction](#introduction)
- [Getting started](#getting-started)
- [Build and run](#build-and-run)
- [Design](#design)
- [Code](#code)
  - [Tech stack](#tech-stack)

<!-- /TOC -->
<!-- /TOC -->

# Introduction
This application is a server used for communicating with an Opentrons robot through a REST API. The Opentrons REST API documentation can be found at the robot's ip address and add:
portnumber: `31950`
path: `/redoc`

An example: `http://169.254.189.20:31950/redoc`
# Getting started

Make sure you have the following installed:

- python 3.7.9
- pip 20.1.1
- Visual Studio Code
- Chrome
- Powershell (You can use the one embedded in VS Code)

# Build and run

**Install packages**

Before running the project the following packages must be installed with pip:
- `pip install flask`
- `pip install flask_cors`
- `pip install requests`

**Run server**

This will start the server:

`python app.py`

The server can be accessed at : `http://127.0.0.1:5000` 

# Design

The code tries as best as possible to follow REST principles. 
The REST endpoints and main function are located in `app.py`.
The functions used by the endpoints are located in `src/functions.py` folder.
By putting the functions into it's own folder, then the other endpoints can make
use of them and only return a response that is relevant to that endpoint.

# Code

## Tech stack

The primary tech stack is as follows:

- Python - language
- pip - package manager
- Flask - server
- Requests - HTTP library for python