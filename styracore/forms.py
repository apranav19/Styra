from django import forms

class UserSignUp(forms.Form):
	email_field = forms.EmailField()
	first_name = forms.CharField(max_length=128)
	last_name = forms.CharField(max_length=128)