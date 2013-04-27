import hashlib
import sqlite3

class SqliteDB(object):
	def __init__(self, database):
		self.database = database
		self.conn = sqlite3.connect(database)
		self.cursor = self.conn.cursor()

	def create_schema(self):
		c = self.cursor
		q1 = """CREATE TABLE users
			 (
			 uid int,
			 user_name varchar(20),
			 password varchar(30)
			 )"""

		c.execute(q1)
		self.conn.commit()

	def get_user(self, username):
		c = self.cursor
		q = 'SELECT uid FROM users WHERE user_name=?'
		c.execute(q, (username,))
		row = c.fetchone()
		if row:
			return True
		else:
			return False

	def add_account(self, username, password):
		c = self.cursor
		if self.get_user(username) == False:
			password_hash = self._get_hash(password)
			c.execute('INSERT INTO users (user_name, password) VALUES (?, ?)',
				(username, password_hash,))
			self.conn.commit()

	def _get_hash(self, password):
		c = self.cursor
		h = hashlib.sha1()
		h.update(password)
		return h.hexdigest()

	def _match_password(self, username, check_password):
		c = self.cursor
		q = 'SELECT password FROM users WHERE user_name=?'
		c.execute(q, (username,))
		row = c.fetchone()
		if row:
			db_password = row[0]
			if db_password == self._get_hash(check_password):
				return True
			else:
				return False
		else:
			raise Exception('User does not exist.')

	def authenticate(self, username, password):
		print (username, password)
		try:
			match_result = self._match_password(username, password)
			return match_result
		except:
			return False

	def delete_account(self, username):
		c = self.cursor
		q = 'DELETE FROM users WHERE user_name=?'
		c.execute(q, (username,))