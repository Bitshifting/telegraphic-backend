from bottle import error, get, post, run, request
import database


@error(404)
def error404(error):
    return "404"


def log(msg):
    """Prints a message alongside the IP of the client that generated it."""
    print('[' + request.remote_addr + '] ' + msg)


def fail(msg):
    """Returns a failure JSON to the user."""
    return {'success': False, 'message': msg}


def success(msg):
    """Returns a success JSON to the user."""
    return {'success': True, 'message': msg}


# ######################################################################################################################
# User Accounts
# ######################################################################################################################

# Register user

@post('/user/register')
def registerUser():
    if not 'username' in request.json.keys():
        return fail('Username not provided in registration.')
    if not 'passwordHash' in request.json.keys():
        return fail('Password hash not provided in registration.')

    log("Registering new user account: " + request.json['username'] + " " + request.json['passwordHash'])

    # Check that this user doesn't already exist.
    con = database.connect()
    c = con.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE username=:username", {'username': request.json['username']})

    r = c.fetchone()
    if r[0] != 0:
        log("That username already exists.")
        return fail('Username already exists.')

    # Ok. Insert them into the database.
    c.execute("INSERT INTO users (username, passwordHash) VALUES (:username, :passwordHash)",
              {'username': request.json['username'], 'passwordHash': request.json['passwordHash']})

    database.close(con)

    log("User registered.")
    return success('User registered.')

# ######################################################################################################################
# Image Handling
# ######################################################################################################################



print("Creating tables if need be...")
database.createTables()
print("API starting...")
run(host='localhost', port=8082, quiet=True)