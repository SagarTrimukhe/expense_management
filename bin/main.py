import json
import pymongo
from datetime import date
import sys
import os
import subprocess


client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["expense_management"]
# db = client["test_db"]


def store_transactions(payment_mode, category, amount, new_balance, remarks, user_date=''):
    # Creating a collection per month
    # Get the current date

    today = date.today()
    current_date = today.strftime("%d/%m/%Y")
    month_year = today.strftime("%m_%Y")
    collection = db[month_year]

    if user_date != '':
        current_date = user_date
        # month_year = user_date[3:5]+'_'+user_date[6:]
        month_year = user_date[3:].replace("/", "_")
        collection = db[month_year]

    data = {"date": current_date,
            "details": []
            }

    temp = {"payment_mode": payment_mode,
            "category": category,
            "amount": amount,
            "closing_balance": new_balance,
            "remarks": remarks}

    check = collection.find_one({"date": current_date})

    if check is None:
        collection.insert_one(data)
        collection.update_one({"date": current_date}, {"$set": {"details": [temp]}})
    else:
        x = collection.find_one({"date": current_date})
        previous_data = x["details"]
        previous_data.append(temp)
        collection.update_one({"date": current_date}, {"$set": {"details": list}})


def enter_expense_details():
    expense_categories = {"Food": [],
                          "Travelling": [],
                          "Health(Fruits/Meds)": [],
                          "Groceries": [],
                          "Home(rent/water/EC)": [],
                          "Shopping": [],
                          "Entertainment": [],
                          "Mobile": [],
                          "Family": []
                          }

    map_between_ip_and_category = {
        1: "Food",
        2: "Travelling",
        3: "Health(Fruits/Meds)",
        4: "Groceries",
        5: "Home(rent/water/EC)",
        6: "Shopping",
        7: "Entertainment",
        8: "Mobile",
        9: "Family"}

    collection = db["accounts"]

    payment_modes = {}

    account_count = 1
    for x in collection.find({"wallet": "y"}, {"name": 1}):
        payment_modes[account_count] = x["name"]
        account_count += 1

    ''''''''''''''' Taking Input from user'''''''''''''''''''''
    try:
        print("Press ENTER for today's date or Enter date in dd/mm/yyyy format")
        user_date = input()

        while True:
            print("Select Category: ")
            print(json.dumps(map_between_ip_and_category, indent=4))
            while True:
                category = int(input())
                if category > 9:
                    print("Invalid Choice")
                else:
                    break

            print("Select mode of Payment")
            print(json.dumps(payment_modes, indent=4))
            while True:
                pay_mode = int(input())
                if pay_mode > 4:
                    print("Invalid Choice")
                else:
                    break

            print("Enter Amount :", end='')
            while True:
                amount = int(input())
                if amount < 0:
                    print("Invalid amount")
                else:
                    break

            print("Any remarks :", end='')
            remarks = input()
            ###############################################################

            expense_categories[map_between_ip_and_category[category]].append(amount)
            expense_categories[map_between_ip_and_category[category]].append(remarks)

            # ########## Updating Database balance ############################### #
            collection = db['accounts']

            x = collection.find_one({"name": payment_modes[pay_mode]})

            if x is None:
                print("Account doesn't exists in the DB. Please add and Proceed")
                return

            new_balance = int(x["balance"]) - amount

            query = {'name': payment_modes[pay_mode]}
            new_value = {"$set": {"balance": new_balance}}

            collection.update_one(query, new_value)  # Updating the balance

            # #### Calling the DB function to store the transaction ##############
            store_transactions(payment_modes[pay_mode], map_between_ip_and_category[category], amount,
                               new_balance, remarks, user_date)
            print("Enter ^C to Dashboard  //*\\  ENTER to add expenses")
            input()

    except KeyboardInterrupt:
        print()


def account_transfer():
    collection = db["accounts"]

    print(30 * '*', "Current Account Details", 30 * '*')
    print('{:40s}{:6s}'.format("Account Name", "Balance"))
    print(50 * '-')
    for x in collection.find():
        print('{:40s}{:6s}'.format(str(x["name"]), str(x["balance"])))

    print("Enter source account: ", end='')
    source = input()
    print("Enter destination account: ", end='')
    destination = input()

    print("Enter amount: ", end='')
    amount = int(input())  # add min balance checker

    print("Transferring Rs.", amount, " from ", source, "to ", destination)

    x = collection.find_one({"name": source})
    new_balance = int(x["balance"]) - amount
    collection.update_one({"name": source}, {"$set": {"balance": new_balance}})

    x = collection.find_one({"name": destination})
    new_balance = int(x["balance"]) + amount
    collection.update_one({"name": destination}, {"$set": {"balance": new_balance}})

    print("Transfer Successful!!")


def edit_account_details():
    collection = db["accounts"]
    # collection.drop()

    print("1 - To add new account")
    print("2 - To change the account balance")
    print("3 - To delete an account")

    while True:
        ch = int(input())
        if ch > 3:
            print("Invalid Choice, Enter correct choice")
        else:
            break

    if ch == 1:
        print("Enter account details")

        try:
            while True:
                account_details = {"name": '',
                                   "balance": '',
                                   "wallet": ''}

                print("Enter account Name : ", end='')  # Check if the account with same name exists
                account_details["name"] = input()

                x = collection.find_one({"name": account_details["name"]})

                if x is not None:
                    print("Account Already exists")

                else:
                    while True:
                        print("Enter account Balance : ", end='')
                        account_details["balance"] = int(input())

                        if account_details["balance"] < 0:
                            print("Invalid Balance. Please enter >=0  Value. Try again")
                        else:
                            break

                    print("Are you using this account as a wallet i.e. Do you spend the money for daily expenses(y/n)?")
                    account_details["wallet"] = input()
                    account_details["wallet"] = account_details["wallet"].lower()

                    print(account_details)
                    collection.insert_one(account_details)

                print("Enter ^C to Dashboard //*\\ Enter to add another account")
                input()

        except KeyboardInterrupt:
            print("Done")

    elif ch == 2:
        print(30*'*', "Current Account Details", 30*'*')
        print('{:40s}{:6s}'.format("Account Name", "Balance"))
        print(50*'-')
        for x in collection.find():
            print('{:40s}{:6s}'.format(str(x["name"]), str(x["balance"])))

        print("Enter the account name:", end='')
        account_name = input()

        try:
            print("Enter new balance: ", end='')
            new_balance = int(input())
            print(account_name, new_balance)
            collection.update_one({"name": account_name}, {'$set': {"balance": new_balance}})
            print("Balance Updated Successfully!!")

        except Exception as e:
            print(e)

    elif ch == 3:
        print(30 * '*', "Current Account Details", 30 * '*')
        print('{:40s}{:6s}'.format("Account Name", "Balance"))
        print(50 * '-')
        for x in collection.find():
            print('{:40s}{:6s}'.format(str(x["name"]), str(x["balance"])))

        print("Enter the account name to delete:", end='')
        account_name = input()

        try:
            collection.delete_one({"name": account_name})
            print("Account deleted Successfully!!")

        except Exception as e:
            print("Account deletion Unsuccessful")
            print(e)

    else:
        print("Invalid input")


def view_account_details():
    print(30*'*', "Account Summary", 30*'*')
    collection = db['accounts']
    print('{:50s}{:10s}{:10s}'.format("Name", "Balance", "Wallet"))
    print(76*"-")
    for x in collection.find():
        print('{:50s}{:10s}{:10s}'.format(str(x["name"]), str(x["balance"]), str(x["wallet"])))


def view_spent_report_of_month():

    print("Press ENTER to view details of Current month or else Enter (mm/yyyy)")
    month_year = input()

    if month_year == '':
        today = date.today()
        month_year = today.strftime("%m_%Y")

    else:
        month_year = month_year.replace("/", "_")

    collection = db[month_year]

    category_amount_dict = {"Food": [0, 0],
                            "Travelling": [0, 0],
                            "Health(Fruits/Meds)": [0, 0],
                            "Groceries": [0, 0],
                            "Home(rent/water/EC)": [0, 0],
                            "Shopping": [0, 0],
                            "Entertainment": [0, 0],
                            "Mobile": [0, 0],
                            "Family": [0, 0]}

    for day in collection.find():                         # Traversing through all the days of month
        for i in range(len(day["details"])):              # Traversing through all the entries of day
            for j in category_amount_dict.keys():        # Traversing through all the categories of one entry
                if j == day["details"][i]["category"]:
                    category_amount_dict[j][0] += int(day["details"][i]["amount"])

    total_spent = 0
    for x in category_amount_dict.values():
        total_spent += x[0]

    for x in category_amount_dict.values():
        x[1] = (x[0]/total_spent)*100

    print(30 * '*', "Expense Summary of " + month_year, 30 * '*')
    print('{:40s}{:10s}{:6s}'.format("Category", "Amount", "Percentage"))
    for x in category_amount_dict.keys():
        print('{:40s}{:10s}{:6.2f}'.format(x, str(category_amount_dict[x][0]), category_amount_dict[x][1]))

    print(50 * '-')
    print()
    print("Total: ", total_spent)
    print()


def view_expense_details_of_particular_day():
    collection_name = date.today().strftime("%m_%Y")
    today = date.today().strftime("%d/%m/%Y")
    # today = "03/09/2019"

    print("Press ENTER to see today's details or Enter date in (dd/mm/yyyy) format : ", end='')
    user_date = input()

    if len(user_date) < 1:
        user_date = today
    else:
        collection_name = user_date[3:5]+'_'+user_date[6:]

    collection = db[collection_name]
    x = collection.find_one({"date": user_date})

    if x is None:
        print("No Data available. Please enter today's expenses to see the results")
        return

    details = x["details"]

    print(20 * '*', "Today's Expense Details", 20 * '*')
    print('{:20s}{:20s}{:10s}{:40s}'.format("Payment Mode", "Category", " Amount", "Remarks"))
    print(65*'-')

    for transaction in details:
        print('{:20s}{:20s}{:10s}{:40s}'.format(transaction["payment_mode"], transaction["category"],
                                                str(transaction["amount"]), transaction["remarks"]))


def view_transaction_history():
    today = date.today()
    month_year = today.strftime("%m_%Y")
    collection = db[month_year]

    x = collection.find_one()
    if x is None:
        print("No records found. Please insert some data")

    for x in collection.find().sort([("date", 1)]):
        print(x["date"])
        print('{:20s}{:25s}{:10s}{:6s}{:40s}'.format("Payment Mode", "Category", "Amount", "CB", "Remarks"))
        for i in x["details"]:
            print('{:20s}{:25s}{:10s}{:6s}{:40s}'.format(i["payment_mode"], i["category"], str(i["amount"]),
                                                         str(i["closing_balance"]), i["remarks"]))
        print("\n")

    return


# For testing purpose only... Delete it afterwards
def view_raw_db():
    collection = db["accounts"]
    for x in collection.find():
        print(x)
        # print(json.dumps(x,indent=4))


def start():
    print()
    print("----------------------------------Welcome to your Personal Expense Mangement Console-----------------------------------")
    print()
    print("*******************Dashboard*******************")

    print("1 - Enter Expenses")
    print("2 - Edit Account details ")
    print("3 - Account Transfer")
    print("4 - View Expenses of a Particular day")
    print("5 - View Total Expenses of current month")
    print("6 - View Account details")
    print("7 - View Transaction History")

    print()
    print("Enter your choice :: ", end='')

    choice_method_map = {
        1: enter_expense_details,
        2: edit_account_details,
        3: account_transfer,
        4: view_expense_details_of_particular_day,
        5: view_spent_report_of_month(),
        6: view_account_details,
        7: view_transaction_history
    }

    try:
        choice = input()
        choice = int(choice)
        choice_method_map[choice]()

    except Exception as e:
        print(e)

    print(60*"_-")


try:
    while True:
        start()
        print("Enter ^C to Quit  //*\\  ENTER to Continue")
        input()
except KeyboardInterrupt:
    print("Hold on...Backup is in Process!!")
    os.chdir("..\\data")
    subprocess.check_output("backup.bat", creationflags=0x08000000)
    print("Done..")
    sys.exit()
