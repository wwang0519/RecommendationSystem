
from sklearn.feature_extraction.text import *

def extracttfidf_restaurant(restaurant_indexed_reviews):
    """
    extract tf-idf feature for each restaurant
    restaurant_indexed_reviews is a new review dictionary {business_id : {user_id : [review]}} that can be indexed by restaurant_id
    return restaurant_features -- {restaurant: sparse array(word vector)}
    """
    restaurant_feature = dict()
    restaurant_all_reviews = []
    for restaurant in restaurant_indexed_reviews:
        reviews_content = ''
        for user in restaurant_indexed_reviews[restaurant]:
            reviews = restaurant_indexed_reviews[restaurant][user]
            for review in reviews:
                reviews_content += review['text'][0:len(review['text'])-1]
        restaurant_all_reviews.append(reviews_content)
    # count words
    vectorizer = TfidfVectorizer(min_df=1)
    word_count = vectorizer.fit_transform(restaurant_all_reviews)
    i = 0
    for restaurant in restaurant_indexed_reviews:
        restaurant_feature[restaurant] = word_count[i, :]
        i = i + 1
    return restaurant_feature

def extracttfidf_user(user_indexed_reviews):
	"""
	extract tf-idf feature for each user
    user_indexed_reviews is a new review dictionary {user_id : {business_id : [review]}} that can be indexed by restaurant_id
	return restaurant_features -- {user: sparse array(word vector)}
	"""
	user_feature = dict()
	user_all_reviews = []
	for user in user_indexed_reviews:
		reviews_content = ''
		for restaurant in user_indexed_reviews[user]:
			reviews = user_indexed_reviews[user][restaurant]
			for review in reviews:
				reviews_content += review['text'][0:len(review['text'])-1]
		user_all_reviews.append(reviews_content)
	# count words
	vectorizer = TfidfVectorizer(min_df=1)
	word_count = vectorizer.fit_transform(user_all_reviews)
	for i, user, value in enumerate(user_indexed_reviews.items()):
		user_feature[user] = word_count[i, :]
	return user_feature