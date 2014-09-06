from bottle import error, get, post, run, request
import database


@error(404)
def error404(error):
    return "404"


def log(msg):
    """Prints a message alongside the IP of the client that generated it."""
    print('[' + request.remote_addr + '] ' + msg)



print("Creating tables if need be...")
database.createTables()
print("API starting...")
run(host='localhost', port=8082, quiet=True)