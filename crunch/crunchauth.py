import hashlib
import sqlite3

conn = sqlite3.connect('crunch.db')
c = conn.cursor()

def create_schema():
	q1 = """CREATE TABLE users
		 (
		 uid int,
		 user_name varchar(20),
		 password varchar(30)
		 )"""

	c.execute(q1)
	conn.commit()

def get_user(username):
	q = 'SELECT uid FROM users WHERE user_name=?'
	c.execute(q, (username,))
	row = c.fetchone()
	if row:
		return True
	else:
		return False

def add_account(username, password):
	if get_user(username) == False:
		password_hash = get_hash(password)
		c.execute('INSERT INTO users (user_name, password) VALUES (?, ?)', (username, password_hash,))
		conn.commit()

def get_hash(password):
	h = hashlib.sha1()
	h.update(password)
	return h.hexdigest()

def match_password(username, check_password):
	q = 'SELECT password FROM users WHERE user_name=?'
	c.execute(q, (username,))
	row = c.fetchone()
	if row:
		db_password = row[0]
		if db_password == get_hash(check_password):
			return True
		else:
			return False
	else:
		raise Exception('User does not exist.')

def authenticate(username, password):
	try:
		match_result = match_password(username, password)
		if match_password(username, password) == True:
			return True
		else:
			return False
	except:
		return False