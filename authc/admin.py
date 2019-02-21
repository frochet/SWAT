from django.contrib import admin

# Register your models here.

from .models import User, Computer, Canvas

admin.site.register(Computer)
admin.site.register(Canvas)

class CanvasAdmin(admin.ModelAdmin):

	search_fields = ('version', 'date_creation')


