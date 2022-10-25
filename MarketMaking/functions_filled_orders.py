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

from functions_main import click_correct_collectible
from functions_main import loading_text_gone


#filled_orders = {}
#filled_orders["recorded"] = []

        

#FILLED ORDERS STUFF        

def goto_page(driver, page_num_wanted):
    error = []
    try:
        page_num_current = int(driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[2]/div/div").text)

        if page_num_current > page_num_wanted:
            num_times = page_num_current - page_num_wanted
            for _ in range(num_times):
                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[2]/span[1]").click()
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[2]/span[1]"))).click() #click go prev page
                
                time.sleep(0.1)
                
        elif page_num_current < page_num_wanted:
            num_times = page_num_wanted - page_num_current
            for _ in range(num_times):
                #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[2]/span[2]").click()
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[2]/span[2]"))).click() #click go forward
                time.sleep(0.1) 
                
        if int(driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[2]/div/div").text) != page_num_wanted:
            error.append([time.time(), "error not syntax just couldent get to it", traceback.format_exc()])
            return error
                         
    except:
        error.append([time.time(), "error goto page", traceback.format_exc()])
        return error
        
    return error


def get_all_filled_orders(driver, filled_orders):
    error = []
    
    try:
    
        try:
            page_num = 1
            while True:
                goto_page(driver, page_num)
                open_order_text = WebDriverWait(driver, 5).until(loading_text_gone((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]")))
                filled_orders_array = np.array(open_order_text.split("\n")).reshape(-1, 9) 
                page_num += 1

        except ValueError: #once there is an error we know we have reached the last page
            for page_num_in in range(1, page_num)[::-1]:
                error_goto_page = goto_page(driver, page_num_in)
                
                if not len(error_goto_page):
                    open_order_text = WebDriverWait(driver, 5).until(loading_text_gone((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]")))
                    filled_orders_array = np.array(open_order_text.split("\n")).reshape(-1, 9)

                    filled_orders["recorded"] = np.reshape(np.append(filled_orders_array, filled_orders["recorded"]), (-1, 9))
                else:                    
                    return error_goto_page
        except:
            error.append([time.time(), "get all filled_orders_error not ValueError", traceback.format_exc()])
            return error
                
    except:
        error.append([time.time(), "get all filled_orders_error", traceback.format_exc()])
        return error
        
    return error
            
    
    

def get_filled_orders(driver, filled_orders):

    error = []
  
    try:
        #driver.find_element(By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[1]/div[2]").click() #click filled orders
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[1]/div[2]"))).click() #click filled orders
    
        if len(filled_orders["recorded"]):


            for page_num in range(1, 20):


                error_goto_page = goto_page(driver, page_num)
                open_order_text = WebDriverWait(driver, 5).until(loading_text_gone((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]"))) ##get the filled orders text after loading text is gone
                
                if open_order_text == "No data is available":
                    
                    if page_num == 1:
                        break
                        
                    else:
                        for page_num_in in range(1, page_num)[::-1]:
                            
                            error_goto_page = goto_page(driver, page_num_in)
                            open_order_text = WebDriverWait(driver, 5).until(loading_text_gone((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]")))


                            filled_orders_array = np.array(open_order_text.split("\n")).reshape(-1, 9) ##get the filled orders text after loading text is gone

                            if not len(error_goto_page):
                                filled_orders["recorded"] = np.reshape(np.append(filled_orders_array, filled_orders["recorded"]), (-1, 9))
                            else:                                    
                                return error_goto_page

                    
                    break
                    
                
                filled_orders_array = np.array(open_order_text.split("\n")).reshape(-1, 9) ##get the filled orders text after loading text is gone

                #print(page_num)

                try:

                    if not len(error_goto_page):

                        try:

                            indx = np.where(filled_orders_array[:,0] == filled_orders["recorded"][0][0])[0][0] #where the last recorded item is in new data
                            filled_orders["recorded"] = np.reshape(np.append(filled_orders_array[:indx], filled_orders["recorded"]), (-1, 9)) #we can do this because 

                        except IndexError:

                            continue #goto nex page if there is an index error (the last recorded cannot be found on the page)
                        
                        except:
                            error.append([time.time(), "get_filled_orders_error not an index error", traceback.format_exc()])
                            return error

                        if page_num > 1:

                            for page_num_in in range(1, page_num)[::-1]: #means page num will not be included which is why we do it for the actual page number above

                                #print("in " + str(page_num_in))

                                error_goto_page = goto_page(driver, page_num_in)
                                open_order_text = WebDriverWait(driver, 5).until(loading_text_gone((By.XPATH, "//*[@id='test-trading']/div/div/div[3]/div[4]/div/div[2]/div/div[1]/div/div/div[3]")))
                                
                                
                                filled_orders_array = np.array(open_order_text.split("\n")).reshape(-1, 9) ##get the filled orders text after loading text is gone

                                if not len(error_goto_page):
                                    filled_orders["recorded"] = np.reshape(np.append(filled_orders_array, filled_orders["recorded"]), (-1, 9))
                                else:                                    
                                    return error_goto_page
                                    

                        break

                    else:
                        return error_goto_page

                except:
                    error.append([time.time(), "error get_filled_orders middle bit", traceback.format_exc()])
                    return error
                    
        else:
            get_all_filled_orders_error = get_all_filled_orders(driver, filled_orders)
            if len(get_all_filled_orders_error):
                return get_all_filled_orders_error



    except:
        error.append([time.time(), "error get_filled_orders whole", traceback.format_exc()])
        return error
        
    return error


def get_profit(filled_orders):
    error = []
    
    on_hand = []
    
    profit = []
    
    try:
            
        for data in filled_orders["recorded"][::-1]:

            if data[2] == "Buy":

                on_hand.append([float(data[4]), float(data[3])]) #price quantity

                profit.append(0)

            elif data[2] == "Sell":

                sell_price = float(data[4])

                sell_quantity = float(data[3])

                profit_in = 0

                on_hand_copy = on_hand.copy()

                satisfied_quantity = 0

                on_hand_array = np.asarray(on_hand)
                indxs_less_than = np.where(on_hand_array[:,0] < sell_price)
                sorted_indx = np.argsort(on_hand_array[:,0])

                if len(indxs_less_than[0]):

                    instruction_indx = np.append(sorted_indx[np.nonzero(np.in1d(sorted_indx, indxs_less_than))][::-1], sorted_indx[np.nonzero((np.in1d(sorted_indx, indxs_less_than) == 0))]).tolist()
                    

                else:
                    instruction_indx = sorted_indx
                


                #for buy_price, buy_quantity in on_hand_array[instruction_indx].tolist():

                marked = 0

                for indx in instruction_indx:
                    buy_price, buy_quantity = on_hand[indx]

                    if buy_quantity > (sell_quantity - satisfied_quantity):

                        profit_in += (sell_quantity - satisfied_quantity)*(sell_price*(1-2.5/100) - buy_price*(1+2.5/100))

                        #on_hand_copy[0][1] = on_hand_copy[0][1] - (sell_quantity - satisfied_quantity)

                        on_hand_copy[indx][1] = on_hand_copy[indx][1] - (sell_quantity - satisfied_quantity)

                        break

                    elif buy_quantity == (sell_quantity - satisfied_quantity):

                        profit_in += (sell_quantity - satisfied_quantity)*(sell_price*(1-2.5/100) - buy_price*(1+2.5/100))

                        #on_hand_copy[0][1] = on_hand_copy[0][1] - (sell_quantity - satisfied_quantity)

                        #on_hand_copy[indx][1] = on_hand_copy[indx][1] - (sell_quantity - satisfied_quantity)

                        on_hand_copy[indx][0] = "marked"

                        marked = 1

                        break




                    else:
                        profit_in += buy_quantity*(sell_price*(1-2.5/100) - buy_price*(1+2.5/100))

                        satisfied_quantity += buy_quantity

                        #del on_hand_copy[0]fil

                        on_hand_copy[indx][0] = "marked"

                        marked = 1

                
                if marked: 
                    for indx_del in np.sort(np.where(np.asarray(on_hand_copy)[:,0] == "marked")[0])[::-1]:
                        del on_hand_copy[indx_del]


                profit.append(profit_in)

                on_hand = on_hand_copy
                            
        filled_orders["profit"] = profit
        filled_orders["on_hand"] = on_hand
                
    except:
        error.append([time.time(), "get_profit_error", traceback.format_exc()])
        return error
    
    return error
    
    
#name consists of [symbol, full name] for example: name = ["PUNK", "#013 Crypto Punk #6837"]
#other name is ["CHTB", '#018 PSA 10 2002 Pokémon #3 Charizard Reverse Foil Legendary Collection']

def get_historical_filled_orders_legacy(driver, filled_orders, name):
    
    error = []
    
    try:


        
        if not len(filled_orders["history"]):
        
            driver.find_element(By.XPATH, "//*[@id='wallets-link']").click() #click wallets

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='root']/div[1]/div/div[4]/div/div/div/div[2]/div/div[1]/div[2]/div"))).click() #click view all

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='root']/div[1]/div/div[4]/div/div/div/div[2]/div/div[2]/div/div[1]/div/div/div[3]"))).click() #click buy
            time.sleep(5)

            buys = np.reshape(driver.find_element(By.XPATH, "//*[@id='root']/div[1]/div/div[4]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]").text.split("\n"), (-1,5))

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='root']/div[1]/div/div[4]/div/div/div/div[2]/div/div[2]/div/div[1]/div/div/div[4]"))).click() #click sell
            time.sleep(5)

            sells = np.reshape(driver.find_element(By.XPATH, "//*[@id='root']/div[1]/div/div[4]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]").text.split("\n"), (-1,5))

            only_punk_buys = np.array([])

            for indx, i in enumerate(buys[:,0].tolist()):
                if name[0] in i:
                    only_punk_buys = np.append(only_punk_buys, buys[indx])

            only_punk_sells = np.array([]) 

            for indx, i in enumerate(sells[:,0].tolist()):
                if name[0] in i:
                    only_punk_sells = np.append(only_punk_sells, sells[indx])

            only_punk_buys = np.reshape(only_punk_buys, (-1, 5))
            only_punk_sells = np.reshape(only_punk_sells, (-1, 5))

            only_punk_buys = np.concatenate((np.reshape(np.ones(len(only_punk_buys[:,0])), (-1, 1)), only_punk_buys), axis = 1)

            only_punk_buys[:,0] = "Buy"

            only_punk_sells = np.concatenate((np.reshape(np.zeros(len(only_punk_sells[:,0])), (-1, 1)), only_punk_sells), axis = 1)

            only_punk_sells[:,0] = "Sell"

            buys_and_sells = np.reshape(np.append(only_punk_buys, only_punk_sells), (-1, 6))

            test = np.array([])
            for i in buys_and_sells[:,1]:
                test = np.append(test, float(i.split(" ")[0]))

            buys_and_sells[:,1] = test

            test = np.array([])
            for i in buys_and_sells[:,2]:
                test = np.append(test, float(i.split(" ")[0]))

            buys_and_sells[:,2] = test

            test = np.array([])
            for i in buys_and_sells[:,3]:
                test = np.append(test, float(i.split(" ")[0]))

            buys_and_sells[:,3] = test 

            for_datetime = []

            for date_1, time_1 in zip(buys_and_sells[:,4], buys_and_sells[:,5]):
                for_datetime.append([date_1 + " " + time_1])

            for_datetime = [datetime.strptime(i[0], '%m/%d/%Y %H:%M:%S') for i in for_datetime]

            buys_and_sells = np.concatenate((buys_and_sells, np.reshape(np.array(for_datetime), (-1, 1))), axis = 1)

            buys_and_sells_df = pd.DataFrame(buys_and_sells).set_index(6)

            buys_and_sells_sorted = buys_and_sells_df.sort_index(ascending = False).values

            buys_and_sells_sorted = np.concatenate((buys_and_sells_sorted[:,4:], buys_and_sells_sorted[:,:4]), axis = 1)

            a = np.array(np.reshape((np.float64(buys_and_sells_sorted[:,5]) - np.float64(buys_and_sells_sorted[:,4])) / np.float64(buys_and_sells_sorted[:,3]), (-1, 1)), dtype = "U32") #finding price from fee, amount and total price

            buys_and_sells_sorted = np.concatenate((buys_and_sells_sorted, a), axis = 1)

            test = np.concatenate((buys_and_sells_sorted[:,:4], np.reshape(buys_and_sells_sorted[:,-1], (-1, 1))), axis = 1)

            filled_orders["backup"] = filled_orders["recorded"].copy()

            filled_orders["history"] = np.array(np.concatenate((test, np.reshape(np.zeros(len(test) * 4), (-1, 4))), axis = 1), dtype = "U32")

            already_had_history = 0

            print("filled_orders_history[:5] : ")

            print(filled_orders["history"][:5])

        else:
            already_had_history = 1

        print("already_had history: ")
        print(already_had_history)



        #filled_orders["recorded"] = []

        driver.find_element(By.XPATH, "//*[@id='navButtons']/div[4]/a").click() #click market


        error_test = click_correct_collectible(driver, name)

        if len(error_test):
            return error_test

        else:
            error_get_filled_orders = get_filled_orders(driver, filled_orders)

            if len(error_get_filled_orders):

                return error_get_filled_orders

            else:

                if not already_had_history:

                    filled_orders["recorded"] = np.concatenate((filled_orders["recorded"], filled_orders["history"][len(filled_orders["recorded"]):]), axis = 0) if len(filled_orders['recorded']) else filled_orders["history"]

                error_profit = get_profit(filled_orders)

                if len(error_profit):

                    return error_profit

                else:
                    print("recorded: ")
                    print(filled_orders["recorded"])

                    print("profit: ")
                    print(filled_orders["profit"])

                    print("on_hand: ")
                    print(filled_orders["on_hand"])
                    
                    
    except:
        error.append([time.time(), "error get_historical_filled_orders", traceback.format_exc()])
        
    return error


def get_historical_filled_orders(driver, filled_orders, name):
    
    error = []
    
    try:

        #already_had_history = 1

        #print("already_had history: ")
        #print(already_had_history)



        #filled_orders["recorded"] = []

        driver.find_element(By.XPATH, "//*[@id='navButtons']/div[4]/a").click() #click market


        error_test = click_correct_collectible(driver, name)

        if len(error_test):
            return error_test

        else:

            error_get_filled_orders = get_filled_orders(driver, filled_orders)

            if len(error_get_filled_orders):

                return error_get_filled_orders

            else:

                #if not already_had_history:

                #    filled_orders["recorded"] = np.concatenate((filled_orders["recorded"], filled_orders["history"][len(filled_orders["recorded"]):]), axis = 0) if len(filled_orders['recorded']) else filled_orders["history"]

                error_profit = get_profit(filled_orders)

                if len(error_profit):

                    return error_profit

                else:
                    print("recorded: ")
                    print(filled_orders["recorded"])

                    print("profit: ")
                    print(filled_orders["profit"])

                    print("on_hand: ")
                    print(filled_orders["on_hand"])
                    
                    
    except:
        error.append([time.time(), "error get_historical_filled_orders", traceback.format_exc()])
        
    return error
                
                
            
            
    
    
    
    
    
    
    
    
    
    
    
    