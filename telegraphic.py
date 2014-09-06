from bottle import error, get, post, run, request
import database
import uuid


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


# #
# Helper functions
# #
def jsonRow(cursor):
    """Takes the next row from the cursor and formats it as a dictionary (JSON object as far as Bottle is concerned)."""
    fields = [f[0] for f in cursor.description]

    r = cursor.fetchone()
    if r is not None:
        i = 0
        newDict = {}
        for f in fields:
            newDict[f] = r[i]
            i += 1
        return newDict
    else:
        return None


def jsonRows(cursor):
    """Queries a cursor and returns its rows as a JSON response (a list of dictionaries contained in a JSON object)."""
    responseDict = {'success': 'true', 'items': []}

    if cursor is None:
        return responseDict

    jr = jsonRow(cursor)

    while jr is not None:
        responseDict['items'].append(jr)
        jr = jsonRow(cursor)

    return responseDict


# #
# Access token functions
# #

def checkAccessToken():
    """Make sure a certain access token is still valid and can be used to manipulate pictures."""

    if not 'accessToken' in request.json.keys():
        return False

    con = database.connect()
    c = con.cursor()
    c.execute("SELECT COUNT(*) FROM activeAccessTokens WHERE accessToken=:accessToken",
              {'accessToken': request.json['accessToken']})

    r = c.fetchone()

    if r[0] == 0:
        return False
    return True


def accessTokenToUser(token):
    """Look up an access token and find out who the user is."""

    con = database.connect()
    c = con.cursor()
    c.execute("SELECT username FROM activeAccessTokens WHERE accessToken=:accessToken", {'accessToken': token})

    r = c.fetchone()
    v = r[0]
    database.close(con)

    return v


# ######################################################################################################################
# User Accounts
# ######################################################################################################################

# Register user

@post('/user/register')
def userRegister():
    """Register a user."""

    if not 'username' in request.json.keys():
        log('Registration attempt but no username provided in request.')
        return fail('Username not provided in registration.')
    if not 'passwordHash' in request.json.keys():
        log('Registration attempt but no password hash provided in request.')
        return fail('Password hash not provided in registration.')
    if not 'phoneNumber' in request.json.keys():
        log('Registration attempt but no phone number provided in request.')
        return fail('Phone number not provided in registration.')

    if len(request.json['username']) == 0 or len(request.json['passwordHash']) == 0 or len(request.json['phoneNumber']) == 0:
        log('Attempted to register with a 0-length field.')
        return fail('Come on now, no 0-length fields.')
    log("Registering new user account: " + request.json['username'] + " (" + request.json['phoneNumber'] + ") " +
        request.json['passwordHash'])

    # Check that this user doesn't already exist.
    con = database.connect()
    c = con.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE username=:username OR phoneNumber=:phoneNumber",
              {'username': request.json['username'], 'phoneNumber': request.json['phoneNumber']})

    r = c.fetchone()
    if r[0] != 0:
        log("That username or phone number already exists.")
        return fail('Username or phone number already exists.')

    # Ok. Insert them into the database.
    c.execute("INSERT INTO users (username, passwordHash, phoneNumber) VALUES (:username, :passwordHash, :phoneNumber)",
              {'username': request.json['username'], 'passwordHash': request.json['passwordHash'],
               'phoneNumber': request.json['phoneNumber']})

    database.close(con)

    log("User registered.")
    return success('User registered.')


@post('/user/login')
def userLogin():
    """Log a user in and generate a unique ID for this session."""

    if not 'username' in request.json.keys():
        log('Login attempt but no username provided in request.')
        return fail('Username not provided in login.')
    if not 'passwordHash' in request.json.keys():
        log('Login attempt but no password hash provided in request.')
        return fail('Password hash not provided in login.')

    log('Attempt login ' + request.json['username'] + ' ' + request.json['passwordHash'])

    # Check if this is the correct password.
    con = database.connect()
    c = con.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE username=:username AND passwordHash=:passwordHash",
              {'username': request.json['username'], 'passwordHash': request.json['passwordHash']})

    r = c.fetchone()
    if r[0] == 0:
        log('Login failed.')
        return fail('Invalid username or password.')

    # Alright, they've logged in, now generate a random access key and give it to them.
    # XXX: These probably won't collide.
    accessToken = str(uuid.uuid1())

    c.execute("INSERT INTO activeAccessTokens (accessToken, username) VALUES (:accessToken, :username)",
              {'accessToken': accessToken, 'username': request.json['username']})
    database.close(con)

    log('Successful login.')
    return {'success': True, 'accessToken': accessToken, 'message': 'Logged in.'}


@get('/user/list')
def userList():
    """Return a list of users in the database so others can send images to them."""

    log('Returning a list of users...')
    con = database.connect()
    c = con.cursor()
    c.execute("SELECT username FROM users")

    res = jsonRows(c)
    database.close(con)

    return res

@post('/user/list')
def userListWithoutMe():
    """Return a list of users in the database so others can send images to them. Doesn't include yourself."""

    log('Returning a list of users (excluding this one)...')
    thisUser = accessTokenToUser(request.json['accessToken'])

    con = database.connect()
    c = con.cursor()
    c.execute("SELECT username FROM users WHERE username<>:username", {'username': thisUser})

    res = jsonRows(c)
    database.close(con)

    return res


# ######################################################################################################################
# Image Handling
# ######################################################################################################################

@post('/image/create')
def imageCreate():
    """Create an initial image."""
    if not checkAccessToken():
        return fail('Invalid access token.')
    if not 'editTime' in request.json.keys():
        return fail('No editTime specified.')
    if not 'hopsLeft' in request.json.keys():
        return fail('No hopsLeft specified.')
    if not 'nextUser' in request.json.keys():
        return fail('No nextUser specified.')
    if not 'image' in request.json.keys():
        return fail('No image specified.')

    log('Creating an initial image...')

    # Make sure the next user is valid...
    con = database.connect()
    c = con.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE username=:nextUser", {'nextUser': request.json['nextUser']})
    r = c.fetchone()
    if r[0] == 0:
        database.close(con)
        log('Next user was not valid.')
        return fail('Invalid nextUser.')

    # Add the image to the pending queue.
    thisUser = accessTokenToUser(request.json['accessToken'])
    thisImageUUID = str(uuid.uuid1())

    c.execute(
        "INSERT INTO images (imageUUID, originalOwner, hopsLeft, editTime, image, nextUser, previousUser) VALUES (:imageUUID, :originalOwner, :hopsLeft, :editTime, :image, :nextUser, :previousUser)",
        {'imageUUID': thisImageUUID, 'originalOwner': thisUser,
         'hopsLeft': request.json['hopsLeft'], 'editTime': request.json['editTime'], 'image': request.json['image'],
         'nextUser': request.json['nextUser'], 'previousUser': thisUser})

    # Add the initial creator into the log of people who should be notified when this image is done.
    c.execute("INSERT INTO imageHistory (imageUUID, username) VALUES (:imageUUID, :username)",
              {'imageUUID': thisImageUUID, 'username': thisUser})

    # TODO: Send push notification to the next user.

    database.close(con)
    log('Image successfully created.')
    return success('Image created and next user will be alerted.')


@post('/image/update/{UUID}')
def imageUpdate(uuid):
    """Update an existing image, and decrement its number of hops. If it reaches the end of its life, add it to the
    list of pending images that people need to see (and send push notifications)."""
    if not checkAccessToken():
        return fail('Invalid access token.')
    if not 'nextUser' in request.json.keys():
        return fail('No nextUser specified.')
    if not 'image' in request.json.keys():
        return fail('No image specified.')

    log('Updating image...')

    # Check that this image has this user specified as its next user (aka that we have permission to edit this image).
    thisUser = accessTokenToUser(request.json['accessToken'])

    con = database.connect()
    c = con.cursor()
    c.execute("SELECT COUNT(*) FROM images WHERE imageUUID=:imageUUID AND nextUser=:nextUser",
              {'imageUUID': uuid, 'nextUser': thisUser})

    r = c.fetchone()

    if r[0] == 0:
        log('Not allowed to update this image, or the image does not exist.')
        return fail('Not the next user, or this image does not exist.')

    # Decrement its hop count and update its next user. If hop count is 0, set next user to null.
    c.execute("SELECT hopCount FROM images WHERE imageUUID=:imageUUID", {'imageUUID': uuid})
    r = c.fetchone()
    newHopCount = r[0] - 1

    # Also, update the actual image...
    c.execute(
        "UPDATE images SET hopCount=:hopCount, image=:image, previousUser=:previousUser WHERE imageUUID=:imageUUID",
        {'hopCount': newHopCount, 'image': request.json['image'], 'imageUUID': uuid, 'previousUser': thisUser})

    # Add this user to the affected user list who need to see the final image...
    c.execute("INSERT INTO imageHistory (imageUUID, username) VALUES (:imageUUID, :username)",
              {'imageUUID': uuid, 'username': thisUser})


    # Check if this is the final hop and if so, alert all users.
    if newHopCount == 0:
        log('Image updated, at the end of the line. Notifying all users.')
        # TODO: Push notifications to all users...
    else:
        log('Image updated, passing to next user.')
        # TODO: Push notify nextUser

    database.close(con)
    return success('Image passed along to the next user!')


@post('/image/query')
def imageQuery():
    """Returns a list of images that a user should see. Some might be incomplete, needing additions, and others might be
     finished images."""
    if not checkAccessToken():
        return fail('Invalid access token.')

    log('Querying images that belong to this user...')
    thisUser = accessTokenToUser(request.json['accessToken'])

    # Basically, look at the images table and see if any have nextUser set to us. This will be the first set of results.
    # Also look for images in the images table whose hopCount is 0 and with us in the history table linking us to this image.
    con = database.connect()
    c = con.cursor()

    # We need the rows from this and also anything that this username has in the image history which hasn't 0 hopCount.
    c.execute("SELECT imageUUID, previousUser, editTime, hopsLeft, image FROM images WHERE nextUser=:thisUser",
              {'thisUser': thisUser})

    firstSet = jsonRows(c)['items']

    # Now, we also need any image whose UUID is mentioned with this username in the imageHistory, and whose hopCount is 0
    c.execute(
        "SELECT images.imageUUID, previousUser, editTime, hopsLeft, image FROM images JOIN imageHistory ON imageHistory.username=:username WHERE hopsLeft=0",
        {'username': thisUser})

    secondSet = jsonRows(c)['items']

    database.close(con)

    print("\tThere are " + len(firstSet) + " images that need completing by this user.")
    print("\tThere are " + len(secondSet) + " images that are done and need viewing by this user.")
    finalSet = []
    for thing in firstSet:
        finalSet.append(thing)
    for thing in secondSet:
        finalSet.append(thing)

    return {'success': True, 'items': finalSet}


@post('/image/seen/{uuid}')
def imageSeen():
    """Set an image's hop count to -1 so it won't appear in the list of images the client gets when they query."""
    if not checkAccessToken():
        return fail('Invalid access token.')

    log('Client marking image seen...')

    # Make sure a client can only mark their own images as seen, and only images that have a hopCount of 0.
    thisUser = accessTokenToUser(request.json['accessToken'])

    con = database.connect()
    c = con.cursor()

    c.execute("UPDATE images SET hopCount=-1 WHERE imageUUID=:imageUUID AND hopCount=0 AND username=:username",
              {'imageUUID': uuid, 'username': thisUser})

    database.close(con)

    log('Client acknowledgement complete.')
    return success('Successfully acknowledged image.')


print("Creating tables if need be...")
database.createTables()
print("API starting...")
run(host='kersten.io', port=8888, quiet=True)