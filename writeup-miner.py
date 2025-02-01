from modules.Logger import logger
from modules.scrape import scrape
from modules.Logger import Color
from modules import filedb
from modules import mongodb
import os, pymongo, argparse, hashlib, sys, time

HOMEPATH = os.path.expanduser('~')
WORKINGDIR = os.path.dirname(os.path.abspath(__file__))
FILEDBDIR = os.path.join(HOMEPATH, ".wiretupminer", "feeds", "feedsDB.txt")
VERSION = 2.0

def slow_print(text, delay=0.005):
    """طباعة تفاعلية للحروف بأسلوب الهاكرز"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def displayBanner():
    # بانر يظهر اسم الأداة بشكل واضح ودقيق "rednexus"
    banner = Color.GREEN + r"""
  _____           _   _   _                    
 |  __ \         | \ | | | |                   
 | |  | |  _   _ |  \| | | |__    ___  _ __    
 | |  | | | | | || . ` | | '_ \  / _ \| '__|   
 | |__| | | |_| || |\  | | | | ||  __/| |      
 |_____/   \__,_||_| \_| |_| |_| \___||_|      
                                              
             rednexus - Interactive Hacker Writeup Miner
    """ + Color.RESET
    slow_print(banner)
    slow_print(">> Booting rednexus system...", 0.03)
    slow_print(">> Initializing cyber components...\n", 0.03)

def setup_argparse():
    parser = argparse.ArgumentParser(description="rednexus - Interactive Hacker Writeup Miner")
    parser.add_argument("-H", "--host", help="MongoDB host", default="localhost")
    parser.add_argument("-p", "--port", help="MongoDB port", default="21017")
    parser.add_argument("-d", "--database", help="MongoDB Database name to store feeds on it", default="writeupminer")
    parser.add_argument("-l", "--urls", help="Path to the urls.txt file", default=f"{WORKINGDIR}/res/urls.txt")
    parser.add_argument("-m", "--dbmode", help="Database mode (file/mongo)", default="file")
    parser.add_argument("-f", "--filter", help="Path to filters.txt file to filter words from feed titles", default=f"{WORKINGDIR}/res/filters.txt")
    parser.add_argument("-u", "--update", action="store_true", help="Force update Database")
    parser.add_argument("-t", "--token", help="Telegram Bot token")
    parser.add_argument("-c", "--chatid", help="Telegram chat id")
    parser.add_argument("-w", "--webhook", help="Discord webhook URL")
    parser.add_argument("-v", "--version", help="Display version", action="store_true")

    args = parser.parse_args()

    if args.version:
        print("rednexus Version: {}".format(VERSION))
        exit(0)

    if args.update:
        return args

    if args.webhook:
        return args

    if not (args.token and args.chatid):
        parser.error("Error: Both -t/--token and -c/--chatid are required unless using -u/--update or -w/--webhook.")
    
    return args

def main():
    displayBanner()
    args = setup_argparse()
    
    logger(">> Accessing URLs file: {} ...".format(args.urls), "INF")
    urls = filedb.loadDatabase(args.urls)
    if not urls:
        logger(">> No URLs found. Aborting mission!", "ERR")
        exit(1)
    
    logger(">> Loading filters from: {} ...".format(args.filter), "INF")
    filtered_words = filedb.loadDatabase(args.filter)
    
    logger(">> Engaging web scraping protocols...", "INF")
    newFeeds = scrape(urls)
    logger(">> Feeds captured: {} items".format(len(newFeeds)), "INF")

    if args.dbmode == "file":
        logger(">> Scanning local feed database directory...", "INF")
        filedb.makeDatabaseDir(os.path.join(HOMEPATH, '.wiretupminer', 'feeds'))

        if args.update:
            logger(">> Updating FileDB with latest feed hashes...", "INF")
            updateFeeds = []
            for feed in newFeeds:
                hashed = hashlib.md5((feed["title"] + feed["published"]).encode()).hexdigest()
                updateFeeds.append(hashed.strip())
            filedb.pushDatabase(updateFeeds, FILEDBDIR)
            logger(">> FileDB update complete. Mission accomplished!", "OK")
            exit(0)

        if os.path.exists(FILEDBDIR):
            logger(">> Verifying new feeds against local DB...", "INF")
            filedb.checkDatabase(newFeeds, FILEDBDIR, args.webhook, args.token, args.chatid, filtered_words)
        else:
            firstFeeds = []
            logger(">> feedsDB not found. Creating initial DB snapshot...", "INF")
            for feed in newFeeds:
                hashed = hashlib.md5((feed["title"] + feed["published"]).encode()).hexdigest()
                firstFeeds.append(hashed.strip())
            filedb.pushDatabase(firstFeeds, FILEDBDIR)
            logger(">> Initial FileDB created successfully.", "OK")

    elif args.dbmode == "mongo":
        logger(">> Connecting to MongoDB at {}:{} ...".format(args.host, args.port), "INF")
        myclient = pymongo.MongoClient("mongodb://{}:{}/".format(args.host, args.port))
        mydb = myclient[args.database]
        is_exist = mongodb.existdb(myclient)

        if args.update:
            logger(">> Updating MongoDB with new feed data...", "INF")
            mongodb.updateDatabase(mydb, newFeeds, exist=is_exist)
            logger(">> MongoDB update complete. System secure.", "OK")
            exit(0)

        if is_exist:
            logger(">> Comparing scraped feeds with MongoDB records...", "INF")
            mongodb.check_database(mydb, newFeeds, args.webhook, args.token, args.chatid, filtered_words)
        else:
            logger(">> MongoDB collection not found. Initializing collection with current feeds...", "INF")
            mongodb.updateDatabase(mydb, newFeeds, exist=is_exist)

if __name__ == "__main__":
    main()
