import utils
import sklearn

def CF_evaluating(test_user_data,user_rating_table,restaurant_features):
    """
    calculate evaluations using collaborative filtering
    test_user_data -- {user : {restaurant : [reviews]}}
    user_rating_table --{user : {restaurant : rating}}
    restaurant_features -- {restaurant: list}, where list is a word vector, mean-centered
    return evaluations -- {user : {restaurant : (true_rating, prediction)}}
    """
    
    print len(test_user_data), " users to predict"
    
    cache = {}
    evaluations = dict()
    count = 0
    for user,item_review_table_test in test_user_data.iteritems():
        print count
        print "this user has ",len(item_review_table_test)," ratings to predict"
        # user -- John, item_review_table_test -- dict{restaurant:[reviews]} the test set for user John
        count = count + 1
        evaluations[user] = dict()
        count1 = 0
        for restaurant,reviews in item_review_table_test.iteritems():
            print "doing prediction for test sample ", count1
            count1 = count1 + 1
            print "calculating true rating"
            true_rating = utils.cal_average_rating(reviews)
            print "calculating prediction"
            prediction = CF_prediction(user_rating_table[user],restaurant_features,restaurant,user,cache)
            evaluations[user][restaurant] = (true_rating,prediction)
        # if count > 100:
        #     break
    return evaluations

def CF_prediction(item_rating_table,restaurant_features,restaurant,user,cache):
    """
    item_rating_table -- {restaurant:rating}, a dict of restaurants that a particular user has reviewed
    restaurant_features -- {restaurant: list}, where list is a word vector, mean-centered
    restaurant: restaurant to predict rating
    user: who we are doing the rating prediction for
    RETURNS predicted rating
    """
    
    if restaurant in item_rating_table:
        print "The user has rating for this item, don't need predication, return rating"
        return item_rating_table[restaurant]
    
    numerator = 0.0
    denominator = 0.0
    
    for item in item_rating_table:
        if (item,restaurant) in cache:
            similarity = cache[(item,restaurant)]
        elif (restaurant,item) in cache:
            similarity = cache[(restaurant,item)]
        else:
            similarity = utils.cal_pearson_corr(restaurant_features[item],restaurant_features[restaurant])
            cache[(item,restaurant)] = similarity
        numerator += similarity * item_rating_table[item]
        denominator += similarity
        
    if  denominator == 0:
        prediction = all_users[(user,)][0]["average_stars"]
    else:
        prediction = numerator / denominator
    
    return prediction