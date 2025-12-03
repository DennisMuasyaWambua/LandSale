from django.db import models

# Create your models here.
class Land(models.Model):
    plot_number = models.IntegerField()
    size = models.DecimalField(max_digits=10, decimal_places=2)
    property_type = models.CharField(max_length=100,choices=[('commercial','Commercial'),('residential','Residential')])
    price = models.DecimalField(max_digits=15, decimal_places=2)