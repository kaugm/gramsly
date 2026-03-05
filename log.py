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
        self.friendly = input("Human Friendly Name: ").strip().title()
        self.size = Decimal(input("Serving Size (g): ").strip())
        self.servings = Decimal(input("Number of Servings: ").strip())
        self.fat = Decimal(input("Fat (g): ").strip())
        self.carbs = Decimal(input("Carbohydrates (g): ").strip())
        self.protein = Decimal(input("Protein (g): ").strip())
        self.cost = Decimal(input("Cost on Receipt ($): ").strip())
        self.unit_size = Decimal(input("Unit Size - 100(g) or 1: ").strip())

        # Calculate ratio for 100g
        self.ratio = 100 / self.size

        # Calculate macros for 100g
        self.per_100g_fat = round(self.ratio * self.fat, 2)
        self.per_100g_carbohydrates = round(self.ratio * self.carbs, 2)
        self.per_100g_protein = round(self.ratio * self.protein, 2)
        self.per_100g_cost = round(self.cost * (100 / (self.servings * self.size)), 2)

    def log(self):
        '''Upload item to DynamoDB'''

        try:
            print('[2] Uploading..')
            item = {
                "id": self.id,
                "friendly_name": self.friendly,
                "carbs": self.per_100g_carbohydrates,
                "protein": self.per_100g_protein,
                "fats": self.per_100g_fat,
                "fiber": 0,
                "cost": self.per_100g_cost,
                "updated_at": datetime.now().strftime('%Y%m%d%H%M%S'),
                "unit_size": self.unit_size
            }

            table.put_item(Item=item)

            return f"[3] Success! Food item added to DynamoDB.\n[4] Exiting.."
        
        except botocore.exceptions.ClientError as e:
            return f'[3] Error: {e.response["Error"]}'
        except Exception as e:
            return f"[3] Failed! {e}"



if __name__ == '__main__':

    # About
    print(f"\n{Color.BOLD}Enter values found on nutrition facts\nFor fruits/vegetables enter size:100 and servings:1{Color.ENDC}")

    # Instantiate Ingredient
    i = Food()

    # Confirm Values
    print(f"\n{Color.BOLD}{i.friendly} calculated data{Color.ENDC}")
    for key, value in i.__dict__.items():
        print(f"{key}: {value}")

    confirm = input("\n[1] Confirm upload to DynamoDB [Y/N]: ") or "N"

    if confirm.upper() != "Y":
        print("[2] Exiting.. \n")
        os._exit(1)
    
    # Upload to DynamoDB
    print(i.log())
    

    






    