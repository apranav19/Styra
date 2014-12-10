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
ACCEPTABLE_COMMANDS = set(['get directions', 'get summary', 'get history', 'sign up'])

'''
	Given a phoner number,
	this function will fetch and analyze the mileage statistics for each mode of transport 
'''
def get_stats(user_phone_number):
	reply_msg = "Looks like you have not made any trips yet"
	if not is_registered(user_phone_number):
		return "Looks like your phone number is not registered. Text Sign Up with your full name."

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

def parse_command(command_str):
	command_content = command_str.lower()
	return command_content if command_content in ACCEPTABLE_COMMANDS else None

'''
	Given a phone number and the user's name,
	the function will validate to check if phone number has been already registered
	and will proceed to either register the user
'''
def register_user(user_phone_number, details):
	'''
		Validate if phone number has been registered
	'''
	if len(StyraUser.objects.filter(phone_number=user_phone_number)) > 0:
		return "Looks like this phone number has already been registered"

	user_name = None
	resp = "Thank you for registering"
	if details == None:
		user_name = ["user", ""]
	else:
		user_name = details.split()

	StyraUser.objects.create(phone_number=user_phone_number, first_name=user_name[0], last_name=user_name[1])

	resp += " " + user_name[0]
	return resp

'''
	Returns true if user is registered, false otherwise
'''
def is_registered(user_phone_number):
	return True if len(StyraUser.objects.filter(phone_number=user_phone_number)) > 0 else False

'''
	Given a phone number and the message containing the mode of transit and a pair of addresses,
	this function will make a request to Google Directions API and fetch the directions
'''
def fetch_directions(user_phone_number, details):
	current_users = StyraUser.objects.filter(phone_number=user_phone_number)
	resp_msgs = []
	'''
		Validate for a registered user
	'''
	if not is_registered(user_phone_number):
		return "Looks like your phone number is not registered. Text Sign Up with your full name."

	current_user = current_users[0]
	parsed_message = details.split(":")
	mode, addresses = parsed_message[0], get_addresses(parsed_message[1])

	'''
		Validate message format for correct addresses
	'''
	if len(addresses) == 0:
		return "Looks like your message was not formatted correctly"

	if mode not in ACCEPTABLE_MODES:
		mode = "driving"

	'''
		Prepare HTTP request
	'''
	resp = requests.get(DIRECTIONS_URL, params=prepare_request_params(addresses, mode))

	'''
		Ensure HTTP response is valid
	'''
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
	duration = leg['duration']['text'] # Get the duration for this leg


	route_obj = Route(mode_of_transport=mode, origin=addresses[0], destination=addresses[1], route_duration=duration, route_distance=distance)
	route_obj.styra_user = current_user
	route_obj.save()

	steps, instruction_objs = format_steps(leg['steps'], mode)

	# Save instructions to db
	for instruction in instruction_objs:
		instruction.route = route_obj
		instruction.save()

	reply_msg = "Hi " + current_user.first_name +" !\nThere are: " + str(len(steps)) + " steps in this trip\nThe total distance for this trip is: " + distance + "\nThe total duration for this trip is: " + duration
	resp_msgs.append(reply_msg) # Send an overview text
	resp_msgs.append(("\n").join(steps)) # Send a detailed series of steps

	return resp_msgs

def get_history(user_phone_number):
	'''
		Validate for a registered user
	'''
	if not is_registered(user_phone_number):
		return "Looks like your phone number is not registered. Text Sign Up with your full name."

	current_user = StyraUser.objects.filter(phone_number=user_phone_number)
	routes = Route.objects.filter(styra_user=current_user)

	if len(routes) == 0:
		return "Looks like you have no recent travel history."

	reply_msgs = []
	reply_msgs.append("Here is your recent travel history:")
	for i,r in enumerate(routes[:5]):
		route_summary = str(i+1) + ") Date: " + str(r.time_of_travel) + "\nOrigin: " + r.origin + "\nDestination: " + r.destination + "\nMode: " + r.mode_of_transport
		reply_msgs.append(route_summary)

	return ("\n\n").join(reply_msgs)

@twilio_view
def test_text(request):
	r, reply_msg = twiml.Response(), None
	message_content = request.GET['Body'].split("\n")
	command_content = parse_command(message_content[0])
	current_user = None

	'''
		Check if valid command was processed
	'''
	if command_content == None:
		r.message('Looks like you requested an invalid command')
		return r

	user_phone_number = request.GET['From']
	
	'''
		If registration was requested
	'''
	if command_content == 'sign up':
		resp_msg = register_user(request.GET['From'], message_content[1])
		r.message(resp_msg)
		return r

	'''
		If directions were requested
	'''
	if command_content == 'get directions':
		resp_msgs = fetch_directions(request.GET['From'], message_content[1])
		for msg in resp_msgs:
			r.message(msg)
		return r

	'''
		If summary was requested
	'''
	if command_content == 'get summary':
		resp_msg = get_stats(request.GET['From'])
		r.message(resp_msg)
		return r

	'''
		If history was requested
	'''
	if command_content == 'get history':
		resp_msg = get_history(request.GET['From'])
		r.message(resp_msg)
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