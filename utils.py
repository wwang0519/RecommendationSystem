import json
import math

def isJson(f):
    """                                                                                                                                      
    Returns true if a file ends in .json                                                                                                     
    """
    return len(f) > 5 and f[-5:] == '.json'

def parseJson(keys, json_file):
    """                                                                                                                                     
    Parses a single json file. return a dictionary with KEY = keys and VALUE = items contained in json_file, keys is a tuple that identifies
    the item to be queried in the database, len(keys) can be 1. items is a list such that one key can associate multiple items
    """
    itemList, itemDict = [], {}
    with open(json_file, 'r') as f:
        for line in f:
            itemList.append(json.loads(line))
    for item in itemList:
        item_keys = []
        for key in keys:
            item_keys.append(item[key])
        item_keys = tuple(item_keys)
        if item_keys not in itemDict:
            itemDict[item_keys] = [item]
        else:
            itemDict[item_keys] += [item]
    # make sure the choosing field is a proper key
    # assert len(itemDict) == len(itemList), 'Key choice inappropriate!'
    return itemDict

def printItemsHigherThanThreshold(list_of_items, threshold, number_to_print):
    """
    print first number_to_print items in list_of_items that's higher then threshold. if the number of such items < number_to_print, 
    only qualified items are printed
    """
    list_of_items = sorted(list_of_items, reverse = True)
    items_to_print = []
    for i, item in enumerate(list_of_items):
        if item < threshold:
            break
        else:
            items_to_print.append(item)
    number_to_print = number_to_print if number_to_print < len(items) else len(items)
    print "The total number of qualified items is", i, "The first", number_to_print, "items that's above thresold are:"
    print items[:number_to_print]

def EuclideanDistance(loc1, loc2):
    """
    return the euclideanDistance given two locations loc1 and loc2
    """
    return math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)

def get_subdictionary(dictionary, percent):
    """
    give a dictionary and percentage percent, return a dictionary containing only percent of the original dictionary
    """
    sub_dict_size = int(len(dictionary) * percent)
    count = 0
    subdictionary = dict()
    for key, value in dictionary.items():
        subdictionary[key] = value
        count += 1
        if count > sub_dict_size:
            break
    return subdictionary

def innerProduct(v1, v2):
    """
    compute inner product for two vectors
    """
    innerP = 0.0
    for i in range(len(v1)):
        innerP += v1[i] * v2[i]
    return innerP

def cal_average_rating(reviews): 
    """
    calculate the rating from reviews, if a user has multiple reviews for a restaurant, use the average rating
    """
    rating, count = 0.0, 0
    for review in reviews:
        rating += review["stars"]
        count += 1
    rating /= count
    return rating 

def cal_rmse(evaluation_table):
    """
    give an evaluation_table {test_user_id : {restaurant : (true_rating, prediction)}}, 
    return final rmse
    """
    err, n = 0, 0
    for user, evaluations in evaluation_table.items():
        for restaurant, (true_rating, prediction) in evaluations.items():
            err += (true_rating-prediction)**2
            n += 1
    return math.sqrt(err/n)

