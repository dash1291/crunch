Crunch
======

Experimental tools to allow serving content from behind firewall'd networks to the internet.

How it works?
-------------

A middleware server which receives HTTP requests from the internet, routes these requests to the serving nodes according to the requested URI. A serving node serve its content to the server over a persistent connection, which is started by the node itself. Hence, the need to accept connections behind the firewall is eliminated.

The node is a client which binds to the server's protocol, receives the content requests and writes the content back to the server. The content on reaching the server is served as the resposne to the original HTTP request.

Structure
---------

The server and client both are implemented using awesome tools like Tornado. The server runs an HTTP receiver on one thread and the crunch receiver on the other thread, both of which are non-blocking.

Usage
-----

Running the server
##################

::

	from crunch.server import runserver

	# This is the port for accepting incoming HTTP requests. Your choice
	http_port = 80

	# This is the port for accepting incoming connections from crunch clients.
	# Again your choice
	crunch_port = 8080
	
	runserver(http_port, crunch_port)

Running the client
##################

::

	from crunch.crunchclient import start_client

	config = {
		'port': 8080,	# this the crunch port your server runs on
		'address': 'localhost'	# this is the address of the server
	}

	start_client(config)
