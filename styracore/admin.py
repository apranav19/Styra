from django.contrib import admin
from styracore.models import StyraUser, Route, Instruction

admin.site.register(StyraUser)
admin.site.register(Route)
admin.site.register(Instruction)