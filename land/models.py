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
    phase = models.CharField(max_length=100, blank=True, default='')
    customer_name = models.CharField(max_length=200)
    customer_contact = models.CharField(max_length=100)
    booking_date = models.DateTimeField(auto_now_add=True)
    payment_reference = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100,choices=[('cash','Cash'),('mpesa','mpesa'),('bank_transfer','Bank Transfer')])
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=50,choices=[('booked','Booked'),('confirmed','Confirmed'),('cancelled','Cancelled')])


class ProjectSales(models.Model):
    plot = models.ForeignKey(Plots, on_delete=models.CASCADE)
    client = models.CharField(max_length=200)
    phase = models.CharField(max_length=100)
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2)
    deposit = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Project Sales"

    def __str__(self):
        return f"{self.client} - Plot {self.plot.plot_number}"


class AgentSales(models.Model):
    plot = models.ForeignKey(Plots, on_delete=models.CASCADE)
    phase = models.CharField(max_length=100)
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2)
    commission = models.DecimalField(max_digits=5, decimal_places=2, help_text="Commission percentage (e.g., 5.00 for 5%)")
    sub_agent_name = models.CharField(max_length=200, blank=True, default='')
    principal_agent = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Agent Sales"

    def __str__(self):
        return f"{self.principal_agent} - Plot {self.plot.plot_number}"