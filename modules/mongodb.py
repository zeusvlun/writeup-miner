import pymongo, hashlib
from .Logger import logger
from .Notify import notify

def existdb(myclient):
    try:
        logger("Checking for Database existence.", "INF")
        dbnames = myclient.list_database_names()
        if "writeupminer" in dbnames:
            logger("Database Found.", "OK")
            return True
        logger("Database Not Found.", "ERR")
    except Exception as e:
        logger("{}".format(e), "ERR")
        exit(1)

def updateDatabase(mydb, new_feeds, exist):
    try:
        logger("Updating Database.", "INF")
        mycol = mydb["writeups"]
        if exist:
            logger("Removing previous collection.", "INF")
            mycol.drop()
        else:
            logger("Creating new collection.", "INF")
        for feed in new_feeds:
            hashed = str(hashlib.md5(( feed["title"] + feed["published"]).encode()).hexdigest())
            mycol.insert_one({"writeup": hashed})
        logger("Database Updated.", "OK")
    except Exception as e:
        logger("{}".format(e), "ERR")
        exit(1)

def push_to_database(mydb, new_feed):
    try:
        logger("Pushing new posts to database.", "INF")
        mycol = mydb["writeups"]
        hashed = str(hashlib.md5(( new_feed["title"] + new_feed["published"]).encode()).hexdigest())
        mycol.insert_one({"writeup": hashed})
        logger("Pushed new posts to database.", "OK")
    except Exception as e:
        logger("{}".format(e), "error")
        exit(1)


def check_database(mydb, new_feeds, webhook, token, chatid, filtered_words):
    try:
        logger("Checking for new posts.", "INF")
        mycol = mydb["writeups"]
        old_feeds = mycol.find({})
        writeups = []
        for old_feed in old_feeds:
            writeups.append(old_feed['writeup'])

        for new_feed in new_feeds:
            if new_feed["writeup"] not in writeups:
                logger("New Feed Found : "+new_feed["title"], "OK")
                push_to_database(mydb, new_feed)
                notify(new_feed, filtered_words, webhook, token, chatid)
    except Exception as e:
        logger("{}".format(e), "ERR")
        exit(1)
