import utils
import sys
import random
import math
import yelp_data_preprocessing
import svd
import extract_feature

all_restaurants = yelp_data_preprocessing.parse_restaurants()
reserved_restaurants = []
for (restaurant,), [reviews] in all_restaurants.items():
    if reviews['review_count'] >= 1:
        reserved_restaurants.append(restaurant)

reserved_restaurants = set(reserved_restaurants)
all_reviews = yelp_data_preprocessing.parse_reviews()

def build_user_and_restaurant_indexed_reviews(all_reviews, user_indexed_reviews, restaurant_indexed_reviews):
    """
    all_reviews is a dictionary {(user_id, business) : [review]}
    user_indexed_reviews is a new review dictionary {user_id : {business_id : [review]}} that can be indexed by user_id
    restaurant_indexed_reviews is a new review dictionary {user_id : {business_id : [review]}} that can be indexed by restaurant_id
    """
    assert len(user_indexed_reviews) == 0, "user_indexed_reviews must be empty"
    assert len(restaurant_indexed_reviews) == 0, "restaurant_indexed_reviews must be empty"

    for (user, restaurant), reviews in all_reviews.items():
        if restaurant not in reserved_restaurants:
            continue
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

def pick_tests(user, user_indexed_reviews, restaurant_indexed_reviews, test_user_data, test_percentage):
    """
    for the current user, pick out test data and delete corresponding entry in indexed reviews. pick out standard, for each picked out restaurant 
    in user's reviews (among other restuarant js), at least min_similarity_num other users have rated both i and j
    """
    def count_common_raters(restaurant_i, restaurant_j, restaurant_indexed_reviews):
        count = 0
        for user in restaurant_indexed_reviews[restaurant_i]:
            if user in restaurant_indexed_reviews[restaurant_j]:
                count += 1
        return count

    total_review_num = len(user_indexed_reviews[user])
    test_review_num = int(total_review_num * test_percentage)
    restaurants = user_indexed_reviews[user].keys();
    restaurant_pair_count = dict()
    restaurant_count = dict()
    for restaurant_i in restaurants:
        count = 0
        for restaurant_j in restaurants:
            if restaurant_i == restaurant_j:
                continue
            pair = tuple(sorted([restaurant_i, restaurant_j]))
            if pair in restaurant_pair_count:
                count += restaurant_pair_count[pair]
            else:
                local_count = count_common_raters(restaurant_i, restaurant_j, restaurant_indexed_reviews)
                count += local_count
                restaurant_pair_count[pair] = local_count
        restaurant_count[restaurant_i] = count
    restaurant_count = restaurant_count.items()
    restaurant_count.sort(key=lambda x:x[1], reverse=True)

    for i in range(test_review_num):
        restaurant = restaurant_count[i][0]
        if restaurant_count[i][1] <= 2 * test_review_num:
            break
        test_user_data[user][restaurant] = user_indexed_reviews[user][restaurant]
        del user_indexed_reviews[user][restaurant]
        del restaurant_indexed_reviews[restaurant][user]

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
            if len(restaurant_indexed_reviews[restaurant]) == 1: # restaurant only has one review, don't delete it
                test_review_num += 1 # go to next item
                continue
            test_user_data[test_user][restaurant] = reviews
            del user_indexed_reviews[test_user][restaurant]
            del restaurant_indexed_reviews[restaurant][test_user]
            if i == test_review_num:
                break

#        pick_tests(test_user, user_indexed_reviews, restaurant_indexed_reviews, test_user_data, test_percentage)
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

def build_restaurant_user_table(restaurant_indexed_reviews, user_indexed_reviews):
    """
    return a dictionary {restaurant_id: {user who rated the resaurant: rating - this user's average rating}}
    """
    def cal_user_average_rating(user_indexed_reviews, user):
        """
        for a given user, calculate this user's average rating for all the reviews in user_indexed_reviews table
        """
        total, count = 0, 0
        for restaurant, reviews in user_indexed_reviews[user].items():
            for review in reviews:
                total += review['stars']
                count += 1
        return 1.0*total/count

    user_average_table = dict()
    restaurant_user_table = dict() 
    for restaurant, user_reviews in restaurant_indexed_reviews.items():
        restaurant_user_table[restaurant] = dict()
        for user, reviews in user_reviews.items():
            if user in user_average_table:
                average = user_average_table[user]
            else:
                average = cal_user_average_rating(user_indexed_reviews, user)
                user_average_table[user] = average
            restaurant_user_table[restaurant][user] = cal_average_rating(reviews) - average#all_restaurants[(restaurant,)][0]["stars"]
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

global_total_count = 0
global_count = 0
global_count2= 0

def CF_evaluating(test_user_data, user_rating_table, item_table):
    """
    calculate evaluations using collaborative filtering
    test_user_data -- {user : {restaurant : [reviews]}}
    user_rating_table --{user : {restaurant : rating}}
    item_table -- {item : {user : rating - average}}
    return evaluations -- {user : {restaurant : (true_rating, prediction)}}
    """
    evaluations = dict() 
    count = 1
    for user in test_user_data:
        count += 1
        count_item = 1
        evaluations[user] = dict()
        for restaurant, reviews in test_user_data[user].items():
            count_item += 1
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
    global global_count, global_total_count
    if item_to_predict in item_rating_table:
        print "The user has rating for this item, don't need predication, return rating"
        return item_rating_table[item_to_predict]
    numerator, denominator = 0.0, 0.0
    for item in item_rating_table:
        similarity = cal_CF_similarity(item_to_predict, item, item_table)
        global_total_count += 1
        if similarity == 0:
            global_count += 1
        numerator += similarity * item_rating_table[item]
        denominator += similarity
    if denominator == 0: 
        prediction = random.randint(1, 10) * 0.5#all_users[(user,)][0]["average_stars"]
    else:
        prediction = numerator/denominator
        if prediction < 0.5:
            prediction = 0.5
    return round(prediction*2)/2

def cal_CF_similarity(item_i, item_j, item_table):
    """
    give a dictionary item_table {item : {user : rating - average}}, 
    return the CF similarity of item_i, item_j
    """
    product, sum_square1, sum_square2 = 0.0, 0.0, 0.0
    global global_count2
    for user in item_table[item_i]:
        if user in item_table[item_j]:
            product += item_table[item_i][user] * item_table[item_j][user]
            sum_square1 += item_table[item_i][user]**2
            sum_square2 += item_table[item_j][user]**2
    if sum_square2 == 0:
        global_count2 += 1
    if sum_square1 == 0 or sum_square2 == 0:
        return 0
    else:
        return abs(product)/math.sqrt(sum_square1 * sum_square2)
                
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
    for user in test_user_data:
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

def svd_evaluating(test_user_data, user_rating_table, number_of_users):
    """
    calculate evaluations using svd
    test_user_data -- {user : {restaurant : [reviews]}}
    user_rating_table --{user : {restaurant : rating}}
    return evaluations -- {user : {restaurant : (true_rating, prediction)}}
    """
    # svd
    svd_model = svd.SVD(number_of_users, len(all_restaurants), user_rating_table)
    svd_model.svd_training(user_rating_table, test_user_data, 30)
    evaluations = svd_model.svd_test(test_user_data)
    return evaluations

def update_training_set(user_indexed_reviews, restaurant_indexed_reviews, training_percentage):
    for user, restaurant_reviews in user_indexed_reviews.items():
        total_reviews = len(restaurant_reviews)
        training_reviews = int(total_reviews * training_percentage)
        if training_reviews <= 0:
            training_reviews = 1 
        delete_reviews = total_reviews - training_reviews
        for i, (restaurant, reviews) in enumerate(restaurant_reviews.items()):
            if i >= delete_reviews:
                break
            del user_indexed_reviews[user][restaurant]
            del restaurant_indexed_reviews[restaurant][user]

def main(argv):
    # set necessary parameters
    review_minimum_num = 50
    test_percentage = 0.1 # percentage of test data in all data set
    training_percentage = 0.25 # percentage of actual training set in all training data 

    # initialize data set
    user_indexed_reviews = dict()  # user -> review
    restaurant_indexed_reviews = dict()  # {'business id': {'user':[review]}}, where review is a dict {'text':"It is good. "}

    # build reviews that can be indexed from both user_id and restaurant_id 
    print "building indexed dictionaries..."
    build_user_and_restaurant_indexed_reviews(all_reviews, user_indexed_reviews, restaurant_indexed_reviews)

    print "setting data for test purposes..."
    test_user_set = get_test_users(user_indexed_reviews, review_minimum_num)
    test_user_data = get_tests_and_update_reviews(user_indexed_reviews, restaurant_indexed_reviews, test_user_set, test_percentage)
    print "total number of users in test_user_data:", len(test_user_data)

    update_training_set(user_indexed_reviews, restaurant_indexed_reviews, training_percentage)

    restaurant_user_table = build_restaurant_user_table(restaurant_indexed_reviews, user_indexed_reviews)
    user_rating_table = build_user_rating_table(user_indexed_reviews)

    # CF evaluation
    print "calculating CF evaluations..."
    CF_evaluations = CF_evaluating(test_user_data, user_rating_table, restaurant_user_table)
    CF_rmse = cal_rmse(CF_evaluations)
    print "final total CF rmse for the test data is:", CF_rmse
    print "global total count is", global_total_count
    print "global count is", global_count
    print "global count2 is", global_count2


#     #random evaluation
#     print "calculating random rmse..."
#     random.seed()
#     random_evaluations = random_evaluating(test_user_data)
#     random_rmse = cal_rmse(random_evaluations)
#     print "final total CF rmse for the test data is:", random_rmse

    # SVD evaluation
#    print "calculating SVD evaluations..."
#    SVD_evaluations = svd_evaluating(test_user_data, user_rating_table, len(user_indexed_reviews))
#    SVD_rmse = cal_rmse(SVD_evaluations)
#    print "final total SVD rmse for the test data is:", SVD_rmse

    #print "calculating SVD evaluations..."
    #SVD_evaluations = svd_evaluating(test_user_data, user_rating_table)
    #SVD_rmse = cal_rmse(SVD_evaluations)
    #print "final total SVD rmse for the test data is:", SVD_rmse

    # Content-based CF
    # restaurant_feature = extract_feature.extracttfidf_restaurant(restaurant_indexed_reviews)

    # Content-boosted CF
#     print "construct classifier for user..."
#     classfiers = extract_feature.construct_classifier_for_user(user_indexed_reviews)
#     print "extract tfidf feature for resaurant..."
#     restaurant_feature = extract_feature.extracttfidf_restaurant(restaurant_indexed_reviews)
#     print "updat user rating table..."
#     user_rating_table = extract_feature.update_rating(restaurant_feature, classfiers, user_rating_table, restaurant_indexed_reviews)
#     #restaurant_user_table = extract_feature.update_difference()

if __name__ == '__main__':
    main(sys.argv)
