import sqlite3
import queries

def connect():
    """Opens a connection to the database and returns the connection object."""
    return sqlite3.connect("telegraph.sqlite")

def close(con):
    """Closes any open connection to the database."""
    # I guess every connection with the DB-API 2.0 bindings is treated like a transaction, so commit it.
    con.commit()
    con.close()

def createTables():
    """Creates the default tables in the database."""
    con = connect()
    c = con.cursor()
    c.execute(queries.CREATE_TABLE_USERS)
    c.execute(queries.CREATE_TABLE_IMAGES)
    c.execute(queries.CREATE_TABLE_IMAGE_HISTORY)
    c.execute(queries.CREATE_TABLE_ACTIVE_ACCESS_TOKENS)
    close(con)
    
def dropTables():
    """Drops all the known tables in the database, useful for debugging."""
    con = connect()
    c = con.cursor()
    c.execute(queries.DROP_TABLE_USERS)
    c.execute(queries.DROP_TABLE_IMAGES)
    c.execute(queries.DROP_TABLE_IMAGE_HISTORY)
    c.execute(queries.DROP_TABLE_ACTIVE_ACCESS_TOKENS)
    close(con)


