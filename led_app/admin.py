from django.contrib import admin
from .models import TemperatureReading, LEDSchedule, BuzzerConfig


@admin.register(TemperatureReading)
class TemperatureReadingAdmin(admin.ModelAdmin):
    list_display  = ['timestamp', 'temperature', 'humidity']
    list_filter   = ['timestamp']
    ordering      = ['-timestamp']


@admin.register(LEDSchedule)
class LEDScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'on_time', 'off_time', 'days', 'enabled']


@admin.register(BuzzerConfig)
class BuzzerConfigAdmin(admin.ModelAdmin):
    list_display = ['threshold', 'enabled']
