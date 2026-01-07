from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=200)
    phase = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    project_svg_map = models.FileField(upload_to='project_maps/', null=True, blank=True)
    location = models.CharField(max_length=300)
    size = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Plots(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    plot_number = models.CharField(max_length=50)
    size = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    property_type = models.CharField(max_length=100, choices=[('commercial','Commercial'),('residential','Residential')], default='residential')
    phase = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Booking(models.Model):
    plot = models.ForeignKey(Plots, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=200)
    customer_contact = models.CharField(max_length=100)
    booking_date = models.DateTimeField(auto_now_add=True)
    payment_reference = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100,choices=[('cash','Cash'),('mpesa','mpesa'),('bank_transfer','Bank Transfer')])
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=50,choices=[('booked','Booked'),('confirmed','Confirmed'),('cancelled','Cancelled')])