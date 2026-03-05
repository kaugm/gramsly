#!/usr/bin/python3

'''
Docstring for personal_api.log

CLI script to add a food item's macros (per 100g) to DynamoDB.
'''

import os
from decimal import Decimal
from datetime import datetime
import boto3
import botocore.exceptions


TABLE = "karl-macro-tracker-Table-Food-Data"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE)

class Color:
   RED = '\033[91m'
   BOLD = '\033[1m'
   ENDC = '\033[0m'

class Food():
    def __init__(self):
        '''Instantiate Food object via inputs'''

        # Get input
        self.id = input("Internal ID: ").strip().upper() # Primary Key
        self.fiber = Decimal(input("Fiber per 100g (g): ").strip())


    def log(self):
        '''Update cost attribute for item in DynamoDB'''

        try:
            print('[2] Uploading..')

            response = table.update_item(
                Key={
                    "id": self.id
                },
                UpdateExpression="SET fiber = :f, updated_at = :u",
                ExpressionAttributeValues={
                    ":f": self.fiber,
                    ":u": datetime.now().strftime('%Y%m%d%H%M%S')
                },
                ReturnValues="UPDATED_NEW"
            )

            return f"[3] Success! item:{self.id} updated in DynamoDB.\n[4] Exiting.."
        
        except botocore.exceptions.ClientError as e:
            return f'[3] Error: {e.response["Error"]}'
        except Exception as e:
            return f"[3] Failed! {e}"



if __name__ == '__main__':

    # About
    print(f"\n{Color.BOLD}Enter fiber per 100g{Color.ENDC}")

    # Instantiate Ingredient
    i = Food()

    # Confirm Values
    print(f"\n{Color.BOLD}{i.id} calculated data{Color.ENDC}")
    for key, value in i.__dict__.items():
        print(f"{key}: {value}")

    confirm = input("\n[1] Confirm upload to DynamoDB [Y/N]: ") or "N"

    if confirm.upper() != "Y":
        print("[2] Exiting.. \n")
        os._exit(1)
    
    # Upload to DynamoDB
    print(i.log())
    

    






    