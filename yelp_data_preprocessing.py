import utils
import cPickle

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
#     printStartSaving("reviews")
#     cPickle.dump(all_reviews, open("processed_review_data.p", "wb"), protocol=2)
#     printSaveSucceed("reviews")

def parse_restaurants():
    printStartParsing("restaurants")
    all_restaurants = utils.parseJson(("business_id",), filepath+'yelp_academic_dataset_business.json')
    printParseSucceed("restaurants")
    return all_restaurants
#     printStartSaving("restaurants")
#     cPickle.dump(all_restaurants, open("processed_restaurant_data.p", "wb"), protocol=2)
#     printSaveSucceed("restaurants")

def parse_users():
    printStartParsing("users")
    all_users = utils.parseJson(("user_id",), filepath+'yelp_academic_dataset_user.json')
    printParseSucceed("users")
    return all_users
#     printStartSaving("users")
#     cPickle.dump(all_users, open("processed_user_data.p", "wb"), protocol=2)
#     printSaveSucceed("users")

#parse_reviews()


# review_file = open('processed_review_data.p', 'rb')
# print "start loading all reviews data"
# all_reviews = cPickle.load(review_file)
# print "successfully loaded all reviews data"

# restaurant_file = open('processed_restaurant_data.p', 'rb')
# print "start loading all restaurants data"
# all_restaurants = cPickle.load(restaurant_file)
# print "successfully loaded all restaurants data"
