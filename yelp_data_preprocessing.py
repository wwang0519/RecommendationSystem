import utils
#import pickle

filepath = './data/'

def printStartParsing(string):
    print "Start parsing", string, "data..."

def printParseSucceed(string):
    print "Successfully parsed", string, "data!"

def printStartSaving(string):
    print "Start saving", string, "to disk..."

def printSaveSucceed(string):
    print "Successfully saved", string, "to disk!"

def parse_reviews():
    printStartParsing("reviews")
    all_reviews = utils.parseJson(("user_id","business_id"), filepath+'yelp_academic_dataset_review.json')
    printParseSucceed("reviews")
    return all_reviews
    # printStartSaving("reviews")
    # pickle.dump(all_reviews, open("processed_review_data.p", "wb"))
    # printSaveSucceed("reviews")

def parse_restaurants():
    printStartParsing("restaurants")
    all_restaurants = utils.parseJson(("business_id",), filepath+'yelp_academic_dataset_business.json')
    printParseSucceed("restaurants")
    return all_restaurants
# printStartSaving("restaurants")
# pickle.dump(all_restaurants, open("processed_restaurant_data.p", "wb"))
# printSaveSucceed("restaurants")

def parse_users():
    printStartParsing("users")
    all_users = utils.parseJson(("user_id",), filepath+'yelp_academic_dataset_user.json')
    printParseSucceed("users")
    return all_users
# printStartSaving("users")
# pickle.dump(all_users, open("processed_user_data.p", "wb"))
# printSaveSucceed("users")
