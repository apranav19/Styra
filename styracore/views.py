from django.shortcuts import render
from django_twilio.decorators import twilio_view
from styracore.models import StyraUser, Route, Instruction
from twilio import twiml
from bs4 import BeautifulSoup
import requests
import re
import time

DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json?"
ACCEPTABLE_MODES = set(['driving', 'walking', 'bicycling', 'transit'])

def get_stats(user_phone_number):
	reply_msg = None
	current_user = StyraUser.objects.filter(phone_number=user_phone_number)[0]
	current_user_routes = Route.objects.filter(styra_user=current_user)

	if len(current_user_routes) > 0:
		total_distance = get_total_distance(current_user_routes)

		reply_msg = "Hi! " + current_user.first_name + " Here is a your usage summary:\n\n"
		reply_msg += "You have covered a total distance of: " + str(total_distance) + " miles\n\n"
		reply_msg += "Your modes of travel have been:\n\n"
		reply_msg += get_mode_summary(current_user_routes)

	return reply_msg

def get_mode_summary(routes):
	res = {'driving':0, 'walking':0, 'bicycling':0, 'transit':0}

	for route in routes:
		res[route.mode_of_transport] += 1

	summary = ["\t" + k + " : " + str(v) + " times" for k,v in res.items()]
	return ("\n").join(summary)

def get_total_distance(routes):
	tot_sum = round(sum(map(float, [r.route_distance.split()[0] for r in routes])), 2)
	return tot_sum

@twilio_view
def test_text(request):
	r, reply_msg = twiml.Response(), None
	msg_content = request.GET['Body'].split(':')
	
	if len(msg_content) != 2:
		r.message('Looks like your message was not formatted correctly')
		return r

	user_phone_number, addresses = request.GET['From'], get_addresses(msg_content[1])

	'''
		Set phone number
	'''
	current_user, res_creation = StyraUser.objects.get_or_create(phone_number=user_phone_number)

	if len(addresses) == 0:
		r.message("Looks like your message was not formatted correctly")
		return r

	if msg_content[0] not in ACCEPTABLE_MODES:
		msg_content[0] = 'driving'

	resp = requests.get(DIRECTIONS_URL, params=prepare_request_params(addresses, msg_content[0]))

	if resp.status_code != requests.codes.ok:
		reply_msg = "Oops! Something went wrong on our side. Try again."
		r.message(reply_msg)
		return r

	data = resp.json()

	if data['status'] != 'OK':
		reply_msg = "Looks like your addresses are invalid"
		r.message(reply_msg)
		return r

	
	stats_msg = get_stats(user_phone_number)
	if stats_msg != None:
		r.message(stats_msg)

	route = data['routes'][0] # Get the first possible route
	leg = route['legs'][0] # Get the first/default leg
	distance = leg['distance']['text'] # Get the distance for this leg
	duration = leg['duration']['text'] # Get the duration for this leg


	route_obj = Route(mode_of_transport=msg_content[0], origin=addresses[0], destination=addresses[1], route_duration=duration, route_distance=distance)
	route_obj.styra_user = current_user
	route_obj.save()

	steps, instruction_objs = format_steps(leg['steps'], msg_content[0])

	# Save instructions to db
	for instruction in instruction_objs:
		instruction.route = route_obj
		instruction.save()

	reply_msg = "Hi " + current_user.first_name +" !\nThere are: " + str(len(steps)) + " steps in this trip\nThe total distance for this trip is: " + distance + "\nThe total duration for this trip is: " + duration
	r.message(reply_msg) # Send an overview text
	r.message(("\n").join(steps)) # Send a detailed series of steps
	return r

'''
	Returns an array containg the travel model
	and the origin>destination string
'''
def parse_message(msg):
	return msg.split()

'''
	Returns an array of parsed origin and destination
'''
def get_addresses(msg):
	return re.split(r'[>:;]{1}', msg)

'''
	Returns a dictionary containing origin and destination
'''
def prepare_request_params(addresses, mode):
	res = {'origin': addresses[0], 'destination': addresses[1], 'mode': mode}
	if mode == 'transit':
		res['departure_time'] = "now"
	return res

'''
	Parses HTML instructions and returns
	- an array containing formatted instructions
	- an array containing instruction objects
'''
def format_steps(steps, mode):
	formatted_steps, step_objs = [],[]

	for idx, step in enumerate(steps):
		clean_ins = str(idx+1) + ")\t" + BeautifulSoup(step['html_instructions']).get_text()
		if mode == 'transit' and 'transit_details' in step:
			clean_ins += " at " + step['transit_details']['departure_time']['text'] + "\n"
		else:
			clean_ins += "\n"
		duration,distance = step['duration']['text'], step['distance']['text']
		instruction = Instruction(instruction=clean_ins, step_duration=duration, step_distance=distance)
		formatted_steps.append(clean_ins)
		step_objs.append(instruction)

	return formatted_steps, step_objs