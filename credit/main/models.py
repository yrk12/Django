from django.db import models

# Create your models here.
class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255, blank=False)
    last_name = models.CharField(max_length=255, blank=False)
    phone_number = models.CharField(max_length=20, blank=False)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    approved_limit = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    current_debt = models.DecimalField(max_digits=10, decimal_places=2, null=False)

class Loan(models.Model):
    loan_id = models.AutoField(primary_key=True)
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenure = models.PositiveIntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    monthly_repayment = models.DecimalField(max_digits=10, decimal_places=2)
    emis_paid_on_time = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField() 
