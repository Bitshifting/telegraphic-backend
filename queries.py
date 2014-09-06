# ######################################################################################################################
# Tables
# ######################################################################################################################

CREATE_TABLE_USERS = """
    CREATE TABLE IF NOT EXISTS users (
         userID INTEGER PRIMARY KEY AUTOINCREMENT,
         username TEXT NOT NULL,
         passwordHash TEXT NOT NULL,
        createdOn INTEGER DEFAULT CURRENT_TIMESTAMP NOT NULL,
         phoneNumber TEXT NOT NULL
     )
"""

CREATE_TABLE_ACTIVE_ACCESS_TOKENS = """
    CREATE TABLE IF NOT EXISTS activeAccessTokens (
        tokenID INTEGER PRIMARY KEY AUTOINCREMENT,
        accessToken TEXT NOT NULL,
        username REFERENCES users (username),
        createdOn INTEGER DEFAULT CURRENT_TIMESTAMP NOT NULL
    )
"""

CREATE_TABLE_IMAGES = """
    CREATE TABLE IF NOT EXISTS images (
        imageID INTEGER PRIMARY KEY AUTOINCREMENT,
        imageUUID TEXT NOT NULL,
        originalOwner REFERENCES users (username),
        createdOn INTEGER DEFAULT CURRENT_TIMESTAMP NOT NULL,
        hopsLeft INTEGER NOT NULL,
        editTime INTEGER NOT NULL,
        image BLOB NOT NULL,
        nextUser REFERENCES users (username),
        previousUser REFERENCES users (username)
    )
"""

# Use to keep a one-to-many relationship between images and their previous owners to determine who to show the completed
# image to once it runs out of hops.
CREATE_TABLE_IMAGE_HISTORY = """
    CREATE TABLE IF NOT EXISTS imageHistory (
        historyID INTEGER PRIMARY KEY AUTOINCREMENT,
        imageUUID REFERENCES images (imageUUID),
        username REFERENCES users (username)
    )
"""

CREATE_TABLE_FRIENDS_LIST = """
    CREATE TABLE IF NOT EXISTS friends (
        friendEntryID INTEGER PRIMARY KEY AUTOINCREMENT,
        username REFERENCES users (username),
        friend REFERENCES users (username)
    )
"""

DROP_TABLE_USERS = """
    DROP TABLE IF EXISTS users
"""

DROP_TABLE_ACTIVE_ACCESS_TOKENS = """
    DROP TABLE IF EXISTS activeAccessTokens
"""

DROP_TABLE_IMAGES = """
    DROP TABLE IF EXISTS images
"""

DROP_TABLE_IMAGE_HISTORY = """
    DROP TABLE IF EXISTS imageHistory
"""

DROP_TABLE_FRIENDS_LIST = """
    DROP TABLE IF EXISTS friends
"""