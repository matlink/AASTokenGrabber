import tornado.ioloop
import tornado.web
import random
import time
import sys

from gpapi.googleplay import GooglePlayAPI
from gpapi import config
import requests

import constants
import utils

class MainHandler(tornado.web.RequestHandler):
	def get_auth_token(self, email, aasToken):
		params = {
			"service": "oauth2:https://www.googleapis.com/auth/googleplay",
			"app": "com.android.vending",
			"oauth2_foreground": "1",
			"token_request_options": "CAA4AVAB",
			"check_email": "1",
			"Token": aasToken,
			"client_sig": "38918a453d07199354f8b19af05ec6562ced5788",
			"callerPkg": "com.google.android.gms",
			"system_partition": "1",
			"_opt_is_called_from_account_manager": "1",
			"is_called_from_account_manager": "1",
		}
		raw_response = requests.post(constants.AUTH_URL, data=params)
		if raw_response.status_code == 200:
			for param in raw_response.text.split():
				if param.startswith("Auth="):
					return param[5:]
		return None

	def get_aac_token(self, email, password):
		token_param = 'Token'
		enc_password = utils.encrypt_password(email, password)
		params = {'Email': email,
					'EncryptedPasswd': enc_password,
					'add_account': '1',
					'accountType': 'HOSTED_OR_GOOGLE',
					'google_play_services_version': '11951438',
					'has_permission': '1', 'source': 'android',
					'device_country': 'de',
					'lang': 'de',
					'client_sig': '38918a453d07199354f8b19af05ec6562ced5788',
					'callerSig': '38918a453d07199354f8b19af05ec6562ced5788', 'service': 'sj',
					'callerPkg': 'com.google.android.gms'}

		raw_response = requests.post(constants.AUTH_URL, data=params)

		if raw_response.status_code >=400:
			print(raw_response.text.split())
			return None

		if raw_response.status_code == 200:
			response = raw_response.text.split()
			for param in response:
				if param.startswith(token_param):
					return param[6:]
		else:
			return None

	def initialize(self, credentials_list):
		self.credentials_list = credentials_list

	def get(self, email = None):
		if email is None:
			email, pwd = random.choice(self.credentials_list)
			self.write(email)
			return
		for address, pwd in self.credentials_list:
			if address == email:
				break
		token = self.get_aac_token(email, pwd)
		token = self.get_auth_token(email, token)
		self.write("%s" % (token))

def make_app(credential_file):
	with open(credential_file) as inbuff:
		credentials_list = [tuple(line.split()) for line in inbuff if not line.startswith('#')]
	print("Loaded credentials: ", [line[0] for line in credentials_list])
	params = dict(credentials_list=credentials_list)
	return tornado.web.Application([
		(r"/email", MainHandler, params),
		(r"/token/email/(.*)", MainHandler, params),
	])

if __name__ == "__main__":
	app = make_app(sys.argv[1])
	app.listen(8080)
	tornado.ioloop.IOLoop.current().start()