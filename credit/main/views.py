from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.views import View
from .models import Customer, Loan
from datetime import date
from django.db import models
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd

# Create your views here.

MAX_LOANS = 30
MAX_YEAR_LOANS = 3
MAX_SINGLE_LOAN = 1000000
MAX_TOTAL_LOAN_AMOUNT = MAX_LOANS * MAX_SINGLE_LOAN

def home(request):
    return render(request, 'main/home.html')

@method_decorator(csrf_exempt, name='dispatch')
class Register(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            print("data", data)
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            age = data.get('age')
            monthly_income = data.get('monthly_income')
            phone_number = data.get('phone_number')

            approved_limit = round(36 * monthly_income, -5)

            new_customer = Customer.objects.create(
                first_name=first_name,
                last_name=last_name,
                monthly_salary=monthly_income,
                approved_limit=approved_limit,
                current_debt=0,
                phone_number=phone_number,
            )

            response_data = {
                'customer_id': new_customer.customer_id,
                'name': f"{new_customer.first_name} {new_customer.last_name}",
                'age': age,
                'monthly_income': monthly_income,
                'approved_limit': approved_limit,
                'phone_number': phone_number,
            }

            return JsonResponse(response_data, status=201)
        except Exception as e:
            return JsonResponse({'error': "Invalid Input"}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class CustomerLoans(View):
    def get(self, *args, **kwargs):
        try:
            customer_id= self.kwargs['customer_id']

            loans = Loan.objects.filter(customer_id=customer_id)
            loans_list = []
            current_date = date.today()
            for loan in loans:
                months_difference = relativedelta(loan.end_date, current_date).months + 1
                loan_item = {
                    'loan_id': loan.loan_id,
                    'loan_amount': loan.loan_amount,
                    'interest_rate': loan.interest_rate,
                    'monthly_installment': loan.monthly_repayment,
                    'repayments_left': months_difference
                }
                loans_list.append(loan_item)
            return JsonResponse({'loans': loans_list}, status=200)
        except Exception as e:
            return JsonResponse({'error': "Invalid Input"}, status=400)

    
@method_decorator(csrf_exempt, name='dispatch')
class GetLoan(View):
    def get(self, *args, **kwargs):
        try:
            loan_id= self.kwargs['loan_id']
            loan = Loan.objects.filter(loan_id=loan_id)
            customer = Customer.objects.filter(customer_id=loan[0].customer_id.customer_id)
            customer = {
                'first_name': customer[0].first_name,
                'last_name': customer[0].last_name,
                'phone_number': customer[0].phone_number,
            }

            loan = {
                'loan_id': loan[0].loan_id,
                'customer': customer,
                'loan_amount': loan[0].loan_amount,
                'interest_rate': loan[0].interest_rate,
                'monthly_installment': loan[0].monthly_repayment,
                'tenure': loan[0].tenure,
            }
            return JsonResponse(loan, status=200)
        except Exception as e:
            return JsonResponse({'error': "Invalid Input"}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class CheckEligibility(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            customer = Customer.objects.filter(customer_id=data['customer_id'])
            if customer.__len__() == 0:
                return JsonResponse({
                    'approval': False,
                    'message': 'id not found',
                }, status=200)
            loans = Loan.objects.filter(customer_id=data['customer_id'])
            credit_score = 0.0

            #assigning default credit score if no data is present
            if loans.__len__() == 0:
                credit_score = 40
            else:
                #30% credit score depends on timely payments
                total_tenure = loans.aggregate(total_sum=models.Sum('tenure'))['total_sum']
                total_timely_payments = loans.aggregate(total_sum=models.Sum('emis_paid_on_time'))['total_sum']
                credit_score+=total_timely_payments/total_tenure*30

                
                #25% credit score depends on number of loans taken in past
                credit_score+=loans.__len__()/MAX_LOANS*25

                #25% of credit score depends on Loan approved volume
                total_approved_volume = loans.aggregate(total_sum=models.Sum('loan_amount'))['total_sum']
                credit_score+=float(total_approved_volume)/MAX_TOTAL_LOAN_AMOUNT*25

                #20% of credit score depends on loan activity in current year
                current_year = date.today().year
                number_of_loans_current_year = loans.filter(
                    start_date__year=current_year
                ).count()
                credit_score+=number_of_loans_current_year/MAX_YEAR_LOANS*20

                if loans.__len__() == MAX_LOANS or number_of_loans_current_year == MAX_YEAR_LOANS:
                    return JsonResponse({
                        'approval': False,
                        'message': 'loan limit reached',
                    }, status=200)
                sum_of_current_loans = 0
                sum_of_current_loans = loans.filter(end_date__gt=date.today()).aggregate(total_sum=models.Sum('loan_amount'))['total_sum']
                if sum_of_current_loans + data['loan_amount'] > customer[0].approved_limit:
                    return JsonResponse({
                        'approval': False,
                        'message': 'Approval limit reached',
                    }, status=200)
                
                sum_of_current_emi = loans.filter(end_date__gt=date.today()).aggregate(total_sum=models.Sum('monthly_repayment'))['total_sum']
                if sum_of_current_emi > customer[0].monthly_salary:
                    return JsonResponse({
                        'approval': False,
                        'message': 'Not Enough monthly salary',
                    }, status=200)



            if credit_score < 0:
                return JsonResponse({
                    'approval': False,
                    'message': 'Not Enough credit score',
                }, status=200)

            corrected_interest_rate = data['interest_rate']
            if credit_score < 30:
                corrected_interest_rate = max(16, corrected_interest_rate)
            if credit_score < 50 and credit_score > 30:
                corrected_interest_rate = max(12, corrected_interest_rate)

            monthly_installment = data['loan_amount']/data['tenure'] + data['loan_amount']/data['tenure']*corrected_interest_rate/100
            
            response_data = {
                'customer_id': data['customer_id'],
                'approval': True,
                'interest_rate': data['interest_rate'],
                'corrected_interest_rate': corrected_interest_rate,
                'tenure': data['tenure'],
                'monthly_installment': monthly_installment
            }
            
            return JsonResponse(response_data, status=200)
        except Exception as e:
            return JsonResponse({'error': "Invalid Input"}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class CreateLoan(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            eligibility = CheckEligibility().post(request)
            eligibility = json.loads(eligibility.content)

            if not eligibility['approval']:
                return JsonResponse({
                    'loan_approved': False,
                    'message': 'Not Enough credit score',
                }, status=400)
            
            new_loan = Loan(
                customer_id=Customer.objects.filter(customer_id=data['customer_id'])[0],
                loan_amount=data['loan_amount'],
                tenure=data['tenure'],
                interest_rate=eligibility['corrected_interest_rate'],
                monthly_repayment=eligibility['monthly_installment'],
                emis_paid_on_time=0,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30*data['tenure']),
            )

            new_loan.save()

            return JsonResponse({
                    'customer_id': data['customer_id'],
                    'loan_id': new_loan.loan_id,
                    'loan_approved': True,
                    'monthly_installment': eligibility['monthly_installment']
                }, status=201)
        except Exception as e:
            return JsonResponse({'error': "Invalid Input"}, status=400)

        

@method_decorator(csrf_exempt, name='dispatch')
class Task(View):
    def get(self, *args, **kwargs):
        try:
            excel_file_path = 'main/customer_data.xlsx'
            df = pd.read_excel(excel_file_path)
            for index, row in df.iterrows():
                print(index)
                try:
                    new_customer = Customer.objects.create(
                        customer_id = row['Customer ID'],
                        first_name = row["First Name"],
                        last_name = row["Last Name"],
                        phone_number = row["Phone Number"],
                        monthly_salary = row["Monthly Salary"],
                        approved_limit = row["Approved Limit"],
                        current_debt = 0,
                    )
                    print(new_customer)
                except Exception as e:
                    print("EXCEPTION ", e)
            excel_file_path = 'main/loan_data.xlsx'
            df = pd.read_excel(excel_file_path)
            for index, row in df.iterrows():
                print(index)
                try:
                    new_loan = Loan(
                        customer_id = Customer.objects.filter(customer_id=row['Customer ID'])[0],
                        loan_id = row["Loan ID"],
                        loan_amount = row["Loan Amount"],
                        tenure = row["Tenure"],
                        interest_rate = row["Interest Rate"],
                        monthly_repayment = row["Monthly payment"],
                        emis_paid_on_time = row["EMIs paid on Time"],
                        start_date = row["Date of Approval"].to_pydatetime(),
                        end_date = row["End Date"].to_pydatetime(),
                    )

                    new_loan.save()
                    print(new_loan)
                except Exception as e:
                    print("EXCEPTION ", e)

            return JsonResponse({'Succuess': True}, status=200)
        except Exception as e:
            return JsonResponse({'error': 'error'}, status=400)




        