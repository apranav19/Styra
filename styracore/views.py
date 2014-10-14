from django.shortcuts import render
from django_twilio.decorators import twilio_view
from twilio import twiml
from bs4 import BeautifulSoup
import requests
import re

DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json?"

@twilio_view
def test_text(request):
	r, reply_msg = twiml.Response(), None
	addresses = get_addresses(request.GET['Body'])

	if len(addresses) == 0:
		r.message("Looks like your message was not formatted correctly")
		return r

	resp = requests.get(DIRECTIONS_URL, params=prepare_request_params(addresses))

	print 'STATUS CODE: ' + str(resp.status_code)

	if resp.status_code != requests.codes.ok:
		reply_msg = "Oops! Something went wrong on our side. Try again."
		r.message(reply_msg)
		return r

	data = resp.json()

	if data['status'] != 'OK':
		reply_msg = "Looks like your addresses are invalid"
		r.message(reply_msg)
		return r

	route = data['routes'][0] # Get the first possible route
	leg = route['legs'][0] # Get the first/default leg
	distance = leg['distance']['text'] # Get the distance for this leg

	
	steps = format_steps(leg['steps'])
	reply_msg = "There are: " + str(len(steps)) + " in this trip\nThe total distance for this trip is: " + distance
	r.message(reply_msg) # Send an overview text
	r.message(("\n").join(steps)) # Send a detailed series of steps
	return r

def get_addresses(msg):
	return re.split(r'[>:;]{1}', msg)

def prepare_request_params(points):
	return {'origin': points[0], 'destination': points[1]}

def format_steps(steps):
	formatted_steps = [str(idx+1) + ")\t" + BeautifulSoup(step['html_instructions']).get_text() for idx, step in enumerate(steps)]
	return formatted_steps