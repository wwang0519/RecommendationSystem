
from sklearn.feature_extraction.text import *
from sklearn.naive_bayes import *
import numpy as np
import utils

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
    user_indexed_reviews is a new review dictionary {user_id : {business_id : [review]}} that can be indexed by user_id
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
	i = 0
	for user in user_indexed_reviews:
		user_feature[user] = word_count[i, :]
		i = i + 1
	return user_feature

def extracttfidf_user(user_indexed_reviews, all_reviews, restaurant_indexed_reviews):
	"""
	extract tf-idf feature for every user
    user_indexed_reviews {user_id : {business_id : [review]}}
	return word_count -- sparse array(word vector), ratings -- np array of label
	"""
	user_all_reviews = []
	# count vector num in user_count
	user_count = dict()
	X_total = dict()
	y_total = dict()
	restaurant_feature = dict()
	ratings = []
	for user in user_indexed_reviews:
		user_count[user] = 0
		restaurant_reviews = user_indexed_reviews[user]
		for restaurant in restaurant_reviews:
			# extract feature
			reviews_content = ''
			reviews = restaurant_reviews[restaurant]
			for review in reviews:
				reviews_content += review['text'][0:len(review['text'])-1]
			if reviews_content == '':
				continue
			user_all_reviews.append(reviews_content)
			# compute label
			rating = round(utils.cal_average_rating(reviews)*2)
			ratings.append(rating)
			# count words
			user_count[user] += 1
	user_all_reviews += all_reviews
	vectorizer = TfidfVectorizer(min_df=1)
	word_count = vectorizer.fit_transform(user_all_reviews)

	sum_count = 0
	for user in user_indexed_reviews:
		if user_count[user] == 0:
			X_total[user] = None
			y_total[user] = None
		else:
			X_total[user] = word_count[sum_count:sum_count+user_count[user]+1, :]
			y_total[user] = np.array(ratings[sum_count:sum_count+user_count[user]+1])
		sum_count += user_count[user]

	i = sum_count
	for restaurant in restaurant_indexed_reviews:
		restaurant_feature[restaurant] = word_count[i, :]
		i = i + 1
	print i, sum_count
	return X_total,y_total,restaurant_feature


def construct_classifier_for_user(user_indexed_reviews, restaurant_indexed_reviews):
	"""
	construct classifier for each user
    user_indexed_reviews is a new review dictionary {user_id : {business_id : [review]}} that can be indexed by restaurant_id
	restaurant_indexed_reviews is a new review dictionary {business_id : {user_id : [review]}} that can be indexed by restaurant_id
	return user_classifier -- {user: classifier for each user}
	"""	
	# compute all_reviews
	all_reviews = []
	for restaurant in restaurant_indexed_reviews:
		reviews_content = ''
		for user in restaurant_indexed_reviews[restaurant]:
			reviews = restaurant_indexed_reviews[restaurant][user]
			for review in reviews:
				reviews_content += review['text'][0:len(review['text'])-1]
		all_reviews.append(reviews_content)

	print 'extract feature...'
	# construct classifier
	X_total, y_total, restaurant_feature = extracttfidf_user(user_indexed_reviews, all_reviews, restaurant_indexed_reviews)

	print 'construct classifier...'
	i = 0
	for user in user_indexed_reviews:
		print i
		i += 1
		classifier = MultinomialNB(alpha=.01)
		X_train = X_total[user]
		y_train = y_total[user]
		if X_train != None:
			try:
				classifier.fit(X_train, y_train)
				update_rating(user, restaurant_feature, classifier, user_indexed_reviews, restaurant_indexed_reviews)
			except:
				continue

def update_rating(user, restaurant_feature, classifier, user_indexed_reviews, restaurant_indexed_reviews):
	"""
	update rating table
	classifiers -- {user: classifier for each user}
	restaurant_features -- sparse array(word vector)
	user_rating_table -- {user_id: {restaurant_id : rating}
    restaurant_indexed_reviews is a new review dictionary {business_id : {user_id : [review]}} that can be indexed by restaurant_id
	return 
	new_user_rating_table -- {user_id: {restaurant_id : rating}

	"""
	for restaurant in restaurant_indexed_reviews:
		if restaurant in user_indexed_reviews[user]:
			continue
		# predict score
		score = classifier.predict(restaurant_feature[restaurant].toarray())[0] / 2.0
		user_indexed_reviews[user][restaurant] = [dict()]
		user_indexed_reviews[user][restaurant][0]['stars'] = score
		restaurant_indexed_reviews[restaurant][user] = [dict()]
		restaurant_indexed_reviews[restaurant][user][0]['stars'] = score

