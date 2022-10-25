import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import DesiredCapabilities

import time
import numpy as np
import pandas as pd
from datetime import datetime
import traceback

#commenting below out because there was a circular import error so we moved the two imports below into the main function
#from functions_filled_orders import get_filled_orders
#from functions_filled_orders import get_profit

#master = {}
#master["spread_req"] = 1.1
#master["spread_not_valid_response_v2_ran"] = 0
#master["path_in"] = []
#master["log"] = []
#master["cutoff"] = 20
#master["base_vol"] = 30
#master["to_log"] = 0
#master["ask_vol_ratio_of_balance"] = 0.25
#master["bid_vol_ratio_of_balance"] = 0.25
#master["max_spread"] = 1.15
#master["path"] = []
#master["refresh_variable"] = 0
#master["ried_refresh"] = 0
#master["with_max_spread"] = 0


def scrape_orderbook(driver, asks_dict, bids_dict):
    error = []
    
    try:
        
        orderbook = driver.find_element(By.CLASS_NAME, "orderbook__order-book-body")
        orderbook_data = orderbook.text
        timestamp = time.time()
        #splitted = orderbook_data.split("\nSpread ")
        splitted = orderbook_data.split("\nLast Price")

        asks_dict["base"] = splitted[0].split("\n")
        bids_dict["base"] = splitted[1].split("\n")[1:-4]

        
    except:
        error.append(["scrape orderbook error", traceback.format_exc(), time.time()])
        return error
        
    #if not len(error): #if we are returning error then no need to check for len(error)

    for data in [asks_dict, bids_dict]:
        data["timestamp"] = timestamp

        data["array"] = []
        
        for i in data["base"]:
            data["array"].append(float(i.replace(",", "")))

        data["indx_to_remove"] = []


        try:

            if len(data["array"])%2:

                if len(data["open_orders"]):

                    for o_indx, [o_price, o_quantity] in enumerate(data["open_orders"]):
                        atleast_1 = 0

                        for indx, price in enumerate(data["array"][::2]):


                            if price == o_price:
                                atleast_1 = 1
                                sus_quant = data["array"][indx * 2+2]

                                if int(sus_quant) == sus_quant:

                                    if sus_quant <= o_quantity:
                                        data["indx_to_remove"].append(indx*2 +2)

                                    else:
                                        error.append([data["name"], "error sus_quant > o_quant", timestamp])
                                        return error
                                else:
                                    error.append([data["name"], "error sus quant not int", timestamp])
                                    return error

                        if not atleast_1:
                            error.append([data["name"],  "error order in orderbook but not in open_orders", timestamp])
                            return error

                else:
                    error.append([data["name"],  "error order in orderbook but no open orders", timestamp])
                    return error
        except:

            error.append([data["name"], "error in parsing data", traceback.format_exc(), timestamp])
            return error

        data["open_orders_from_orderbook"] = []

        try:
            if len(data["indx_to_remove"]):
                for indx in np.sort(data["indx_to_remove"])[::-1]:
                    data["open_orders_from_orderbook"].append([data["array"][indx-2], data["array"][indx - 1], data["array"][indx]])
                    del data["array"][indx]
            try:
                data["array"] = np.reshape(data["array"], (-1, 2))
            except:
                #if not len(error):
                error.append([data["name"],  "could not reshape array", traceback.format_exc(), timestamp])
                return error

        except:
            error.append([data["name"], "error in dealing with remove indexes", traceback.format_exc(), timestamp])
            return error
                       
    return error




def check_spread(asks_dict, bids_dict, master): #check if spread is right
    
    error = []
    
    try:
    
        ask_check = asks_dict["proposed"][0] if len(asks_dict["proposed"]) else asks_dict["open_orders"][0]

        bid_check = bids_dict["proposed"][0] if len(bids_dict["proposed"]) else bids_dict["open_orders"][0]

        if ask_check[0] / bid_check[0] <= master["spread_req"]:

            error.append(["check error: spread not meeting req"])
            
    except:
        error.append(["check error: unknown", traceback.format_exc()])
        
    return error




def my_decimal_floor(x, dp):
    return np.floor(x * (10**dp)) / (10**dp)

def my_decimal_ceil(x, dp):
    return np.ceil(x * (10**dp)) / (10**dp)


#instead of passing in individual variables lets make path_in, cutoff, spread_req, base_vol ---> master and just pass in master

#def spread_not_valid_response_v2(asks_dict, bids_dict, path_in, cutoff, spread_req, base_vol):
def spread_not_valid_response_v2(asks_dict, bids_dict, master):
    
    error = []
    timestamp = time.time()
    
    if len(asks_dict["proposed"]) and len(bids_dict["proposed"]): #identifying where problem comes from
        master["path_in"].append(["spread_not_valid_response_v2", 1])
        try:

            ask_orderbook_copy = asks_dict["array"].copy() 
            bid_orderbook_copy = bids_dict["array"].copy()

            if len(asks_dict["open_orders"]): #removing our influence
                
                our_indx_ask = np.where(asks_dict["array"][:,0] == asks_dict["open_orders"][0][0])[0][0]
                ask_orderbook_copy[:,1][our_indx_ask] = asks_dict["array"][:,1][our_indx_ask] - asks_dict["open_orders"][0][1]

                if ask_orderbook_copy[:,1][our_indx_ask] == 0:
                    ask_orderbook_copy = np.delete(ask_orderbook_copy, our_indx_ask, axis = 0)


            if len(bids_dict["open_orders"]): 

                our_indx_bid = np.where(bids_dict["array"][:,0] == bids_dict["open_orders"][0][0])[0][0]
                bid_orderbook_copy[:,1][our_indx_bid] = bids_dict["array"][:,1][our_indx_bid] - bids_dict["open_orders"][0][1] #remove our influence

                if bid_orderbook_copy[:,1][our_indx_bid] == 0:
                    bid_orderbook_copy = np.delete(bid_orderbook_copy, our_indx_bid, axis = 0)


            #find first cutoff both sides
            indx_ask_initial = np.where(np.cumsum(ask_orderbook_copy[:,1][::-1]) > master["cutoff"])[0][0]
            indx_bid_initial = np.where(np.cumsum(bid_orderbook_copy[:,1]) > master["cutoff"])[0][0]


            got_one = 0
            if (ask_orderbook_copy[:,0][::-1][indx_ask_initial] - 0.001) / (bid_orderbook_copy[:,0][indx_bid_initial] + 0.001) > master["spread_req"]: #most favoourable position, this should not be possible because its why we entered this fcking function in the first place but no harm in checking
                asks_dict["proposed"] = np.round([[ask_orderbook_copy[:,0][::-1][indx_ask_initial] - 0.001, master["base_vol"]]], 3).tolist()
                bids_dict["proposed"] = np.round([[bid_orderbook_copy[:,0][indx_bid_initial] + 0.001, master["base_vol"]]], 3).tolist()
                got_one = 1

            else: #goto second and onwards most favourable position
                indx_ask_true = indx_ask_initial
                indx_bid_true = indx_bid_initial
                for i in range(8):

                    indx_ask_initial = indx_ask_true
                    indx_bid_initial = indx_bid_true

                    indx_ask = np.where(np.cumsum(ask_orderbook_copy[:,1][::-1][indx_ask_initial+1:] > master["cutoff"]))[0][0] #second and onwards cutoff
                    indx_bid = np.where(np.cumsum(bid_orderbook_copy[:,1][indx_bid_initial+1:] > master["cutoff"]))[0][0]

                    indx_ask_true = indx_ask_initial + 1 + indx_ask
                    indx_bid_true = indx_bid_initial + 1 + indx_bid



                    if (ask_orderbook_copy[:,0][::-1][indx_ask_true] - 0.001) / (bid_orderbook_copy[:,0][indx_bid_true] + 0.001) > master["spread_req"]:
                        asks_dict["proposed"] = np.round([[ask_orderbook_copy[:,0][::-1][indx_ask_true] - 0.001, master["base_vol"]]], 3).tolist()
                        bids_dict["proposed"] = np.round([[bid_orderbook_copy[:,0][indx_bid_true] + 0.001, master["base_vol"]]], 3).tolist()
                        got_one = 1
                        break
            if not got_one:
                error.append([timestamp, "error spread not valid response we didnt get one lets get em next time"])
                return error
                  
        except:
            error.append([timestamp, traceback.format_exc(), "error spread not valid response with first condition"])
            return error
        

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



    elif len(bids_dict["proposed"]):
        master["path_in"].append(["spread_not_valid_response_v2", 3])
        try:

            if len(asks_dict["open_orders"]): #dont know under which condition we wouldnt have an open ask order at the same time, but it is necessary to find the "bid price needs to be smaller than bit"

                bid_price_needs_to_be_smaller_than = asks_dict["open_orders"][0][0] / master["spread_req"]
                bid_orderbook_copy = bids_dict["array"].copy()

                if len(bids_dict["open_orders"]):


                    our_indx = np.where(bids_dict["array"][:,0] == bids_dict["open_orders"][0][0])[0][0]
                    bid_orderbook_copy[:,1][our_indx] = bids_dict["array"][:,1][our_indx] - bids_dict["open_orders"][0][1] #remove our influence

                    if bid_orderbook_copy[:,1][our_indx] == 0:
                        bid_orderbook_copy = np.delete(bid_orderbook_copy, our_indx, axis = 0)

                try:
                    indx_not_included = np.where(bid_orderbook_copy[:,0] >= my_decimal_floor(bid_price_needs_to_be_smaller_than, 3))[0][-1] #indx to not include when finding indx > cutoff
                except:
                    indx_not_included = -1

                indx = np.where(np.cumsum(bid_orderbook_copy[:,1][indx_not_included+1:]) > master["cutoff"])[0][0]

                bids_dict["proposed"] = [[bid_orderbook_copy[:,0][indx_not_included + 1 + indx] + 0.001, master["base_vol"]]]

                bids_dict["proposed"] = np.round(bids_dict["proposed"], 3).tolist()

            else:
                #error.append(["no open ask order and its not proposed bruh"])
                asks_dict["proposed"] = [[]]
                error = spread_not_valid_response_v2(asks_dict, bids_dict, master) #rerun with placeholder proposed ask
                
        except:
            error.append([timestamp, traceback.format_exc(), "error spread not valid response with third condition"])
            return error
            
    else:
        error.append(timestamp, "wtf nothing to check")
        return error
            
        
    return error

#def check_ask_higher_than_on_hand_avg(asks_dict, bids_dict, master, filled_orders):
    
#    error = []
#    try:
        
#        if len(asks_dict["proposed"]):
#            avg_buy_price = (np.array(filled_orders["on_hand"])[:,0]  * (np.array(filled_orders["on_hand"])[:,1]  / np.array(filled_orders["on_hand"])[:,1].sum())).sum()
#            if asks_dict["proposed"][0][0]  < master["spread_req"] * avg_buy_price:
#                master["path_in"].append(["check_ask_higher_than_on_hand_avg", 1])
#                new_ask_price = my_decimal_ceil(avg_buy_price * master["spread_req"], 3)
#                asks_dict["proposed"][0][0] = new_ask_price
                
#    except:
#        error.append([time.time(), traceback.format_exc(), "check_ask_higher_than_on_hand_avg error"])
        
#    return error

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



class loading_text_gone(object):

    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        element = driver.find_element(*self.locator)   # Finding the referenced element
        if element.text != "Loading...":
            return element.text
        else:
            return False
        
        
        
def cancel_execution_error_retry(driver, master, indx, indxs):
    error = []
    
    try:
        a = np.where(np.sort(indxs)[::-1] == indx)[0][0]

        for indx_2 in indxs[::-1][a:]:
            time.sleep(1.5)
            
            #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]/div[" + str(indx_2 + 1) + "]/div[8]/button").click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]/div[" + str(indx_2 + 1) + "]/div[8]/button"))).click()
            
        master["to_log"] = 1
        
    except:
        error.append([time.time(), traceback.format_exc(), "cancel execution error_retry"])
        return error
        
    return error
        
        
        
        
        
def cancel_orders(driver, asks_dict, bids_dict, master):
    
    error = []
    indxs = []
    timestamp = time.time()
    
    if len(asks_dict["to_cancel"]) or len(bids_dict["to_cancel"]):
        
        master["path_in"].append(["cancel_orders", 1])
        
        try:
            
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[1]/div[1]"))).click() #click open orders            
            open_order_text = WebDriverWait(driver, 5).until(loading_text_gone((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]")))
            #open_order_text = driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]").text #get the open orders text
            open_order_data = np.array(open_order_text.split("\n")).reshape(-1, 8)
        except:
            
            if ["cancel_orders", 2] not in master["path_in"]: #havent run twice (second time with 2s delay between to allow for loading)
                      
                time.sleep(2)
                master["path_in"].append(["cancel_orders", 2])
                error = cancel_orders(driver, asks_dict, bids_dict, master)
                
            else:
                           
                error.append(timestamp, traceback.format_exc(), "cancel error scraping open orders")
                return error
            
        if len(error): #need this beause if we run twice and we have an error on second time aswell, it will return the error to here, but in here (before the inclusion of this clause) we didnt exit so thats why we have it now
            return error


        try:
            if len(asks_dict["to_cancel"]):
                
                if (asks_dict["to_cancel"][0][0] != asks_dict["proposed"][0][0]) or len(asks_dict["vetoed"]): #if the price ofwhat we are cancelling is exactly the same as the new proposal we dont proceed except if its vetoed
                    

                    indxs.append(np.intersect1d(np.where(open_order_data[:,1] == "Sell")[0], np.where(np.asarray(open_order_data[:,4], dtype = "float") == asks_dict["to_cancel"][0][0])[0])[0])
                    master["path_in"].append(["cancel_orders", 3])
                    
        except:
            error.append([timestamp, traceback.format_exc(), "cancel order error ask side"])
        try:
            if len(bids_dict["to_cancel"]):
                
                if (bids_dict["to_cancel"][0][0] != bids_dict["proposed"][0][0]) or len(bids_dict["vetoed"]):
                    
          
                    indxs.append(np.intersect1d(np.where(open_order_data[:,1] == "Buy")[0], np.where(np.asarray(open_order_data[:,4], dtype = "float") == bids_dict["to_cancel"][0][0])[0])[0])
                    master["path_in"].append(["cancel_orders", 4])
                    
        except:
            error.append([timestamp, traceback.format_exc(), "cancel order error bid side"])

        if len(error):
            return error
        else:
            if len(indxs):
                try:
                    for indx in np.sort(indxs)[::-1]:
                        #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]/div[" + str(indx + 1) + "]/div[8]/button").click()
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]/div[" + str(indx + 1) + "]/div[8]/button"))).click()
                        
                        #master["to_log"] += 1
                        
                        #debug_dict["debug"] = [time.time(), "canceled"]
                    master["to_log"] = 1
                    master["path_in"].append(["cancel_orders", 6])

                except:
                    master["path_in"].append(["cancel_orders", 7])
                    error = cancel_execution_error_retry(driver, master, indx, indxs)
                    
                    if len(error):
                        return error

            
                  
    return error


def cancel_all_open_orders(driver):
    #num times ran is an input because of the depreciated cancel_all_open_orders function
    
#//*[@id="test-trading"]/div/div/div[3]/div[2]/div[2]/div/div/div[2]/div[4]/div/button[3]
    error = []
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[2]/div[2]/div/div/div[2]/div[4]/div/button[3]"))).click()
        time.sleep(3)
    except:
        error.append(["error cancelling all orders", traceback.format_exc()])
        return error
    return error


    
    

#just add a 0.5s delay or someshit if to_cancel exists
def update_balance(driver, asks_dict, bids_dict, master):
    error = []
    timestamp = time.time()
    
    try:
        #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[2]").click() #click sell
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[2]"))).click() #click sell
        
        token = float(driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[1]/div[2]/div/span[1]").text.replace(",", "")) #available balance
        
        #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[1]").click() #click buy
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[1]"))).click() #click buy
        
        
        dollars = float(driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[1]/div[2]/div/span[1]").text.replace(",", "")) #available balance
        master["path_in"].append(["update_balance", 1])
        
        if len(asks_dict["to_cancel"]) and master["to_log"] == 1:
            #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[2]").click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[2]"))).click() #click sell
            
            for _ in range(20):
                time.sleep(0.1)
                if float(driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[1]/div[2]/div/span[1]").text.replace(",", "")) != token:
                    token = float(driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[1]/div[2]/div/span[1]").text.replace(",", ""))
                    break
            master["path_in"].append(["update_balance", 2])
                    
        if len(bids_dict["to_cancel"]) and master["to_log"] == 1:
            #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[1]").click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[1]"))).click() #click buy
            
            for _ in range(20):
                time.sleep(0.1)
                if float(driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[1]/div[2]/div/span[1]").text.replace(",", "")) != dollars:
                    dollars = float(driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[1]/div[2]/div/span[1]").text.replace(",", ""))
                    break
            master["path_in"].append(["update_balance", 3])
                
                        
        asks_dict["balance"], bids_dict["balance"] = token, dollars
                        
    except:
        error.append([timestamp, "error updating balance", traceback.format_exc()])
        return error
    
    return error
        





def check_enough_balance(asks_dict, bids_dict):
    
    error = []
    try:
        if len(asks_dict["proposed"]):
            if asks_dict["balance"] < asks_dict["proposed"][0][1]:

                del asks_dict["proposed"][0] #deleting instead of raising an error becauce we dont want to break, we just dont want to proceed further, and the checks for len(proposed ask/bid) achieve this
                #error.append(["not enough balance ask side"])

        if len(bids_dict["proposed"]):
            if bids_dict["balance"] < bids_dict["proposed"][0][0] * bids_dict["proposed"][0][1]:

                del bids_dict["proposed"][0] #deleting instead of raising an error becauce we dont want to break, we just dont want to proceed further, and the checks for len(proposed ask/bid) achieve this
                #error.append(["not enough balance bid side"])
        
    except:
        error.append(["Check_enough_balance unknown error", traceback.format_exc()])
        
    return error



class check_button_text_exit_or_sumbmit(object):

    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        element = driver.find_element(*self.locator)   # Finding the referenced element
        if element.text == "Exit":
            
            return element, 1
        
        elif element.text == "Submit Order":
            
            return element, 2
            
        else:
            return False
        
        
        
        
class check_button_text(object):

    def __init__(self, locator, button_text):
        self.locator = locator
        self.button_text = button_text

    def __call__(self, driver):
        element = driver.find_element(*self.locator)   # Finding the referenced element
        if element.text == self.button_text:
            
            return element
            
        else:
            return False
        
    
def execute(driver, asks_dict, bids_dict, master):
    error = []
    
    master["run_ask"] = 0
    master["run_bid"] = 0
    
    try:
        if len(asks_dict["proposed"]):
            
            if len(asks_dict["open_orders"]):
        
                if (asks_dict["proposed"][0][0] != asks_dict["open_orders"][0][0]) or len(asks_dict["vetoed"]): #this code block is to check if we are not executing something that already exists (to_cancel has this same condition)
                    master["run_ask"] = 1
            else:
                master["run_ask"] = 1
            
            if master["run_ask"] == 1:
                
        
                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[1]/div[1]").click() #click order entry
                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[2]/div/form/div[1]/div/div/label[2]").click()          #click sell depreciated
                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[2]/div/form/div[2]/div[1]/div/div[2]/label[2]").click()   #click limit depreciated
                #limit_quantity_box = driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[2]/div/form/div[2]/div[2]/div/input") depreciated
                #Limit_price_box = driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[2]/div/form/div[2]/div[3]/div/input") depreciated
                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[2]/div/form/div[2]/div[6]/button").click() depreciated

                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[2]").click() #click sell
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[2]"))).click() #click sell


                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[1]/div[1]/div/div/label[1]").click()   #click limit
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[1]/div[1]/div/div/label[1]"))).click()  #click limit


                limit_quantity_box = driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[3]/div/input")

                ask_vol = asks_dict["proposed"][0][1]

                limit_quantity_box.send_keys(Keys.BACKSPACE * 10)
                limit_quantity_box.send_keys(ask_vol)


                Limit_price_box = driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[2]/div/input")
                ask_price = asks_dict["proposed"][0][0]

                Limit_price_box.send_keys(Keys.BACKSPACE * 10)
                Limit_price_box.send_keys(ask_price)



                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[7]/button").click()  #click place order
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[7]/button"))).click() #click place order
                
                
                master["path_in"].append(["execute", 1])

                try:

                    element = WebDriverWait(driver, 5).until(check_button_text((By.XPATH, "/html/body/div[8]/div/div/div[3]/button"), "Confirm"))

                    element.click()

                    element, instruction = WebDriverWait(driver, 5).until(check_button_text_exit_or_sumbmit((By.XPATH, "/html/body/div[8]/div/div/div[3]/button")))

                    if instruction == 1:

                        element.click()
                    elif instruction == 2:

                        element.click()

                        element = WebDriverWait(driver, 5).until(check_button_text((By.XPATH, "/html/body/div[8]/div/div/div[3]/button"), "Exit"))

                        element.click()

                    asks_dict["most_recent_execution"] = asks_dict["proposed"].copy()
                    
                    asks_dict["open_orders"] = asks_dict["proposed"].copy()
                    
                    asks_dict["to_log"] = 1
                    
                    master["path_in"].append(["execute", 2])


                except:

                    error.append([time.time(), "execution error ask order submission", traceback.format_exc()])
                    return error
                    

            else:
                
                master["log"].append([time.time(), "execution failed because exactly the same ask"])

    except:
        
                           
        error.append([time.time(), "execution error ask", traceback.format_exc()])
        return error
                           
            
    try:
        if len(bids_dict["proposed"]):
            
            if len(bids_dict["open_orders"]):
        
                if (bids_dict["proposed"][0][0] != bids_dict["open_orders"][0][0]) or len(bids_dict["vetoed"]):
                    master["run_bid"] = 1
            
            else:
                master["run_bid"] = 1
            
            if master["run_bid"] == 1:
        

                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[1]/div[1]").click() #click order entry
                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[2]/div/form/div[1]/div/div/label[1]").click()          #click buy
                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[2]/div/form/div[2]/div[1]/div/div[2]/label[2]").click()   #click limit
                #limit_quantity_box = driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[2]/div/form/div[2]/div[2]/div/input")
                #Limit_price_box = driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[2]/div/form/div[2]/div[3]/div/input")
                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div/div[2]/div/form/div[2]/div[6]/button").click()   #click place order

                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[1]").click() #click buy
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[1]/div/div/label[1]"))).click() #click buy
                
                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[1]/div[1]/div/div/label[1]").click() #click limit
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[1]/div[1]/div/div/label[1]"))).click()  #click limit

                limit_quantity_box = driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[3]/div/input")

                bid_vol = bids_dict["proposed"][0][1]

                limit_quantity_box.send_keys(Keys.BACKSPACE * 10)
                limit_quantity_box.send_keys(bid_vol)


                Limit_price_box = driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[2]/div/input")
                bid_price = bids_dict["proposed"][0][0]

                Limit_price_box.send_keys(Keys.BACKSPACE * 10)
                Limit_price_box.send_keys(bid_price)


                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[7]/button").click()
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[3]/div[2]/form/div[7]/button"))).click() 
                
                
                master["path_in"].append(["execute", 3])

                try:
                    element = WebDriverWait(driver, 5).until(check_button_text((By.XPATH, "/html/body/div[8]/div/div/div[3]/button"), "Confirm"))

                    element.click()

                    element, instruction = WebDriverWait(driver, 5).until(check_button_text_exit_or_sumbmit((By.XPATH, "/html/body/div[8]/div/div/div[3]/button")))

                    if instruction == 1:
                        element.click()
                    elif instruction == 2:
                        element.click()

                        element = WebDriverWait(driver, 5).until(check_button_text((By.XPATH, "/html/body/div[8]/div/div/div[3]/button"), "Exit"))

                        element.click()

                    bids_dict["most_recent_execution"] = bids_dict["proposed"].copy()
                    
                    bids_dict["open_orders"] = bids_dict["proposed"].copy()
                    
                    bids_dict["to_log"] = 1
                    
                    master["path_in"].append(["execute", 4])

                except:
                    error.append([time.time(), "execution error bid order submission", traceback.format_exc()])
                    return error
            else:
                master["log"].append([time.time(), "execution failed because exactly the same bid"])
                
    except:
        error.append([time.time(), "execution error bid", traceback.format_exc()])
        return error
        
        
    return error


def click_correct_collectible(driver, name):
    error = []

    try:
        
        try:
            time.sleep(3)
            #WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='root']/div[1]/div/div[4]/div[1]/div/div[1]/div[2]/div"))).click() #go pro
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[1]/div/div/button[2]"))).click() #click choose asset
        except:
            driver.find_element(By.XPATH, "//*[@id='root']/div[1]/div/div[2]/div[2]/div[1]/div[1]/div[2]/div[1]/span").click() #cometimes theres a annoying ass finish siginining up before x to proceed bullshit
            time.sleep(3)
            #WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='root']/div[1]/div/div[4]/div[1]/div/div[1]/div[2]/div"))).click() #go pro
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[1]/div/div/button[2]"))).click() #click choose asset
        

        #select_collectible_text = driver.find_element(By.XPATH, "/html/body/div[7]/div/div/div[3]/div[3]").text
        #select_collectible_text = driver.find_element(By.XPATH, "/html/body/div[8]/div/div/div[3]/div[3]/div[1]").text
        select_collectible_text = driver.find_element(By.XPATH, "/html/body/div[8]/div/div/div[3]/div[3]").text
        
        #indx = np.where(np.array(select_collectible_text.split("\n")[::9]) == '#013 Crypto Punk #6837')[0][0]
        #indx = np.where(np.array(select_collectible_text.split("\n")[::9]) == name[1])[0][0]
        indx = np.where(np.array(select_collectible_text.split("\n")[::9]) == name[1])[0][0]
        
        
        #/html/body/div[7]/div/div/div[3]/div[3]/div[1]/div/div[1]/div
        #driver.find_element(By.XPATH, "/html/body/div[7]/div/div/div[3]/div[3]/div[1]/div/div[" + str(indx+1) + "]/div").click() #this stopped working for some reason (click on the element)
        #driver.find_element(By.XPATH, "/html/body/div[8]/div/div/div[3]/div[3]/div[1]/div/div[" + str(indx + 1) + "]").click() #click on the element
        driver.find_element(By.XPATH, "/html/body/div[8]/div/div/div[3]/div[3]/div[" + str(indx+1) + "]/div").click()
    
    # **next bit is commented out because they removed the next page button?**
    #except IndexError:
    #    driver.find_element(By.XPATH, "/html/body/div[7]/div/div/div[3]/div[3]/div[2]/div/a[2]").click() #click next page
    #    time.sleep(0.5)
    #    #select_collectible_text = driver.find_element(By.XPATH, "/html/body/div[7]/div/div/div[3]/div[3]").text
    #    error = click_correct_collectible()
        
    except:
        error.append(["messed up click correct collectible", traceback.format_exc()])
        
    return error


def three(driver, asks_dict, bids_dict, master, errors_dict, filled_orders):
    errors_dict["check_ask_higher_than_on_hand_avg_error"] = check_ask_higher_than_on_hand_avg(asks_dict, bids_dict, master, filled_orders)
    
    if len(errors_dict["check_ask_higher_than_on_hand_avg_error"]):
        master["path_in"].append(["error with check_ask_higher_than_on_hand_avg_error so breaking"])
        print("check_ask_higher_than_on_hand_avg_error")
        return "break"


    cancel_orders_error = cancel_orders(driver, asks_dict, bids_dict, master)
    errors_dict["cancel_orders_error"] = cancel_orders_error
    #print(22)
    master["path_in"].append(27)

    if len(cancel_orders_error):
        #print(23)
        master["path_in"].append(28)
        print("cancel_orders_error")
        return "break"

    else:
        update_balance_error = update_balance(driver, asks_dict, bids_dict, master)
        errors_dict["update_balance_error"] = update_balance_error

        #if len(asks_dict["to_cancel"]) or len(bids_dict["to_cancel"]):
        #    time.sleep(1)
        #    update_balance_error = update_balance()
        #    debug_dict["debug2"] = [time.time(), "updated"]
        #    #print(24)
        #    path_in.append(24)
        #else:
        #    update_balance_error = update_balance()
        #    
        ##    #print(asks_dict["balance"])
        #    #print(bids_dict["balance"])
        #    #print(25)
        master["path_in"].append(29)

        if len(update_balance_error):
            print("update_balance_error")
            #print(26)
            master["path_in"].append(30)
            return "break"

        else:
            if len(asks_dict["proposed"]):

                ask_val = int(master["ask_vol_ratio_of_balance"] * asks_dict["balance"])

                asks_dict["proposed"][0][1] = 1 if ask_val == 0 else ask_val

                #print(27)
                master["path_in"].append(31)

            if len(bids_dict["proposed"]):
                bid_val = int((bids_dict["balance"] * master["bid_vol_ratio_of_balance"]) / bids_dict["proposed"][0][0])

                bids_dict["proposed"][0][1] = 1 if bid_val == 0 else bid_val

                #print(28)
                master["path_in"].append(32)

            check_enough_balance_error = check_enough_balance(asks_dict, bids_dict)
            errors_dict["check_enough_balance_error"] = check_enough_balance_error
            #print(29)
            master["path_in"].append(33)
            if len(check_enough_balance_error):
                print("check_enough_balance_error")
                #print(30)
                master["path_in"].append(34)
                return "break"
            else:
                if len(asks_dict["proposed"]) or len(bids_dict["proposed"]): #must check again because check_enoguh_balance() might have deleted the proposed ask/bid

                    execute_error = execute(driver, asks_dict, bids_dict, master)
                    errors_dict["execute_error"] = execute_error
                    #print(31)
                    master["path_in"].append(35)
                    if len(execute_error):
                        print("execute_error")
                        master["path_in"].append(36)
                        return "break"
                    else:
                        #asks_dict["open_orders"] = asks_dict["proposed"] if len(asks_dict["proposed"]) else asks_dict["open_orders"]
                        #bids_dict["open_orders"] = bids_dict["proposed"] if len(bids_dict["proposed"]) else bids_dict["open_orders"]

                        #asks_dict["most_recent_execution"] = asks_dict["open_orders"].copy()
                        #bids_dict["most_recent_execution"] = bids_dict["open_orders"].copy()
                        #if asks_dict["to_log"] or bids_dict["to_log"] or master["to_log"]:
                        #    master["log"].append([datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), master["to_log"], [asks_dict["array_for_logging_ask"], asks_dict["open_ask_for_logging"], asks_dict["to_cancel"], asks_dict["proposed"], asks_dict["balance"], asks_dict["to_log"]],[bids_dict["array_for_logging_bid"], bids_dict["open_bid_for_logging"], bids_dict["to_cancel"], bids_dict["proposed"], bids_dict["balance"], bids_dict["to_log"]]])
                        #    print(master["log"][-1])
                        
                            master["path_in"].append(37)
                            
                            
                            
def two(driver, asks_dict, bids_dict, master, errors_dict, check_spread_error, filled_orders):
    
    if len(check_spread_error):
        master["path_in"].append(21)
        if len(check_spread_error) == 1 and check_spread_error[0][0] == "check error: spread not meeting req":
            
            error_spread_not_valid = spread_not_valid_response_v2(asks_dict, bids_dict, master)
            errors_dict["error_spread_not_valid"] = error_spread_not_valid
            master["path_in"].append(22)
            
            if len(error_spread_not_valid):
                print("error spread not valid")
                master["path_in"].append(23)
                return "break"
            
            else:
                check_spread_error2 = check_spread(asks_dict, bids_dict, master)
                errors_dict["check_spread_error2"] = check_spread_error2
                if len(check_spread_error2):
                    print("check spread error 2")
                    master["path_in"].append(24)
                    return "continue"
                else:
                    master["path_in"].append(25)
                    return three(driver, asks_dict, bids_dict, master, errors_dict, filled_orders)
                
        else:
            master["path_in"].append(26)
            print("check spread error")
            return "break"
                    
    else:
        return three(driver, asks_dict, bids_dict, master, errors_dict, filled_orders)      
    
    
def one(driver, asks_dict, bids_dict, master, errors_dict, filled_orders):


    check_spread_error = check_spread(asks_dict, bids_dict, master)
    errors_dict["check_spread_error"] = check_spread_error
    #print(20)
    master["path_in"].append(20)

    return two(driver, asks_dict, bids_dict, master, errors_dict, check_spread_error, filled_orders)




"""
FOR TESTING

"""
    
    
def initialize():
    master = {}
    master["spread_req"] = 1.1
    master["cutoff"] = 10
    master["base_vol"] = 30
    master["ask_vol_ratio_of_balance"] = 0.25
    master["bid_vol_ratio_of_balance"] = 0.25
    master["max_spread"] = 1.15
    master["with_max_spread"] = 0
    master["path"] = []
    master["log"] = []
    
    asks_dict = {}
    bids_dict = {}
    
    asks_dict["name"] = "ask"
    bids_dict["name"] = "bid"

    asks_dict["open_orders"] = []
    bids_dict["open_orders"] = []

    asks_dict["proposed"] = []
    bids_dict["proposed"] = []
    
    errors_dict = {}
    
    return asks_dict, bids_dict, master, errors_dict
    
    
def main_loop(driver, asks_dict, bids_dict, master, errors_dict, filled_orders):
    
    
    import sys
    import pickle 
    import json
    import requests

    from functions_filled_orders import get_filled_orders
    from functions_filled_orders import get_profit
    
    #CHANGE THIS FILE TO THE DESIRED LOGGING FILE

    

    master["refresh_variable"] = 0
    master["tried_refresh"] = 0

    broke_because_interruption = 0

    with open("/home/seluser/logging/graceful.json", "w") as f:
        json.dump(0, f)
    

    screenshot_count = 0
    count_print_on_hand = 0
    binary_for_entering = 0
    refresh_timer = time.time()

    #count_for_debugging = 0


    while True:



        


    #for epoch in range(1):

        sys.stdout = open("/home/seluser/logging/logs.txt", "a+")
        sys.stderr = open("/home/seluser/logging/err.txt", "a+")

        if not binary_for_entering:
            print("entered main loop")
            binary_for_entering = 1


        master["path_in"] = []

        master["to_log"] = 0
        
        master["run_ask"] = 0
        master["run_bid"] = 0

        asks_dict["to_log"] = 0
        bids_dict["to_log"] = 0

        errors_dict["orderbook_error"] = []
        errors_dict["main"] = []
        errors_dict["ask_proposal"] = []
        errors_dict["bid_proposal"] = []
        errors_dict["middle_bit"] = []

        errors_dict["check_spread_error"] = []
        errors_dict["error_spread_not_valid"] = []
        errors_dict["check_spread_error2"] = [] 
        errors_dict["check_ask_higher_than_on_hand_avg_error"] = []  
        errors_dict["cancel_orders_error"] = []
        errors_dict["update_balance_error"] = []
        errors_dict["check_enough_balance_error"] = []
        errors_dict["execute_error"] = []
        
        

        driver.save_screenshot("/home/seluser/logging/screenshot" + str(screenshot_count) + ".png")


        screenshot_count += 1
        if screenshot_count == 3:
            screenshot_count =0

        #if not count_for_debugging:
        #    time.sleep(60)
        #    count_for_debugging = 1

        


        errors_dict["orderbook_error"] = scrape_orderbook(driver, asks_dict, bids_dict)


        if len(errors_dict["orderbook_error"]):
            print("orderbook_error")
            break


        try:

            asks_dict["open_orders"] = np.round([[asks_dict["open_orders_from_orderbook"][0][0], asks_dict["open_orders_from_orderbook"][0][2]]], 3).tolist() if len(asks_dict["open_orders_from_orderbook"]) else []
            bids_dict["open_orders"] = np.round([[bids_dict["open_orders_from_orderbook"][0][0], bids_dict["open_orders_from_orderbook"][0][2]]], 3).tolist() if len(bids_dict["open_orders_from_orderbook"]) else []

            with open("/home/seluser/logging/open_ask.json", "w") as f:
                json.dump(asks_dict["open_orders"], f)

            with open("/home/seluser/logging/open_bid.json", "w") as f:
                json.dump(bids_dict["open_orders"], f)

            try:

                if requests.get("http://169.254.169.254/latest/meta-data/spot/termination-time", timeout = 5).status_code == 200: #checking if spot instance termination is requested
                    
                    with open("/home/seluser/logging/asks_dict.pkl", "wb") as f:
                        pickle.dump(asks_dict, f)

                    with open("/home/seluser/logging/bids_dict.pkl", "wb") as f:
                        pickle.dump(bids_dict, f)

                    with open("/home/seluser/logging/master.pkl", "wb") as f:
                        pickle.dump(master, f)

                    with open("/home/seluser/logging/filled_orders.pkl", "wb") as f:
                        pickle.dump(filled_orders, f)

                    with open("/home/seluser/logging/graceful.json", "w") as f:
                        json.dump(1, f)

                    broke_because_interruption = 1

                    print([time.time(), "interruption so breaking"])

                    break

            except:
                pass

            


            asks_dict["to_cancel"] = []
            bids_dict["to_cancel"] = []

            asks_dict["vetoed"] = []
            bids_dict["vetoed"] = []

            open_ask_orders = asks_dict["open_orders"]
            open_bid_orders = bids_dict["open_orders"]

            #ask_orderbook = asks_dict["array"]
            #bid_orderbook = bids_dict["array"]

            proposed_ask = []
            proposed_bid = []


            master["path_in"].append(1)

            if master["with_max_spread"]:

                #max_spread = max_spread_array[0]

                ask_orderbook_copy = asks_dict["array"].copy()
                bid_orderbook_copy = bids_dict["array"].copy()

                if len(asks_dict["open_orders"]):
                    our_indx_ask = np.where(asks_dict["array"][:,0] == asks_dict["open_orders"][0][0])[0][0]

                    ask_orderbook_copy[:,1][our_indx_ask] = asks_dict["array"][:,1][our_indx_ask] - asks_dict["open_orders"][0][1]

                    if ask_orderbook_copy[:,1][our_indx_ask] == 0:

                        ask_orderbook_copy = np.delete(ask_orderbook_copy, our_indx_ask, axis = 0)

                if len(bids_dict["open_orders"]):

                    our_indx_bid = np.where(bids_dict["array"][:,0] == bids_dict["open_orders"][0][0])[0][0]
                    bid_orderbook_copy[:,1][our_indx_bid] = bids_dict["array"][:,1][our_indx_bid] - bids_dict["open_orders"][0][1] #remove our influence

                    if bid_orderbook_copy[:,1][our_indx_bid] == 0:
                        
                        bid_orderbook_copy = np.delete(bid_orderbook_copy, our_indx_bid, axis = 0)


                indx_ask_initial = np.where(np.cumsum(ask_orderbook_copy[:,1][::-1]) > master["cutoff"])[0][0]
                indx_bid_initial = np.where(np.cumsum(bid_orderbook_copy[:,1]) > master["cutoff"])[0][0]

                best_ask_price = ask_orderbook_copy[:,0][::-1][indx_ask_initial]
                best_bid_price = bid_orderbook_copy[:,0][indx_bid_initial]

                midpoint = (best_ask_price + best_bid_price) / 2

                either_side_price = (((master["max_spread"] - 1) * midpoint) / 2)

                bid_restrict = my_decimal_floor(midpoint - either_side_price, 3)

                ask_restrict = my_decimal_ceil(midpoint + either_side_price, 3)

                if best_ask_price > ask_restrict:

                    master["path_in"].append(["1.5 added an ask"])

                    if len(np.where(asks_dict["array"][:,0] == ask_restrict)[0]):
                        asks_dict["array"][np.where(asks_dict["array"][:,0] == ask_restrict)[0][0]][1] = (master["cutoff"] + 1)


                    else:
                        if len(np.where(asks_dict["array"][:,0] < ask_restrict)[0]):
                            first_better = np.where(asks_dict["array"][:,0] < ask_restrict)[0][0]

                            asks_dict["array"] = np.reshape(np.append(np.append(asks_dict["array"][:first_better], [ask_restrict, master["cutoff"] + 1]), asks_dict["array"][first_better:]), (-1, 2))

                        else:

                            asks_dict["array"] = np.reshape(np.append(asks_dict["array"], [ask_restrict, master["cutoff"] + 1]), (-1, 2))

                if best_bid_price < bid_restrict:

                    master["path_in"].append(["1.5 added a bid"])

                    if len(np.where(bids_dict["array"][:,0] == bid_restrict)[0]):
                        bids_dict["array"][np.where(bids_dict["array"][:,0] == bid_restrict)[0][0]][1] = (master["cutoff"] + 1)
                    else:

                        if len(np.where(bids_dict["array"][:,0] > bid_restrict)[0]):

                            last_better = np.where(bids_dict["array"][:,0] > bid_restrict)[0][-1]

                            bids_dict["array"] = np.reshape(np.append(np.append(bids_dict["array"][:last_better + 1], [bid_restrict, master["cutoff"] + 1]), bids_dict["array"][last_better + 1:]), (-1, 2))

                        else:


                            bids_dict["array"] = np.reshape(np.append([bid_restrict, master["cutoff"] + 1], bids_dict["array"]), (-1, 2))

            ask_orderbook = asks_dict["array"]
            bid_orderbook = bids_dict["array"]



        except:
            errors_dict["main"].append([[time.time(), "main error", traceback.format_exc()]])
            break


        try:
            if not len(open_ask_orders): #if no open orders

                if ask_orderbook[-1][1] > master["cutoff"]:
                    proposed_ask.append([ask_orderbook[-1][0]-0.001, master["base_vol"]])
                    #print(2)
                    master["path_in"].append(2)
                else:
                    indx_greater_than_cutoff = -1 - np.where(np.cumsum(ask_orderbook[:,1][::-1]) > master["cutoff"])[0][0]   # if highest ask is less than 20, we dont necessarily want to go on the same level as it, for example maybe the next best is 0.005 away, we then check and go one infromt of that
                    proposed_ask.append([ask_orderbook[indx_greater_than_cutoff][0] - 0.001, master["base_vol"]])
                    #print(3)
                    master["path_in"].append(3)

                    #proposed_ask.append([ask_orderbook[-1][0], 500 - ask_orderbook[-1][1]])

            else:

                if ask_orderbook[-1][0] < open_ask_orders[0][0]: #someone is infront of us
                    if ask_orderbook[-1][1] >  master["cutoff"]:
                        asks_dict["to_cancel"] = asks_dict["open_orders"].copy()
                        #asks_dict["to_cancel"].append([open_ask_orders[0][0], open_ask_orders[0][1]])      
                        proposed_ask.append([ask_orderbook[-1][0] - 0.001, master["base_vol"]])
                        #print(4)
                        master["path_in"].append(4)
                    else:
                        #print(5)

                        #indx_greater_than_cutoff = -1 - np.where(np.cumsum(asks_dict["array"][:,1][::-1]) > cutoff)[0][0]   # if highest ask is less than 20, we dont necessarily want to go on the same level as it, for example maybe the next best is 0.005 away, we then check and go one infromt of that

                        our_indx = np.where(ask_orderbook[:,0][::-1] == open_ask_orders[0][0])[0][0]

                        ask_orderbook_copy = ask_orderbook.copy()
                        ask_orderbook_copy[:,1][::-1][our_indx] = ask_orderbook[:,1][::-1][our_indx] - open_ask_orders[0][1]

                        indx_greater_than_cutoff = -1 - np.where(np.cumsum(ask_orderbook_copy[:,1][::-1]) > master["cutoff"])[0][0]
                        master["path_in"].append(5)

                        #index_unaccounted = np.where(np.cumsum(np.append(ask_orderbook[:,1][::-1][:our_indx], ask_orderbook[:,1][::-1][1 + our_indx:])) > cutoff)[0][0] 

                        #indx_greater_than_cutoff = index_unaccounted if index_unaccounted < our_indx else index_unaccounted+1
                        #indx_greater_than_cutoff = -1 - indx_greater_than_cutoff #index of cutoff not including us

                        if ask_orderbook[indx_greater_than_cutoff][0] - 0.001 != open_ask_orders[0][0]: #if we are not 0.001 less than cutoff (if we should do somthing)
                            asks_dict["to_cancel"] = asks_dict["open_orders"].copy()
                            #asks_dict["to_cancel"].append([open_ask_orders[0][0], open_ask_orders[0][1]])
                            proposed_ask.append([ask_orderbook[indx_greater_than_cutoff][0] - 0.001, master["base_vol"]])
                            #print(6)
                            master["path_in"].append(6)


                        #if ask_orderbook[indx_greater_than_cutoff][0] != open_ask_orders[0][0]: #if we are not the cutoff
                        #    asks_dict["to_cancel"].append(["cancel", open_ask_orders[0][0]])                    
                        #    proposed_ask.append([ask_orderbook[indx_greater_than_cutoff][0] - 0.001, base_vol])
                        #else: #we are the cutoff, eg what happens if there is 1 in front and a bunch behind less than cutoff?
                        #    print("create this bit you lazy")                

                elif ask_orderbook[-1][0] == open_ask_orders[0][0]:  #we are at the front
                    #indx_greater_than_cutoff = -2 - np.where(np.cumsum(ask_orderbook[:,1][:-1][::-1]) > cutoff)[0][0] #cutoff not including us

                    ask_orderbook_copy = ask_orderbook.copy()
                    ask_orderbook_copy[:,1][::-1][0] = ask_orderbook[:,1][::-1][0] - open_ask_orders[0][1]
                    indx_greater_than_cutoff = -1 - np.where(np.cumsum(ask_orderbook_copy[:,1][::-1]) > master["cutoff"])[0][0]
                    master["path_in"].append(7)



                    #if ask_orderbook[-2][0] - open_ask_orders[0][0] > 0.0015: #theres space to move back     IS THIS BIT EVEN NECESSARY, ISNT IT A SUBSET OF THE NE BELOW?           
                    #    asks_dict["to_cancel"].append(["cancel", open_ask_orders[0][0]])
                    #    proposed_ask.append([ask_orderbook[indx_greater_than_cutoff][0] - 0.001, base_vol])
                    #    #print(7)
                    #    path_in.append(7)


                    #else:
                    if ask_orderbook[indx_greater_than_cutoff][0]-0.0015 > open_ask_orders[0][0]: #if we should move back
                        asks_dict["to_cancel"] = asks_dict["open_orders"].copy()
                        #asks_dict["to_cancel"].append([open_ask_orders[0][0], open_ask_orders[0][1]])
                        proposed_ask.append([ask_orderbook[indx_greater_than_cutoff][0] - 0.001, master["base_vol"]])
                        #print(8)
                        master["path_in"].append(8)

                        #elif open_ask_orders[0][1] < (base_vol * 0.8): # what is someone just bought most of the volume, we need to reload at same level but we dont want t
                        #    asks_dict["to_cancel"].append(["cancel", open_ask_orders[0][0]])
                        #    proposed_ask.append([open_ask_orders[0][0], base_vol])

        except:
            errors_dict["ask_proposal"].append([time.time(), "error ask proposal", traceback.format_exc()])


        try:

            if not len(open_bid_orders): #if no open bid orders

                if bid_orderbook[0][1] > master["cutoff"]: # if vol of best bid is higher than cutoff
                    proposed_bid.append([bid_orderbook[0][0]+0.001, master["base_vol"]])
                    #print(9)
                    master["path_in"].append(9)
                else:
                    indx_greater_than_cutoff = np.where(np.cumsum(bid_orderbook[:,1]) > master["cutoff"])[0][0]
                    proposed_bid.append([bid_orderbook[indx_greater_than_cutoff][0] + 0.001, master["base_vol"]])
                    #print(10)
                    master["path_in"].append(10)

            else:

                if bid_orderbook[0][0] > open_bid_orders[0][0]: #someone is infront of us
                    if bid_orderbook[0][1] > master["cutoff"]:

                        bids_dict["to_cancel"] = bids_dict["open_orders"].copy()
                        #bids_dict["to_cancel"].append([open_bid_orders[0][0], open_bid_orders[0][1]])      
                        proposed_bid.append([bid_orderbook[0][0] + 0.001, master["base_vol"]])
                        #print(11)
                        master["path_in"].append(11)
                    else:

                        #our_indx = np.where(ask_orderbook[:,0][::-1] == open_ask_orders[0][0])[0][0]

                        #ask_orderbook_copy = ask_orderbook.copy()
                        #ask_orderbook_copy[:,1][::-1][our_indx] = ask_orderbook[:,1][::-1][our_indx] - open_ask_orders[0][1]

                        #indx_greater_than_cutoff = -1 - np.where(np.cumsum(ask_orderbook_copy[:,1][::-1]) > cutoff)[0][0]




                        #indx_greater_than_cutoff = np.where(np.cumsum(bid_orderbook[:,1]) > cutoff)[0][0]

                        our_indx = np.where(bid_orderbook[:,0] == open_bid_orders[0][0])[0][0]

                        bid_orderbook_copy = bid_orderbook.copy()
                        bid_orderbook_copy[:,1][our_indx] = bid_orderbook[:,1][our_indx] - open_bid_orders[0][1]


                        indx_greater_than_cutoff = np.where(np.cumsum(bid_orderbook_copy[:,1]) > master["cutoff"])[0][0]

                        #index_unaccounted = np.where(np.cumsum(np.append(bid_orderbook[:,1][:our_indx], bid_orderbook[:,1][1 + our_indx:])) > cutoff)[0][0] 

                        #indx_greater_than_cutoff = index_unaccounted if index_unaccounted < our_indx else index_unaccounted+1
                        #print(12)
                        master["path_in"].append(12)

                        if bid_orderbook[indx_greater_than_cutoff][0] + 0.001 != open_bid_orders[0][0]: #if we are not 0.001 greater than cutoff (if we should do somthing)

                            bids_dict["to_cancel"] = bids_dict["open_orders"].copy()
                            #bids_dict["to_cancel"].append([open_bid_orders[0][0], open_bid_orders[0][1]]) 
                            proposed_bid.append([bid_orderbook[indx_greater_than_cutoff][0] + 0.001, master["base_vol"]])
                            #print(13)
                            master["path_in"].append(13)



                        #if bid_orderbook[indx_greater_than_cutoff][0] != open_bid_orders[0][0]: #if we are not the cutoff
                        #    bids_dict["to_cancel"].append(["cancel", open_bid_orders[0][0]])                    
                        #    proposed_bid.append([bid_orderbook[indx_greater_than_cutoff][0] + 0.001, base_vol])
                        #else: #we are the cutoff, eg what happens if there is 1 in front and a bunch behind less than cutoff?
                        #    print("create this bit you lazy bid")                

                elif bid_orderbook[0][0] == open_bid_orders[0][0]:  #we are at the front
                    #indx_greater_than_cutoff = 1 + np.where(np.cumsum(bid_orderbook[:,1][1:]) > cutoff)[0][0] #cutoff not including us

                    bid_orderbook_copy = bid_orderbook.copy()
                    bid_orderbook_copy[:,1][0] = bid_orderbook[:,1][0] - open_bid_orders[0][1]


                    indx_greater_than_cutoff = np.where(np.cumsum(bid_orderbook_copy[:,1]) > master["cutoff"])[0][0]
                    master["path_in"].append(14)




                    #if open_bid_orders[0][0] - bid_orderbook[1][0] > 0.0015: #theres space to move back                
                    #    bids_dict["to_cancel"].append(["cancel", open_bid_orders[0][0]])
                    #    proposed_bid.append([bid_orderbook[indx_greater_than_cutoff][0] + 0.001, base_vol])
                    #    #print(14)
                    #    path_in.append(14)

                    #else:
                    if bid_orderbook[indx_greater_than_cutoff][0] + 0.0015 < open_bid_orders[0][0]: #if we should move back

                        bids_dict["to_cancel"] = bids_dict["open_orders"].copy()
                        #bids_dict["to_cancel"].append([open_bid_orders[0][0], open_bid_orders[0][1]]) 
                        proposed_bid.append([bid_orderbook[indx_greater_than_cutoff][0] + 0.001, master["base_vol"]])
                        #print(15)
                        master["path_in"].append(15)

                        #elif open_bid_orders[0][1] < (base_vol * 0.8): # what is someone just bought most of the volume, we need to reload at same level but we dont want t
                        #    bids_dict["to_cancel"].append(["cancel", open_bid_orders[0][0]])
                        #    proposed_bid.append([open_bid_orders[0][0], base_vol])

        except:
            errors_dict["bid_proposal"].append([time.time(), "error bid_proposal", traceback.format_exc()])

        try:
            #WAIT, we DO NOT WANT TO RELOAD IF PEOPLE ARE ON SAME LEVEL BECAUSE THEY GET PRIORITY                
            if not len(proposed_ask) and len(open_ask_orders): #if we dont have o proposed ask, and we have open order we need to see if our vol is the full base vol or if it has been eaten away and we need to reload

                #if open_ask_orders[0][1] < (0.85*asks_dict["most_recent_execution"][0][1]): # if we have transacted at the ask

                if open_ask_orders[0][1] < (0.85 * asks_dict["balance"] * master["ask_vol_ratio_of_balance"]): # if we have transacted at the ask OR if we have closed a bid that has given us more vol to work with

                    our_indx = np.where(ask_orderbook[:,0] == open_ask_orders[0][0])[0][0]
                    #print(16)
                    master["path_in"].append(16)



                    if ask_orderbook[our_indx][1] - open_ask_orders[0][1] < master["cutoff"]: #if noone else order is on the same level

                        asks_dict["to_cancel"] = asks_dict["open_orders"].copy()
                        #asks_dict["to_cancel"].append([open_ask_orders[0][0], open_ask_orders[0][1]])               
                        proposed_ask.append([asks_dict["open_orders"][0][0], master["base_vol"]])
                        asks_dict["vetoed"].append([1])
                        #print(17)
                        master["path_in"].append(17)

            if not len(proposed_bid) and len(open_bid_orders):

                #if open_bid_orders[0][1] < (0.85 * bids_dict["most_recent_execution"][0][1]):

                if open_bid_orders[0][1] < ((bids_dict["balance"] / open_bid_orders[0][0]) * 0.85 * master["bid_vol_ratio_of_balance"]):


                    our_indx = np.where(bid_orderbook[:,0] == open_bid_orders[0][0])[0][0]
                    #print(18)
                    master["path_in"].append(18)

                    if bid_orderbook[our_indx][1] - open_bid_orders[0][1] < master["cutoff"]:

                        bids_dict["to_cancel"] = bids_dict["open_orders"].copy()
                        #bids_dict["to_cancel"].append([open_bid_orders[0][0], open_bid_orders[0][1]]) 
                        proposed_bid.append([bids_dict["open_orders"][0][0], master["base_vol"]])
                        bids_dict["vetoed"].append([1])
                        #print(19)
                        master["path_in"].append(19)

        except:
            errors_dict["middle_bit"].append([time.time(), "error middle bit", traceback.format_exc()])

        if len(errors_dict["main"]) or len(errors_dict["ask_proposal"]) or len(errors_dict["bid_proposal"]) or len(errors_dict["middle_bit"]):
            break


        proposed_ask = np.round(proposed_ask, 3).tolist()
        proposed_bid = np.round(proposed_bid, 3).tolist()

                #proposed_bid.append([bid_orderbook[0][0], 500 - bid_orderbook[0][1]])

        asks_dict["proposed"] = proposed_ask
        bids_dict["proposed"] = proposed_bid

        if len(asks_dict["proposed"]) or len(bids_dict["proposed"]):

            asks_dict["array_for_logging_ask"] = asks_dict["array"][-5:].copy()
            bids_dict["array_for_logging_bid"] = bids_dict["array"][:5].copy()

            asks_dict["open_ask_for_logging"] = asks_dict["open_orders"].copy()
            bids_dict["open_bid_for_logging"] = bids_dict["open_orders"].copy()

            #check_spread_error = check_spread()    
            state = one(driver, asks_dict, bids_dict, master, errors_dict, filled_orders)
            
            if asks_dict["to_log"] or bids_dict["to_log"] or master["to_log"]:
                master["log"].append([datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), master["to_log"], [asks_dict["array_for_logging_ask"], asks_dict["open_ask_for_logging"], asks_dict["to_cancel"], asks_dict["proposed"], asks_dict["balance"], asks_dict["to_log"]],[bids_dict["array_for_logging_bid"], bids_dict["open_bid_for_logging"], bids_dict["to_cancel"], bids_dict["proposed"], bids_dict["balance"], bids_dict["to_log"]]])
                
                print("latest log: ")
                print(master["log"][-1])
            
            

            if state == "break":

                break

                if master["tried_refresh"] == 0:

                    print("refreshing first time")
                    print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                    print(errors_dict)
                    print(master["path_in"])

                    driver.refresh()


                    time.sleep(10)
                    try:
                        driver.find_element(By.XPATH, "//*[@id='root']/div[1]/div/div[2]/div[2]/div[1]/div[2]/div[1]").click() #click cancel the notification
                    except:
                        pass
                    master["tried_refresh"] = 1
                    master["skip_last_bit"] = 1

                elif master["tried_refresh"] == 1:

                    print("cancelling open_orders and refreshing second time")
                    print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                    print(errors_dict)
                    print(master["path_in"])

                    cancel_all_open_orders_error = cancel_all_open_orders(driver)

                    if len(cancel_all_open_orders_error):
                        print("breaking because cancel all open orders error")
                        print(cancel_all_open_orders_error)                    
                        break
                    else:

                        driver.refresh()  

                        time.sleep(10)
                        try:
                            driver.find_element(By.XPATH, "//*[@id='root']/div[1]/div/div[2]/div[2]/div[1]/div[2]/div[1]").click() #click cancel the notification
                        except:
                            pass
                        master["tried_refresh"] = 2
                        master["skip_last_bit"] = 1
                else:
                    print("breaking because tried refreshing twice alr and didnt work")
                    print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                    print(errors_dict)
                    print(master["path_in"])
                    break


            elif state == "continue":
                master["tried_refresh"] = 0
                master["skip_last_bit"] = 0
                continue

            else:
                master["tried_refresh"] = 0
                master["skip_last_bit"] = 0


        master["path"].append(master["path_in"])


        if not master["skip_last_bit"]:
            time.sleep(30)
            

            try:
                

                errors_dict["get_filled_orders_error"] = get_filled_orders(driver, filled_orders)
                
                if len(errors_dict["get_filled_orders_error"]):
                    print("get_filled_orders_error")
                    print(errors_dict)
                    break

                errors_dict["get_profit_error"] = get_profit(filled_orders)
                
                if len(errors_dict["get_profit_error"]):
                    print("get_profit_error")
                    print(errors_dict)
                    break
                

                tx_closed = np.array(filled_orders["profit"])[np.where(np.array(filled_orders["profit"]) !=0)[0]]

                trigger_for_profit = 0

                count_for_profit = 0

                #for i in np.sign(tx_closed):
                #    if i > 0:
                #        count_for_profit += 1
                #    elif i < 0:
                #        count_for_profit = 0 
                #    if count_for_profit ==3:
                #        trigger_for_profit = 1

                #if trigger_for_profit:

                if tx_closed[-5:].sum() < -1.5:

                    if -1.221 in np.round(tx_closed[-5:], 3).tolist():  #just a measure to impliment one off cases that we want to ignore
                        pass
                    else:
                        print("LOST MONEY BRUVLOST MONEY BRUVLOST MONEY BRUVLOST MONEY BRUVLOST MONEY BRUVLOST MONEY BRUV")
                        print("money_lost: ")
                        print(tx_closed[-5:].sum())
                        print("profit: ")
                        print(filled_orders["profit"])
                        break

                if count_print_on_hand == 45:
                    print("time: ")
                    print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                    print("on hand: ")
                    print(filled_orders["on_hand"])
                    print("last 8 profit:  ")
                    print(filled_orders["profit"][-8:])
                    print("last 8 filled orders:")
                    print(filled_orders["recorded"][:8][::-1])

                    count_print_on_hand = 0
                else:
                    count_print_on_hand += 1

                

            except:
                errors_dict["protection_measure"] = [time.time(), traceback.format_exc()]
                break

            time.sleep(2)

            try:

                if not master["refresh_variable"]:

                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='lightweight-chart']/div[1]/button[2]"))).click() #click 5 minute 

                    master["refresh_variable"] = 1
                else:
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='lightweight-chart']/div[1]/button[3]"))).click()

                    master["refresh_variable"] = 0

            except:
                errors_dict["refresh_error"] = [time.time(), "could not refresh innit", traceback.format_exc()]

        
        if time.time() - refresh_timer >= (120 * 60):

            with open("/home/seluser/logging/filled_orders_history.pkl", "wb") as f:
                pickle.dump(filled_orders["recorded"], f)


            refresh_timer = time.time()

            print("refreshing")
            print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            driver.refresh()


            print("waiting for refresh")
            time.sleep(15)
            print("15 seconds over")

            try:
                driver.find_element(By.XPATH, "//*[@id='root']/div[1]/div/div[2]/div[2]/div[1]/div[2]/div[1]").click() #click cancel the thing
                print("canceled the thing")
            except:
                print("didnt have to cancel the thing")
                pass
            



        

        sys.stdout.close()
        sys.stderr.close()


    sys.stdout = open("/home/seluser/logging/logs.txt", "a+")
    sys.stderr = open("/home/seluser/logging/err.txt", "a+")

    driver.save_screenshot("/home/seluser/logging/screenshot_end.png")
            

    if not broke_because_interruption:       
        print("cancelling all open orders because broke")    
        cancel_all_open_orders_error = cancel_all_open_orders(driver)
        print("error: ")
        print(cancel_all_open_orders_error)

    
    print("last 4 logs:")
    print(master["log"][-4:] if len(master["log"]) >= 4 else master["log"][-len(master["log"]):])
    
    print("last 3 path in from path + most receont path in")
    print(master["path"][-3:] if len(master["path"]) >= 3 else master["path"][-len(master["path"]):])
    print(master["path_in"])
    
    print("last errors _dict: ")
    print(errors_dict)

    print("screenshot_count: ")
    print(screenshot_count)


    get_filled_orders_error = get_filled_orders(driver, filled_orders)
    if len(get_filled_orders_error):
        print("there was an error getting filled orders but printed most recent 4 anyways:")
        
    else:
        print("no error getting filled orders: ")
        

    print(filled_orders["recorded"][:8][::-1] if len(filled_orders["recorded"]) >= 8 else filled_orders["recorded"][:len(filled_orders["recorded"])][::-1])


    get_profit_error = get_profit(filled_orders)
    if len(get_profit_error):
        print("error getting profit but printing anyways")
    else:
        print("no error getting profit: ")

    
        
    print(filled_orders["profit"][-20:] if len(filled_orders["profit"]) >= 20 else filled_orders["profit"][-len(filled_orders["profit"]):])


    print("on_hand:  ")
    print(filled_orders["on_hand"])


    try:

        driver.find_element(By.XPATH, "//*[@id='nav-menu']/div[3]").click() #signout

    except:
        print("failed signout still stopping anyways bru")
    

    sys.stdout.close()
    sys.stderr.close()
    sys.stdout = sys.__stdout__
    sys.sterr = sys.__stderr__
                
    



        #log.append("fin")
        #time.sleep(1)
        #x = input("go again?")

    #log.append([time.time(), "broke", orderbook_error, check_spread_error, cancel_orders_error, update_balance_error, check_enough_balance_error, execute_error])
    #log.append([time.time(), [array_for_logging_ask, open_ask_for_logging, asks_dict["to_cancel"], proposed_ask, asks_dict["balance"]],[array_for_logging_bid, open_bid_for_logging, bids_dict["to_cancel"], proposed_bid, bids_dict["balance"]]])

    #print(time.time())
    #print("broke")
    #asks_dict["to_cancel"] = asks_dict["open_orders"]
    #bids_dict["to_cancel"] = bids_dict["open_orders"]
    #cancel_orders_error = cancel_orders()
    #asks_dict["to_cancel"]  = []
    #bids_dict["to_cancel"] = []
    #log.append([time.time(), "canceled all open_orders error:", cancel_orders_error])
    #print(log[-1])
    



 









            
        
            
