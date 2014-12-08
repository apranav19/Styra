from django.conf.urls import patterns, include, url
from styracore import views

urlpatterns = patterns('',
	url(r'^test_text/', views.test_text),
	url(r'^get_stats/', views.get_stats)
)
