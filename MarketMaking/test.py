#FOR TESTING ON LOCAL MACHINE

#import selenium
#from selenium import webdriver
#from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.common.keys import Keys
#from selenium.webdriver import DesiredCapabilities
#from selenium.webdriver.chrome.options import Options

import time
import numpy as np
import pandas as pd
from datetime import datetime
import traceback

import pickle

import functions_filled_orders
import functions_main

import sys


def test1():
    sys.stdout = open("/home/seluser/logging/logs.txt", "a+")
    while True:
        print("printed")
        time.sleep(1)

    sys.stdout.close()
    sys.stdout = sys.__stdout__

def test2():

    #sys.stdout = open("/home/seluser/logging/logs.txt", "a+")
    while True:
        sys.stdout = open("/home/seluser/logging/logs.txt", "a+")
        print("printed")
        time.sleep(1)
        sys.stdout.close()

    #sys.stdout.close()
    sys.stdout = sys.__stdout__



def test3():
    import pickle

    asks_dict = {}
    asks_dict["open_orders"] = [[0.5, 10]]

    while True:
        with open("/home/seluser/logging/open_ask.pkl", "wb") as f:
            pickle.dump(asks_dict["open_orders"], f)


        with open("/home/seluser/logging/open_ask.pkl", "wb") as f:
            pickle.dump(asks_dict["open_orders"], f)

def test4():
    sys.stdout = sys.__stdout__
    try:
        while True:
            print("test4")
            time.sleep(1)

    except KeyboardInterrupt:
        print("accepted")
        #raise IndexError("raised an index error innit")

def test5():
    with open("./graceful", "wb") as f:
        pickle.dump(1, f)

def test6():
    with open("./graceful", "rb") as f:
        graceful = pickle.load(f)








def test_x():
    #PATH = "C:\Program Files (x86)\chromedriver.exe"
    #capabilities = DesiredCapabilities.CHROME
    #capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
    chromeOptions = Options()
    chromeOptions.headless = True

    #driver = webdriver.Chrome(
    #    desired_capabilities=capabilities, executable_path=PATH
    #)
    #driver = webdriver.Chrome(desired_capabilities=capabilities, options=chromeOptions)
    driver = webdriver.Chrome(options = chromeOptions)
    #driver.maximize_window()

    driver.set_window_size(2048, 996) 

    driver.get("https://google.com")

    driver.save_screenshot("/home/seluser/logging/screenshot0.png")

    print("finished")



elif len(asks_dict["proposed"]):
        
    master["path_in"].append(["spread_not_valid_response_v2", 2])

    try:

        if len(bids_dict["open_orders"]):

            ask_price_needs_to_be_greater_than = bids_dict["open_orders"][0][0]* master["spread_req"]
            ask_orderbook_copy = asks_dict["array"].copy()

            if len(asks_dict["open_orders"]):

                our_indx = np.where(asks_dict["array"][:,0] == asks_dict["open_orders"][0][0])[0][0]
                ask_orderbook_copy[:,1][our_indx] = asks_dict["array"][:,1][our_indx] - asks_dict["open_orders"][0][1]

                if ask_orderbook_copy[:,1][our_indx] == 0:
                    ask_orderbook_copy = np.delete(ask_orderbook_copy, our_indx, axis = 0) 

            try:
                indx_not_included = np.where(ask_orderbook_copy[::-1][:,0] <= my_decimal_ceil(ask_price_needs_to_be_greater_than, 3))[0][-1]

            except:
                indx_not_included = -1

            indx = np.where(np.cumsum(ask_orderbook_copy[::-1][:,1][indx_not_included+1:]) > master["cutoff"])[0][0]

            asks_dict["proposed"] = [[ask_orderbook_copy[:,0][::-1][indx_not_included + 1 + indx] - 0.001, master["base_vol"]]]

            asks_dict["proposed"] = np.round(asks_dict["proposed"], 3).tolist()

        else:
            #error.append(["no open bid order and its not proposed my g get your shit together"])
            bids_dict["proposed"] = [[]] 
            error = spread_not_valid_response_v2(asks_dict, bids_dict, master) #rerun with the first condition satisfied
            
    except:
        error.append([timestamp, traceback.format_exc(), "error spread not valid response with second condition"])
        return error


def check_ask_higher_than_on_hand_avg(asks_dict, bids_dict, master, filled_orders):
    
    error = []
    try:
        
        if len(asks_dict["proposed"]):

            avg_buy_price = (np.array(filled_orders["on_hand"])[:,0]  * (np.array(filled_orders["on_hand"])[:,1]  / np.array(filled_orders["on_hand"])[:,1].sum())).sum()

            if asks_dict["proposed"][0][0] < master["spread_req"] * avg_buy_price:

                ask_orderbook_copy = asks_dict["array"].copy()

                if len(asks_dict["open_orders"]): 

                    our_indx = np.where(asks_dict["array"][:,0] == asks_dict["open_orders"][0][0])[0][0]
                    ask_orderbook_copy[:,1][our_indx] = asks_dict["array"][:,1][our_indx] - asks_dict["open_orders"][0][1]

                    if ask_orderbook_copy[:,1][our_indx] == 0:
                        ask_orderbook_copy = np.delete(ask_orderbook_copy, our_indx, axis = 0)
                        
                try:
                    indx_not_included = np.where(ask_orderbook_copy[::-1][:,0] <= master["spread_req"] * avg_buy_price)[0][-1]
                except:
                    indx_not_included = -1

                indx = np.where(np.cumsum(ask_orderbook_copy[::-1][:,1][indx_not_included+1:]) > master["cutoff"])[0][0]

#                if ask_orderbook_copy[:,0][::-1][indx_not_included + 1 + indx] - 0.001 > master["spread_req"] * avg_buy_price:

#                    asks_dict["proposed"] = [[ask_orderbook_copy[:,0][::-1][indx_not_included + 1 + indx] - 0.001, master["base_vol"]]]

#                else:
                while ask_orderbook_copy[:,0][::-1][indx_not_included + 1 + indx] - 0.001 < master["spread_req"] * avg_buy_price:

                    indx_not_included += indx + 1

                    indx = np.where(np.cumsum(ask_orderbook_copy[::-1][:,1][indx_not_included+1:]) > master["cutoff"])[0][0]

                asks_dict["proposed"] = [[ask_orderbook_copy[:,0][::-1][indx_not_included + 1 + indx] - 0.001, master["base_vol"]]]

                asks_dict["proposed"] = np.round(asks_dict["proposed"], 3).tolist()

                master["path_in"].append(["check_ask_higher_than_on_hand_avg", 1])

                #new_ask_price = my_decimal_ceil(avg_buy_price * master["spread_req"], 3)
                #asks_dict["proposed"][0][0] = new_ask_price
                
    except:
        error.append([time.time(), traceback.format_exc(), "check_ask_higher_than_on_hand_avg error"])
        
    return error