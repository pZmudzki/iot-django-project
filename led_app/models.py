from django.db import models


class TemperatureReading(models.Model):
    timestamp   = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField()
    humidity    = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']


class LEDSchedule(models.Model):
    name     = models.CharField(max_length=100)
    on_time  = models.TimeField()
    off_time = models.TimeField()
    # 7 chars, one per day Mon-Sun: '1'=active, '0'=inactive
    days     = models.CharField(max_length=7, default='1111111')
    enabled  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def days_display(self):
        labels = ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Nie']
        return ', '.join(labels[i] for i, c in enumerate(self.days) if c == '1')


class BuzzerConfig(models.Model):
    threshold = models.FloatField(default=30.0)
    enabled   = models.BooleanField(default=True)
