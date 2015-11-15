import utils
import sys
import random
import math
import yelp_data_preprocessing
#import pickle

# print "loading all restaurants..."
# all_restaurants = pickle.load(open( "processed_restaurant_data.p", "rb" )) # {(business_id) : [restaurant_info]}
# print "successfully loaded", len(all_restaurants), "restaurants items."

# print "loading all users..."
# all_users = pickle.load(open( "processed_user_data.p", "rb" )) # {(user_id) : [user_info]}
# print "successfully loaded", len(all_users), "user items."

all_restaurants = yelp_data_preprocessing.parse_restaurants()
all_users = yelp_data_preprocessing.parse_users()

for (user,), reviews in all_users.items():
    print user, reviews[0]["average_stars"]

        

def build_user_and_restaurant_indexed_reviews(all_reviews, user_indexed_reviews, restaurant_indexed_reviews):
    """
    all_reviews is a dictionary {(user_id, business) : [review]}
    user_indexed_reviews is a new review dictionary {user_id : {business_id : [review]}} that can be indexed by user_id
    restaurant_indexed_reviews is a new review dictionary {user_id : {business_id : [review]}} that can be indexed by restaurant_id
    """
    assert len(user_indexed_reviews) == 0, "user_indexed_reviews must be empty"
    assert len(restaurant_indexed_reviews) == 0, "restaurant_indexed_reviews must be empty"

    for (user, restaurant), reviews in all_reviews.items():
        if user not in user_indexed_reviews:
            user_indexed_reviews[user] = dict()
        user_indexed_reviews[user][restaurant] = reviews
        if restaurant not in restaurant_indexed_reviews:
            restaurant_indexed_reviews[restaurant] = dict()
        restaurant_indexed_reviews[restaurant][user] = reviews

def get_test_users(user_indexed_reviews, required_review_num):
    """
    give user_indexed_reviews dictionary and required_review_num, 
    return a set of user_id that only contains users who has more than required_review_num reviews
    """
    tested_uid = set()
    for user, reviews in user_indexed_reviews.items():
        if len(reviews) >= required_review_num:
            tested_uid.add(user)
    return tested_uid

def get_qualified_reviews(all_reviews, review_threshold):
    """
    filter all_reviews and return a new review dictionary with the same structure
    that only contains item that user at least reviewed review_threshold restaurants 
    """
    qualified_reviews = dict()
    user_indexed_reviews = get_user_indexed_reviews(all_reviews)
    for (user, restaurant), reviews in all_reviews.items():
        if len(user_indexed_reviews(user)) >= review_threshold:
            qualified_reviews[(user, restaurant)] = reviews
    return qualified_reviews

def get_tests_and_update_reviews(user_indexed_reviews, restaurant_indexed_reviews, test_user_set, test_percentage):
    """
    update user/restaurant_indexed_reviews based on test_user_set, set aside test_percentage reviews from users in test_user_set for testing purposes
    return the dictionary that contains testing data
    """
    test_user_data = dict()
    for test_user in test_user_set:
        test_user_data[test_user] = dict()
        total_review_num = len(user_indexed_reviews[test_user])
        test_review_num = int(total_review_num * test_percentage)
        for i, (restaurant, reviews) in enumerate(user_indexed_reviews[test_user].items()):
            if i == test_review_num:
                break
            if len(restaurant_indexed_reviews[restaurant]) == 1: # restaurant only has one review, don't delete it
                test_review_num += 1 # go to next item
                continue
            test_user_data[test_user][restaurant] = reviews
            del user_indexed_reviews[test_user][restaurant]
            del restaurant_indexed_reviews[restaurant][test_user]
    return test_user_data

def change_training_ratio(user_indexed_reviews, restaurant_indexed_reviews, training_ratio):
    """
    update user/restaurant_indexed_reviews with training_ratio
    """
    if training_ratio == 1:
        return
    for user, restaurant_reviews in user_indexed_reviews.items():        
        review_num = len(restaurant_reviews)
#        print "   before deleting review size:", review_num
        keep_num = min(int(review_num * training_ratio), review_num)
        del_num = review_num - keep_num
        for i, (restaurant, reviews) in enumerate(restaurant_reviews.items()):
            if i == del_num:
                break
            if len(restaurant_indexed_reviews[restaurant]) == 1: # restaurant only has one review, don't delete it
                del_num += 1
                continue
#            print "    del..."
            del user_indexed_reviews[user][restaurant]
            del restaurant_indexed_reviews[restaurant][user]
 #       print "    after deleting review size:", len(user_indexed_reviews[user])

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

def build_restaurant_user_table(restaurant_indexed_reviews):
    """
    return a dictionary {restaurant_id: {user who rated the restaurant: rating - this user's average rating}}
    """
    restaurant_user_table = dict() 
    for restaurant, user_reviews in restaurant_indexed_reviews.items():
        restaurant_user_table[restaurant] = dict()
        for user, reviews in user_reviews.items():
            restaurant_user_table[restaurant][user] = cal_average_rating(reviews) - all_restaurants[(restaurant,)][0]["stars"] #all_users[(user,)][0]["average_stars"]
    return restaurant_user_table

def build_user_rating_table(user_indexed_reviews):
    """
    return a dictionary {user_id: {restaurant_id : rating}}
    """
    user_rating_table = dict()
    for user, restaurant_reviews in user_indexed_reviews.items():
        user_rating_table[user] = dict()
        for restaurant, reviews in restaurant_reviews.items():
            user_rating_table[user][restaurant] = cal_average_rating(reviews)
    return user_rating_table

def CF_evaluating(test_user_data, user_rating_table, item_table):
    """
    calculate evaluations using collaborative filtering
    test_user_data -- {user : {restaurant : [reviews]}}
    user_rating_table --{user : {restaurant : rating}}
    item_table -- {item : {user : rating - average}}
    return evaluations -- {user : {restaurant : (true_rating, prediction)}}
    """
    evaluations = dict() 
#    count = 1
#    print "total number of users to evaluate:", len(test_user_data)
    for user in test_user_data.keys():
#        print "    ", count
#        count += 1
#        count_item = 1
        evaluations[user] = dict()
        for restaurant, reviews in test_user_data[user].items():
#            print "    count item:", count_item
#            count_item += 1
            true_rating = cal_average_rating(reviews)
            prediction = CF_prediction(user_rating_table[user], item_table, restaurant, user)
            evaluations[user][restaurant] = (true_rating, prediction)
    return evaluations

def CF_prediction(item_rating_table, item_table, item_to_predict, user):
    """
    item_rating_table {item : rating}} 
    item_table -- {item : {user : rating - average}} 
    with item in table all being items rated by the user, 
    return a predicated rating for item of the user
    """
    if item_to_predict in item_rating_table:
        print "The user has rating for this item, don't need predication, return rating"
        return item_rating_table[item_to_predict]
    numerator, denominator = 0.0, 0.0
    for item in item_rating_table:
#        key = sort([item_to_predict, item])
        similarity = cal_CF_similarity(item_to_predict, item, item_table)
        numerator += similarity * item_rating_table[item]
        denominator += similarity
    if denominator == 0: 
        prediction = random.randint(1, 10) * 0.5 #all_users[(user,)][0]["average_stars"]
#        print "use average"
    else:
        prediction = numerator/denominator
#        print "not use average"
    return prediction

def cal_CF_similarity(item_i, item_j, item_table):
    """
    give a dictionary item_table {item : {user : rating - average}}, 
    return the CF similarity of item_i, item_j
    """
    product, sum_square1, sum_square2 = 0.0, 0.0, 0.0
#   print "cal item_i:", item_i, ", and item_j:", item_j
#    print len(item_table[item_i].keys())
#    print len(item_table[item_j].keys())
#    print all_restaurants[(item_j,)][0]["review_count"]
    for user in item_table[item_i].keys():
        if user in item_table[item_j].keys():
#            print "get in"
            product += item_table[item_i][user] * item_table[item_j][user]
#            print product
            sum_square1 += item_table[item_i][user]**2
#            print sum_square1
            sum_square2 += item_table[item_j][user]**2
#            print sum_square2
        if sum_square1 == 0 or sum_square2 == 0:
            return 0
        else:
            return product/math.sqrt(sum_square1 * sum_square2)
                
def cal_CF_similarity_table(item_table):
    """
    give a dictionary item_table {item : {user : rating - average}}, 
    return a dictionary {(item_i, item_j): similarity between i,j}, restaurant_i and restaurant_j are sorted in ascending order
    """
    similarities = dict()
    list_of_items = sorted(item_table.keys())
    countnonezero, countzero = 0, 0
    for i, item_i in enumerate(list_of_items[:-1]):
        print "    calcuating:", i
        for j in range(i+1, len(list_of_items)):
            item_j = list_of_items[j]
            similarity = cal_CF_similarity(item_i, item_j, item_table)
            if similarity == 0:
                countzero += 1
            else:
                countnonezero += 1
            similarities[(item_i, item_j)] = similarity
    print "zero items in similarities:", countzero, "none-zero items in similarities:", countnonezero
    return similarities

def random_evaluating(test_user_data):
    """
    calculate evaluations using random prediction
    test_user_data -- {user : {restaurant : [reviews]}}
    return evaluations -- {user : {restaurant : (true_rating, prediction)}}
    """
    evaluations = dict() 
    for user in test_user_data.keys():
        evaluations[user] = dict()
        for restaurant, reviews in test_user_data[user].items():
            true_rating = cal_average_rating(reviews)
            prediction = random.randint(1, 10) * 0.5
            evaluations[user][restaurant] = (true_rating, prediction)
    return evaluations

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

def searchRestaurantsOnDistance(location, restaurants, numRecommendation):
    """
    Give a location (longitude, latitude) and a dictionary of restaurants, return a list of recommended restaurants 
    of length numRecommendation according to the distance, in the form of (distance, restaurant_id, rating) with increasing order of distances
    """
    recommended = []
    for (restaurant,), info in restaurants.items():
        info = info[0]
        restLoc = (info["longitude"], info["latitude"])
        distance = EuclideanDistance(restLoc, location)
        recommended.append((distance, restaurant, info["stars"]))

    recommended = sorted(recommended)
    for distance, restaurant_id, rating in recommended[:numRecommendation]:
        print 'Distance:', distance, ', Restaurant ID:', restaurant_id, ', Rating:', rating
    return recommended[:numRecommendation]

def test_searchRestaurantsOnDistance():
    locations = [(-15, 20), (10, 12), (-40, 40), (0, 15), (15, -20)]
    for location in locations:
        print 'Search location (longitude, latitude) :', location
        print 'Recommendations:'
        searchRestaurantsOnDistance(location, restaurants, 10)
        print ' '

def main(argv):
#     # set necessary parameters
#     review_minimum_num = 50
#     test_percentage = 0.3 # percentage of test data in all data set
#     training_ratio = 1 # percentage of actual training set in all training data 



#     # load data
# #     print "loading all reivews..."
# #     all_reviews = pickle.load(open( "processed_review_data.p", "rb" )) # {(user_id, business_id) : [review]}
# #     print "successfully loaded", len(all_reviews), "review items."
#     all_reviews = yelp_data_preprocessing.parse_reviews()

#     # initialize data set
#     user_indexed_reviews = dict()
#     restaurant_indexed_reviews = dict()

#     # build reviews that can be indexed from both user_id and restaurant_id 
#     print "building indexed dictionaries..."
#     build_user_and_restaurant_indexed_reviews(all_reviews, user_indexed_reviews, restaurant_indexed_reviews)

#     print "setting data for test purposes..."
#     test_user_set = get_test_users(user_indexed_reviews, review_minimum_num)
#     test_user_data = get_tests_and_update_reviews(user_indexed_reviews, restaurant_indexed_reviews, test_user_set, test_percentage)

#     print "changing training_ratio..."
#     change_training_ratio(user_indexed_reviews, restaurant_indexed_reviews, training_ratio)

#     restaurant_user_table = build_restaurant_user_table(restaurant_indexed_reviews)
#     user_rating_table = build_user_rating_table(user_indexed_reviews)

#     # CF evaluation
#     print "calculating CF evaluations..."
# ##     //similarities = cal_CF_similarity(restaurant_user_table)
#     CF_evaluations = CF_evaluating(test_user_data, user_rating_table, restaurant_user_table)
#     CF_rmse = cal_rmse(CF_evaluations)
#     print "final total CF rmse for the test data is:", CF_rmse, ", CF training ratio", training_ratio

#     # random evaluation
# #     print "calculating random rmse..."
# #     random.seed()
# #     random_evaluations = random_evaluating(test_user_data)
# #     random_rmse = cal_rmse(random_evaluations)
# #     print "final total CF rmse for the test data is:", random_rmse
    raise("not implemented")

if __name__ == '__main__':
    main(sys.argv)
