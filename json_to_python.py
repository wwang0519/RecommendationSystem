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
#    assert len(itemDict) == len(itemList), 'Key choice inappropriate!'
    return itemDict

all_reviews = parseJson(("user_id","business_id"), 'yelp_academic_dataset_review.json')
restaurants = parseJson(("business_id",), 'yelp_academic_dataset_business.json')

def get_restuarant_user_review(all_reviews):
    """
    return a dictionary where key is restaurant_id, value is a dictionary with key = user who rated the resaurant and value is the rating
    """
    def cal_average_rating(reviews):
        rating, count = 0.0, 0
        for review in reviews:
            rating += review["stars"]
            count += 1
        rating /= count
        return rating 
    restaurant_user_review = dict() 
    for (user, restaurant), reviews in all_reviews.items():
        if restuarant not in restaurant_user_review:
            restaurant_user_review[restaurant] = dict()
        restaurant_user_review[restaurant][user] = cal_average_rating(reviews)
    return restaurant_user_review

def cal_CF_similarity():
    """
    return a dictionary where key is (item_i, item_j), value is the similarity between them
    """
    

reviewNum = []
for user in user_review_dict.keys():
    reviewNum.append(len(user_review_dict[user]))

reviewNum = sorted(reviewNum, reverse = True)




#restaurants = parseJson("business_id", 'yelp_academic_dataset_business.json')
# users = parseJson("user_id", "yelp_academic_dataset_user.json")
# reviewNum = []
# for user, info in users.items():
#     reviewNum.append(info["review_count"])
# reviewNum = sorted(reviewNum, reverse = True)


  
for i, key in enumerate(reviewNum):
    if key < 50:
        break
print i
print reviewNum[:20]


def EuclideanDistance(loc1, loc2):
    """
    return the euclideanDistance given two locations loc1 and loc2
    """
    return math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)

def searchRestaurantsOnDistance(location, restaurants, numRecommendation):
    """
    Give a location (longitude, latitude) and a dictionary of restaurants, return a list of recommended restaurants 
    of length numRecommendation according to the distance, in the form of (distance, restaurant_id, rating) with increasing order of distances
    """
    recommended = []
    for restaurant, info in restaurants.items():
        restLoc = (info["longitude"], info["latitude"])
        distance = EuclideanDistance(restLoc, location)
        recommended.append((distance, restaurant, info["stars"]))

    recommended = sorted(recommended)
    for distance, restaurant_id, rating in recommended[:numRecommendation]:
        print 'Distance:', distance, ', Restaurant ID:', restaurant_id, ', Rating:', rating

#    return recommended[:numRecommendation]
# locations = [(-15, 20), (10, 12), (-40, 40), (0, 15), (15, -20)]
# for location in locations:
#     print 'Search location (longitude, latitude) :', location
#     print 'Recommendations:'
#     searchRestaurantsOnDistance(location, restaurants, 10)
#     print ' '
    


                
