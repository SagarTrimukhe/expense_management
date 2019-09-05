import json
import pymongo
from datetime import date
import sys
import os
import subprocess


client = pymongo.MongoClient("mongodb://localhost:27017")
db = client[""]


def store_transactions(payment_mode, category, amount, new_balance, remarks):
    # Creating a collection per month
    ## Get the current date
    today = date.today()
    current_date = today.strftime("%d/%m/%Y")
    month_year = today.strftime("%m_%Y")
    collection = db[month_year]

    data = {"date": current_date,
            "details": []
            }

    temp = {"payment_mode": payment_mode,
            "category": category,
            "amount": amount,
            "closing_balance": new_balance,
            "remarks": remarks}

    check = collection.find_one({"date":current_date})

    if check == None:
        x = collection.insert_one(data)
        x = collection.update_one({"date": current_date}, {"$set": {"details": [temp]}})
    else:
        x = collection.find_one({"date":current_date})
        list = x["details"]
        list.append(temp)
        x = collection.update_one({"date":current_date},{"$set":{"details":list}})


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

    payment_modes = {1: "Paytm", 2: "SBI", 3: "CASH", 4: "ICICI"}

    ''''''''''''''' Taking Input from user'''''''''''''''''''''
    try:
        while True:
            print("Select Category: ")
            print(json.dumps(map_between_ip_and_category, indent=4))
            category = int(input())

            print("Select mode of Payment")
            print(json.dumps(payment_modes, indent=4))
            pay_mode = int(input())

            print("Enter Amount :",end='')
            amount = int(input())

            print("Any remarks :",end='')
            remarks = input()
            ###############################################################

            expense_categories[map_between_ip_and_category[category]].append(amount)
            expense_categories[map_between_ip_and_category[category]].append(remarks)

            ########### Updating Database balance ################################
            collection = db['accounts']

            x = collection.find_one({"name": payment_modes[pay_mode]})
            new_balance = int(x["balance"]) - amount

            query = {'name': payment_modes[pay_mode]}
            new_value = {"$set": {"balance": new_balance}}

            collection.update_one(query,new_value)  ##Updating the balance

            ##### Storing the information in file##############################
            store_transactions(payment_modes[pay_mode],map_between_ip_and_category[category], amount, new_balance, remarks)
            print("Enter ^C to Dashboard  /*\  ENTER to add expenses")
            input()

    except KeyboardInterrupt:
        print("Today's Spent ::", json.dumps(expense_categories, indent=4, sort_keys=True))


def edit_account_details():
    collection = db["accounts"]
    # collection.drop()

    print("1 - To add new account")
    print("2 - To change the account balance")

    ch = int(input())
    if ch == 1:
        print("Enter account details")

        try:
            while True:
                account_details = {"type": '',
                                   "name": '',
                                   "balance": ''}

                print("Enter account type(Savings/MF) : ",end='')
                account_details["type"] = input()
                print("Enter account Name : ",end='')
                account_details["name"] = input()
                print("Enter account Balance : ",end='')
                account_details["balance"] = input()

                print(account_details)
                collection.insert_one(account_details)
                print("Enter ^C to Dashboard /\ Enter to add another account")
                input()

        except KeyboardInterrupt:
            print("Done")

    elif ch == 2:
        print(30*'*',"Current Account Details",30*'*')
        print('{:40s}{:6s}'.format("Account Name","Balance"))
        print(50*'-')
        for x in collection.find():
            print('{:40s}{:6s}'.format(str(x["name"]),str(x["balance"])))

        print("Enter the account name:", end='')
        account_name = input()

        try:
            print("Enter new balance: ",end='')
            new_balance = int(input())
            print(account_name,new_balance)
            collection.update_one({"name":account_name},{'$set':{"balance":new_balance}})
            print("Balance Updated Successfully!!")

        except Exception as e:
            print(e)

    else:
        print("Invalid input")


def view_account_details():
    print(30*'*',"Account Summary",30*'*')
    collection = db['accounts']
    print('{:20s}{:50s}{:6s}'.format("Account Type","Name","Balance"))
    print(76*"-")
    for x in collection.find():
        print('{:20s}{:50s}{:6s}'.format(str(x["type"]),str(x["name"]),str(x["balance"])))


def view_spent_report():
    print(30 * '*', "Expense Summary", 30 * '*')
    today = date.today()
    month_year = today.strftime("%m_%Y")
    collection = db[month_year]



    category_amount_dict={ "Food": 0,
                          "Travelling":0,
                          "Health(Fruits/Meds)": 0,
                          "Groceries": 0,
                          "Home(rent/water/EC)": 0,
                          "Shopping": 0,
                          "Entertainment": 0,
                          "Mobile": 0,
                          "Family": 0}

    for day in collection.find():  ## Traversing through all the days of month
        for i in range(len(day["details"])): ## Traversing through all the entries of day
             for j in category_amount_dict.keys(): ## Traversing through all the categories of one entry
                 if j == day["details"][i]["category"]:
                    category_amount_dict[j] += day["details"][i]["amount"]

    total_spent = 0
    for x in category_amount_dict.values():
        total_spent += x

    print(json.dumps(category_amount_dict,indent = 5))
    print()
    print("Total: ",total_spent)


def account_transfer():
    collection = db["accounts"]

    print(30 * '*', "Current Account Details", 30 * '*')
    print('{:40s}{:6s}'.format("Account Name", "Balance"))
    print(50 * '-')
    for x in collection.find():
        print('{:40s}{:6s}'.format(str(x["name"]), str(x["balance"])))

    print("Enter source account: ",end='')
    source = input()
    print("Enter destination account: ",end='')
    destination = input()

    print("Enter amount: ",end='')
    amount = int(input())  ## add min balance checker

    print("Transferring Rs.", amount, " from ", source, "to ", destination)

    x = collection.find_one({"name":source})
    new_balance = int(x["balance"]) - amount
    collection.update_one({"name":source},{"$set":{"balance":new_balance}})

    x = collection.find_one({"name": destination})
    new_balance = int(x["balance"]) + amount
    collection.update_one({"name": destination}, {"$set": {"balance": new_balance}})

    print("Transfer Successful!!")


def view_expense_details_of_particular_day():
    collection_name  = date.today().strftime("%m_%Y")
    today = date.today().strftime("%d/%m/%Y")
    #today = "03/09/2019"

    print("Press ENTER to see today's details or Enter date in (dd/mm/yyyy) format : ", end='')
    user_date = input()

    if len(user_date) < 1:
        user_date = today
    else:
        collection_name = user_date[3:5]+'_'+user_date[6:]

    collection = db[collection_name]
    x = collection.find_one({"date":user_date})
    print(x)

    if x == None:
        print("No Data available. Please enter today's expenses to see the results")
        return

    details = x["details"]

    print(20 * '*', "Today's Expense Details", 20 * '*')
    print('{:20s}{:20s}{:10s}{:40s}'.format("Payment Mode","Category","Amount","Remarks"))
    print(65*'-')

    for transaction in details:
        print('{:20s}{:20s}{:10s}{:40s}'.format(transaction["payment_mode"],transaction["category"],str(transaction["amount"]),transaction["remarks"]))


# For testing purpose only... Delete it afterwards
def view_raw_db():
    collection = db["09_2019"]

    for x in collection.find():
        print(x)
        #print(json.dumps(x,indent=4))


def start():
    print()
    print("----------------------------------Welcome to your Personal Expense Mangement Console-----------------------------------")
    print()
    print("*******************Dashboard*******************")

    print("1 - Enter todays's Expenses")
    print("2 - Edit Account details ")
    print("3 - Account Transfer")
    print("4 - View Expenses of a Particular day")
    print("5 - View Total Expenses of current month")
    print("6 - View Account details")

    print()
    print("Enter your choice :: ",end='')
    choice =int(input())

    if choice == 1:
        enter_expense_details()
    elif choice == 2:
        edit_account_details()
    elif choice == 3:
        account_transfer()
    elif choice == 4:
        view_expense_details_of_particular_day()
    elif choice == 5:
        view_spent_report()
    elif choice == 6:
        view_account_details()
    else:
        print("Invalid choice")

    print(60*"_-")



try:
    while True:
        start()
        print("Enter ^C to Quit  /*\  ENTER to Continue")
        input()
except KeyboardInterrupt:
    print("Hold on...Backup is in Process!!")
    os.chdir("..\data")
    subprocess.check_output("backup.bat", creationflags= 0x08000000)
    print("Done..")
    sys.exit()

