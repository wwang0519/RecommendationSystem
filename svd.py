import utils
import random, math

class SVD():
	def __init__(self, users_num, restaurant_num, user_rating_table, factorNum = 20, learningrate = 0.001, regularization = 0.05):		
		"""
		initialize p,q,b
		initialize parameters
		"""
		self.users_num = users_num
		self.restaurant_num = restaurant_num
		# average	    
		count = 0
		sum_ratings = 0.0
		for user, restaurant_ratings in user_rating_table.items():
			for restaurant, rating in restaurant_ratings.items():
				sum_ratings += rating
				count += 1
		self.average = sum_ratings / count
		self.bu = [0.0 for i in range(users_num)]
		self.br = [0.0 for i in range(restaurant_num)]
		self.factorNum = factorNum
		self.learningrate = learningrate
		self.regularization = regularization
		self.p = [[3.1*random.random()/math.sqrt(self.factorNum) for i in range(self.factorNum)] \
				  for j in range(self.users_num)]  
		self.q = [[3.1*random.random()/math.sqrt(self.factorNum) for i in range(self.factorNum)] \
				  for j in range(self.restaurant_num)]  

	def svd_training(self, user_rating_table, test_user_data, iterNum = 30):
		"""
		training p,q,b
		user_rating_table --{user : {restaurant : rating}}
		"""
	  	# iteration
  		for user_index, (user, restaurant_ratings) in enumerate(user_rating_table.items()):
  			for restaurant_index, (restaurant, rating) in enumerate(restaurant_ratings.items()):
  				if user_index % 1000 == 0:
	  				evaluations = self.svd_test(test_user_data)
					SVD_rmse = utils.cal_rmse(evaluations)
					print SVD_rmse
  				current_score = self.predictScore(self.average, self.bu[user_index], self.br[restaurant_index], \
									  self.p[user_index], self.q[restaurant_index])
  				error = rating - current_score

    			# update 
				for k in range(self.factorNum):
					p_uk = self.p[user_index][k]
					self.p[user_index][k] += self.learningrate * (error*self.q[restaurant_index][k] \
											- self.regularization * self.p[user_index][k])
					self.q[restaurant_index][k] += self.learningrate * (error*p_uk \
											      - self.regularization * self.q[restaurant_index][k])
				self.bu[user_index] += self.learningrate*(error - self.regularization * self.bu[user_index])
				self.br[restaurant_index] += self.learningrate*(error - self.regularization * self.br[restaurant_index])

	def svd_test(self, test_user_data):
		"""
		test svd model for test user data
		test_user_data -- {user : {restaurant : [reviews]}}
		return evaluations -- {user : {restaurant : (true_rating, prediction)}}
		"""
		evaluations = dict()
		for user_index, user in enumerate(test_user_data.keys()):
			evaluations[user] = dict()
			for restaurant_index, (restaurant, reviews) in enumerate(test_user_data[user].items()):
				true_rating = utils.cal_average_rating(reviews)
				prediction = self.predictScore(self.average, self.bu[user_index], self.br[restaurant_index], \
	    				self.p[user_index], self.q[restaurant_index])
				evaluations[user][restaurant] = (true_rating, prediction)
		return evaluations

	def predictScore(self, average, bu, br, pu, qr):
		"""
		predict score for given pu and qr
		return score
		"""
		score = average + bu + br + utils.innerProduct(pu, qr)
		if score < 0.5:
			score = 0.5
		elif score > 5:
			score = 5
		return score
