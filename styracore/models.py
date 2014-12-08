from django.db import models

'''
	Represents a user who initiates a request for driving directions
'''
class StyraUser(models.Model):

	# Define properties
	email_address = models.EmailField(max_length=75)
	phone_number = models.CharField(max_length=128)
	first_name = models.CharField(max_length=128)
	last_name = models.CharField(max_length=128)


'''
	Represents the Route model that will contain
	information regarding distance, duration, mode of transport,
	and locations visited.
'''
class Route(models.Model):

	# Define properties
	mode_of_transport = models.CharField(max_length=128)
	time_of_travel = models.DateField(auto_now_add=True)
	origin = models.CharField(max_length=512)
	destination = models.CharField(max_length=512)
	route_duration = models.CharField(max_length=128)
	route_distance = models.CharField(max_length=128)

	styra_user = models.ForeignKey(StyraUser, default=1)


'''
	Represents an individual instruction that contains
	information regarding the details of the instruction and the
	distance and duration of the instruction
'''
class Instruction(models.Model):

	# Define properties
	route = models.ForeignKey(Route)
	instruction = models.CharField(max_length=512)
	step_duration = models.CharField(max_length=128)
	step_distance = models.CharField(max_length=128)