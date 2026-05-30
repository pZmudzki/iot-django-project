from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.led_control,    name='led_control'),
    path('morse/',              views.morse_prompt,   name='morse_prompt'),
    path('api/temperature/',    views.temperature_api, name='temperature_api'),
    path('chart/',              views.chart_view,     name='chart'),
    path('schedule/',           views.schedule_view,  name='schedule'),
    path('schedule/<int:pk>/toggle/', views.schedule_toggle, name='schedule_toggle'),
    path('schedule/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
    path('buzzer/',             views.buzzer_config,  name='buzzer_config'),
    path('servo/',              views.servo_view,     name='servo'),
    path('servo/api/',          views.servo_api,      name='servo_api'),
    path('color/',              views.color_view,     name='color'),
    path('color/api/',          views.color_api,      name='color_api'),
    path('pdf/',                views.pdf_report,     name='pdf_report'),
    path('roulette/',           views.roulette_view,  name='roulette'),
    path('roulette/spin/',      views.roulette_spin,  name='roulette_spin'),
    path('roulette/reset/',     views.roulette_reset, name='roulette_reset'),
]
