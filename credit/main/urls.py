from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register', views.Register.as_view(), name='register'),
    path('view-loans/<int:customer_id>/', views.CustomerLoans.as_view(), name='view-loans'),
    path('view-loan/<int:loan_id>/', views.GetLoan.as_view(), name='view-loan'),
    path('check-eligibility', views.CheckEligibility.as_view(), name='check-eligibility'),
    path('create-loan', views.CreateLoan.as_view(), name='create_loan'),
]