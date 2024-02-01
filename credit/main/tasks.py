from celery import shared_task
import pandas as pd
from models import Loan, Customer

excel_file_path = 'customer_data.xlsx'
df = pd.read_excel(excel_file_path)
for index, row in df.iterrows():
    # print(type(row["Date of Approval"].to_pydatetime()))
    Customer(
        customer_id = row['Customer ID'],
        first_name = row["First Name"],
        last_name = row["Last Name"],
        phone_number = row["Phone Number"],
        monthly_salary = row["Monthly Salary"],
        approved_limit = row["Approved Limit"],
    ).save

excel_file_path = 'loan_data.xlsx'
df = pd.read_excel(excel_file_path)
for index, row in df.iterrows():
    # print(type(row["Date of Approval"].to_pydatetime()))
    Loan(
        customer_id = row['Customer ID'],
        loan_id = row["Loan ID"],
        loan_amount = row["Loan Amount"],
        tenure = row["Tenure"],
        interest_rate = row["Interest Rate"],
        monthly_repayment = row["Monthly payment"],
        emis_paid_on_time = row["EMIs paid on Time"],
        start_date = row["Date of Approval"].to_pydatetime(),
        end_date = row["End Date"].to_pydatetime(),
    ).save
