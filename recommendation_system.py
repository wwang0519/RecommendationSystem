import utils
import pickle
import sys
import random
import math

print "loading all restaurants..."
all_restaurants = pickle.load(open( "processed_restaurant_data.p", "rb" )) # {(business_id) : [restaurant_info]}
print "successfully loaded", len(all_restaurants), "restaurants items."

print "loading all users..."
all_users = pickle.load(open( "processed_user_data.p", "rb" )) # {(user_id) : [user_info]}
print "successfully loaded", len(all_users), "user items."

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
        total_review_num = len(user_indexed_reviews)
        test_review_num = int(total_review_num * test_percentage)
        for i, (restaurant, reviews) in enumerate(user_indexed_reviews[test_user].items()):
            if len(restaurant_indexed_reviews[restaurant]) == 1: # restaurant only has one review, don't delete it
                test_review_num += 1 # go to next item
                continue
            test_user_data[test_user][restaurant] = reviews
            del user_indexed_reviews[test_user][restaurant]
            del restaurant_indexed_reviews[restaurant][test_user]
            if i == test_review_num:
                break
    return test_user_data

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
    return a dictionary {restaurant_id: {user who rated the resaurant: rating - this user's average rating}}
    """
    restaurant_user_table = dict() 
    for restaurant, user_reviews in restaurant_indexed_reviews.items():
        restaurant_user_table[restaurant] = dict()
        for user, reviews in user_reviews.items():
            restaurant_user_table[restaurant][user] = cal_average_rating(reviews) - all_restaurants[(restaurant,)][0]["stars"]
    return restaurant_user_table

def build_user_rating_table(user_indexed_reviews):
    """
    return a dictionary {user_id: {restaurant_id : rating}}
    """
    user_rating_table = dict()
    for user, restaurant_reviews in user_indexed_reviews.items():
        user_rating_table[user] = dict()
        for restaurant, reivews in restaurant_reviews.items():
            user_rating_table[user][restaurant] = cal_average_rating(reviews)
    return user_rating_table

def cal_evaluations(test_user_data, similarities, user_rating_table):
    """
    calculate evaluations using collaborative filtering
    test_user_data -- {user : {restaurant : [reviews]}}
    similarities -- {(restaurant_i, restaurant_j) : similarity}
    user_rating_table --{user : {restaurant : rating}}
    return evaluations -- {user : {restaurant : (true_rating, prediction)}}
    """
    evaluations = dict() 
    for user in test_user_data.keys():
        evaluations[user] = dict()
        for restaurant, reviews in test_user_data[user].items():
            true_rating = cal_average_rating(reviews)
            prediction = CF_prediction(similarities, user_rating_table, restaurant)
            evaluations[user][restaurant] = (true_rating, prediction)
    return evaluations

def random_evaluations(test_user_data):
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
            prediction = random.randint(2, 10) * 0.5
            evaluations[user][restaurant] = (true_rating, prediction)
    return evaluations

def cal_rmse(evaluation_table):
    """
    give an evaluation_table {test_user_id : {restaurant : (true_rating, prediction)}}, 
    return a list of pairs -- [(user_id, rmse)]
    """
    rmses = [] # (use_id, rmse)
    for user, evaluations in evaluation_table.items():
        err = 0
        n = len(evaluation)
        for restaurant, (true_rating, prediction) in evaluations.items():
            err += (true_rating-prediction)**2
        rmse = math.sqrt(err/n)
        rmses.append((user, rmse))
    return rmses

def cal_CF_similarity(item_table):
    """
    give a dictionary item_table {item : {user : rating - average}}, 
    return a dictionary {(item_i, item_j): similarity between i,j}, restaurant_i and restaurant_j are sorted in ascending order
    """
    similarities = dict()
    list_of_items = sorted(item_table.keys())
    for i, item_i in enumerate(list_of_items[:-1]):
        for j in range(i+1, len(list_of_items)):
            product, sum_square1, sum_square2 = 0, 0, 0
            item_j = list_of_items[j]
            for user in item_table[item_i].keys():
                if user in item_table[item_j].keys():
                    product += item_table[item_i][user] * item_table[item_j][user]
                    sum_square1 += item_table[item_i]**2
                    sum_square2 += item_table[item_j]**2
            similarity[(item_i, item_j)] = product/math.sqrt(sum_square1 * sum_square2)
    return similarities

def CF_prediction(similarities, user_rating_table, item_to_predict):
    """
    give a dictionary similarities{(item_i, item_j) : similarity} and user_rating_table {item : rating}} with
    item in table all being items rated by the user, return a predicated rating for item of the user
    """
    if item_to_predict not in user_rating_table:
        print "The user has rating for this item, don't need predication, return rating"
        return user_rating_table[item_to_predict]
    numerator, denominator = 0.0, 0.0
    for item in user_rating_table:
        key = sort([item_to_predict, item])
        numerator += similarities(tuple(key)) * user_rating_table[item]
        denominator += similarities(tuple(key))
    return numerator/denominator

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
    # set necessary parameters
    review_minimum_num = 50
    test_percentage = 0.3

    # load data
    print "loading all reivews..."
    all_reviews = pickle.load(open( "processed_review_data.p", "rb" )) # {(user_id, business_id) : [review]}
    print "successfully loaded", len(all_reviews), "review items."

    # initialize data set
    user_indexed_reviews = dict()
    restaurant_indexed_reviews = dict()
    training_reviews = dict()
    testing_reviews = dict()

    # build reviews that can be indexed from both user_id and restaurant_id 
    print "building indexed dictionaries..."
    build_user_and_restaurant_indexed_reviews(all_reviews, user_indexed_reviews, restaurant_indexed_reviews)

    print "setting data for test purposes..."
    test_user_set = get_test_users(user_indexed_reviews, review_minimum_num)
    test_user_data = get_tests_and_update_reviews(user_indexed_reviews, restaurant_indexed_reviews, test_user_set, test_percentage)
    
    print "calculating CF similarities..."
    restaurant_user_table = build_restaurant_user_table(restaurant_indexed_reviews)
    similarities = cal_CF_similarity(restaurant_user_table)

    print "predicting..."
    user_rating_table = build_user_rating_table(user_indexed_reviews)
    CF_evaluations = cal_evaluations(test_user_data, similarities, user_rating_table)
    random_evaluations = random_evaluations(test_user_data)

    print "calculating rmse..."
    rmses = cal_rmse(CF_evaluations)
    total_rmse = 0
    for user, rmse in rmses:
        total_rmse += rmse
    print "final total CF rmse for the test data is:", total_rmse

    random.seed()
    print "calculating random rmse..."
    random_rmses = cal_rmse(random_evaluations)
    random_total_rmse = 0
    for user, rmse in random_rmses:
        total_rmse += rmse
    print "final total CF rmse for the test data is:", random_total_rmse
    

if __name__ == '__main__':
    main(sys.argv)
