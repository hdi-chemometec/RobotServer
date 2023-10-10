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
This application is a server used for communicating with an Opentrons robot through HTTP API. The Opentrons HTTP APIs can be found atthe robots ip address and add:
portnumber: `31950`
path: `/redoc#tag/Control`

# Getting started

Make sure you have the following installed:

- python 3.7.9
- pip
- Chrome
- Powershell (You can use the one embedded in VS Code)

# Build and run

There's a number of scripts that can be used to build and test the applications. These scripts can be found in the package.json file in the root folder of the project. The most important scripts are listed below:

**Run dev server**
This will start the servers in dev mode. This is the recommended way to start the application during development:
`python app.py`

The server can be accessed at : `http://127.0.0.1:5000` 

# Design

The code tries as best as possible to follow REST principles.

# Code

## Tech stack

The primary tech stack is as follows:

- Python - language
- Flask - server
- Requests - HTTP library for python