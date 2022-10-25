import numpy as np
import pandas as pd
from sklearn.utils import shuffle

##prices = pd.read_pickle("parsed_data/prices")
##np.seterr(divide = "ignore", invalid = "ignore")


def worker(x):
    container = np.array([])
    for i in x:
        
        container = np.append(container, i*i)
        container = np.append(container, y)
        
    return container

def aroon_indicator(window, Tickers):
    q = np.array([])
    
    for i in Tickers:
        Aroon_up = prices.loc[i]["Close"].rolling(window).apply(np.argmax).values / (window-1) * 100
        Aroon_down = prices.loc[i]["Close"].rolling(window).apply(np.argmin).values / (window-1) * 100
        thing = Aroon_up - Aroon_down
        q = np.append(q, thing)
        
    return q


def make_class_multi(col_name, features_date_indexed, Date_array, n_classes):
    
    to_append = np.array([])
    
    for Date1 in Date_array:
        
        the_column = features_date_indexed.loc[Date1, col_name].copy()
        
        if np.sum(the_column.isna()) / len(the_column) > 0.4:
            
            to_append = np.append(to_append, [np.nan] * len(the_column))
            
        else:
            
            cutoffs = [np.nanpercentile(the_column, 100 - i*(100/n_classes)) for i in range(n_classes+1)]
            cutoffs[0] += 1
        
            def map_func(x):

                for i in range(n_classes):
                    if x >= cutoffs[i+1] and x < cutoffs[i]:
                        return i
                    
            mapped = the_column.map(map_func, na_action = "ignore")
            
            to_append = np.append(to_append, mapped)
            
    return to_append


def make_class_binary(col_name, features_date_indexed, Date_array, percentage_cutoff):
    
    to_append = np.array([])
    
    for Date1 in Date_array:
        
        the_column = features_date_indexed.loc[Date1, col_name].copy()
        
        if np.sum(the_column.isna()) / len(the_column) > 0.4:
            
            to_append = np.append(to_append, [np.nan] * len(the_column))
            
        else:
        
            cutoff = np.nanpercentile(the_column, percentage_cutoff)

            def map_func(x):
                if x >= cutoff:
                    return 0
                elif x < cutoff:
                    return 1
                else:
                    return np.nan
                
            binaries = the_column.map(map_func, na_action = "ignore")
            
            to_append = np.append(to_append, binaries)
            
    return to_append


def make_dataset(df, training_window, prediction_window, prediction_date_number, Date_array, cols, pred_col):
    
    training_period = Date_array[prediction_date_number - training_window - prediction_window + 1: prediction_date_number - prediction_window +1]
    prediction_period = Date_array[prediction_date_number]
    
    X_train = shuffle(df.loc[training_period, np.append(cols, pred_col)])
    X_train = X_train.replace([np.inf, -np.inf], np.NaN)
    X_train = X_train.dropna(axis = 0)

    Y_train = X_train.pop(pred_col)
    
    X_test = shuffle(df.loc[prediction_period, np.append(cols, pred_col)])
    X_test = X_test.replace([np.inf, -np.inf], np.NaN)
    X_test = X_test.dropna(axis = 0)
    
    Y_test = X_test.pop(pred_col)
    
    return X_train, X_test, Y_train, Y_test

def make_portfolio(portfolio_length, prob_predictions_0, X_test):  
    
    indexes_of_0 = np.argsort(prob_predictions_0)[::-1][:portfolio_length]
    
    portfolio = list(X_test.iloc[indexes_of_0].index)

    return portfolio


def make_dataset_eval_with_extra_return_40_term(df, training_window, prediction_window, eval_size, prediction_date_number, Date_array, cols, pred_col):
    
    training_period = Date_array[prediction_date_number - training_window - prediction_window + 1: prediction_date_number - prediction_window +1]

    prediction_period = Date_array[prediction_date_number :prediction_date_number + eval_size + 1]
    
    X_train = shuffle(df.loc[training_period, np.append(cols, pred_col)])
    X_train = X_train.replace([np.inf, -np.inf], np.NaN)
    X_train = X_train.dropna(axis = 0)

    Y_train = X_train.pop(pred_col)
    
    
    
    X_test = shuffle(df.loc[prediction_period, np.append(np.append(cols, pred_col), "return_40")])
    X_test = X_test.replace([np.inf, -np.inf], np.NaN)
    X_test = X_test.dropna(axis = 0)
    
    Y_test = X_test.pop(pred_col)
    Y_return_40 = X_test.pop("return_40")
    
    return X_train, X_test, Y_train, Y_test, Y_return_40




    
    
    

    
    
