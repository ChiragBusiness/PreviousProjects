import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options

import time
import numpy as np
import pandas as pd
from datetime import datetime
import traceback

import functions_filled_orders
import functions_main

import pickle
import json
import sys

sys.stdout = open("/home/seluser/logging/logs.txt", "a+")
sys.stderr = open("/home/seluser/logging/err.txt", "a+")


print("current time: ")
print(time.time())

#time.sleep(10)



#PATH = "C:\Program Files (x86)\chromedriver.exe"
#capabilities = DesiredCapabilities.CHROME
#capabilities["goog:loggingPrefs"] = {"performance": "ALL"}

chromeOptions = Options()
#chromeOptions.add_argument("--disable-dev-shm-usage")
chromeOptions.headless = True

#driver = webdriver.Chrome(
#    desired_capabilities=capabilities, executable_path=PATH
#)
#driver = webdriver.Chrome(desired_capabilities=capabilities, options=chromeOptions)
driver = webdriver.Chrome(options = chromeOptions)
#driver.maximize_window()

driver.set_window_size(2048, 996) 

driver.get("https://trade.liquidmarketplace.io/login")
print("sleeping for loading the login screen for 10")
time.sleep(10)


driver.find_element(By.XPATH, "//*[@id='root']/div[1]/div/div[2]/div/div/form/div[1]/div/input").send_keys("LilChigga")
driver.find_element(By.XPATH, "//*[@id='root']/div[1]/div/div[2]/div/div/form/div[2]/div/input").send_keys("XgTjUB-*W67tzKg")

driver.find_element(By.XPATH, "//*[@id='root']/div[1]/div/div[2]/div/div/form/button/div").click() #click login
print("sleeping for 10 whilst waiting for base page to load")
time.sleep(10) #wait 10 for everything to load

try:
    driver.find_element(By.XPATH, "//*[@id='root']/div[1]/div/div[2]/div[2]/div[1]/div[2]/div[1]").click() #click cancel the thing
except:
    pass


    

#if len(functions_filled_orders_error):
#    raise IndexError("functions_filled_orders_error")



try:
    with open("/home/seluser/logging/graceful.json", "r") as f:
        graceful = json.load(f)
except:
    graceful = 0

print("graceful: ")
print(graceful)

try:
    if graceful:      

        with open("/home/seluser/logging/asks_dict.pkl", "rb") as f:
            asks_dict = pickle.load(f)

        with open("/home/seluser/logging/bids_dict.pkl", "rb") as f:
            bids_dict = pickle.load(f)

        with open("/home/seluser/logging/master.pkl", "rb") as f:
            master = pickle.load(f)

        with open("/home/seluser/logging/filled_orders.pkl", "rb") as f:
            filled_orders = pickle.load(f)

        errors_dict = {}

        print("no errors getting prev vars")

    else:
        asks_dict, bids_dict, master, errors_dict = functions_main.initialize()
        filled_orders = {}
        #filled_orders["recorded"] = []

        with open("/home/seluser/logging/filled_orders_history.pkl", "rb") as f:
            filled_orders["history"] = pickle.load(f)

        filled_orders["recorded"] = filled_orders["history"].copy()

        #filled_orders["history"] = []

        print("creating new vars")
        
except:
    print("failed initialization")
    raise IndexError("index")

master["ask_vol_ratio_of_balance"] = 0.25
master["bid_vol_ratio_of_balance"] = 0.25


name = ["PUNK", "#013 Crypto Punk #6837"]
#name = ["CHTB", '#018 PSA 10 2002 Pokémon #3 Charizard Reverse Foil Legendary Collection']

functions_filled_orders_error = functions_filled_orders.get_historical_filled_orders(driver, filled_orders, name)
if len(functions_filled_orders_error):
    print(functions_filled_orders_error)
    raise IndexError("functions_filled_orders_error")

sys.stdout.close()
sys.stderr.close()




#asks_dict["open_orders"] = [[0.073, 6]]
#bids_dict["open_orders"] = [[0.065, 28]]

functions_main.main_loop(driver, asks_dict, bids_dict, master, errors_dict, filled_orders)











