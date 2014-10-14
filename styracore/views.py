from django.shortcuts import render
from django.http import HttpResponse
from django_twilio.decorators import twilio_view
from twilio import twiml

@twilio_view
def test_text(request):
    r = twiml.Response()
    r.message('Thanks for the SMS message!')
    return r