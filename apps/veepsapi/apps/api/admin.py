from django.contrib import admin
from .models import (
    Playout,
    Distribution,
    Channel,
    Clip,
    Action,
    Schedule,
    Input,
    CallbackSubscriber,
)

admin.site.register(Playout)
admin.site.register(Distribution)
admin.site.register(Channel)
admin.site.register(Clip)
admin.site.register(Action)
admin.site.register(Schedule)
admin.site.register(Input)
admin.site.register(CallbackSubscriber)
