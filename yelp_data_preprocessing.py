import utils
import pickle

def printStartParsing(string):
    print "Start parsing", string, "data..."

def printParseSucceed(string):
    print "Successfully parsed", string, "data!"

def printStartSaving(string):
    print "Start saving", string, "to disk..."

def printSaveSucceed(string):
    print "Successfully saved", string, "to disk!"

printStartParsing("reviews")
all_reviews = utils.parseJson(("user_id","business_id"), 'yelp_academic_dataset_review.json')
printParseSucceed("reviews")
printStartSaving("reviews")
pickle.dump(all_reviews, open("processed_review_data.p", "wb"))
printSaveSucceed("reviews")

printStartParsing("restaurants")
all_restaurants = utils.parseJson(("business_id",), 'yelp_academic_dataset_business.json')
printParseSucceed("restaurants")
printStartSaving("restaurants")
pickle.dump(all_restaurants, open("processed_restaurant_data.p", "wb"))
printSaveSucceed("restaurants")

printStartParsing("users")
all_users = utils.parseJson(("user_id",), 'yelp_academic_dataset_user.json')
printParseSucceed("users")
printStartSaving("users")
pickle.dump(all_users, open("processed_user_data.p", "wb"))
printSaveSucceed("users")
