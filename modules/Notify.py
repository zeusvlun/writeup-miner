from discord_webhook import DiscordWebhook, DiscordEmbed
from .Logger import logger
import requests, re, time

def create_message(feed, filtered_words):
    try:
        title = re.sub(r'(?i)(?<!\\)(?:\\\\)*\\u([0-9a-f]{4})', lambda m: chr(int(m.group(1), 16)), feed["title"])
        isfiltered = check_filter(title,filtered_words)
        if isfiltered:
            return "filtered"
        tags = ""
        if feed["tags"] != []:
            for tag in feed["tags"]:
                if "-" in tag:
                    tag = tag.replace("-","_")
                tags = tags+"#"+tag+" "
        else:
            tags = "No_Tags"
        message = '◾️ <b>Title:  </b><a href="{}"><b>{}</b></a>\n════════════════════════\n◾️ <b>Date:  </b>{}\n════════════════════════\n◾️ <b>Tags:  </b>{}'.format(feed["url"],title,feed["published"],tags)
        return message
    
    except Exception as e:
        logger("{}".format(e), "ERR")

def create_message_discord(feed, filtered_words):
    try:
        title = re.sub(r'(?i)(?<!\\)(?:\\\\)*\\u([0-9a-f]{4})', lambda m: chr(int(m.group(1), 16)), feed["title"])
        isfiltered = check_filter(filtered_words, title)
        if isfiltered:
            return "filtered"
        tags = ""
        if feed["tags"] != []:
            for tag in feed["tags"]:
                if "-" in tag:
                    tag = tag.replace("-","_")
                tags = tags+"#"+tag+" "
        else:
            tags = "No_Tags"
        return {"title":title , "date":feed["published"], "url":feed["url"], "tags": tags }
    
    except Exception as e:
        logger("{}".format(e), "ERR")


def check_filter(filtered_words,title):

    for word in filtered_words:
        if word in title:
            logger("The feed wasn't pushed because a filtered word was found in the title! {}".format(word),"INF")
            return True
        
        return False
        
def notify(message, filtered_words, webhook=None, token=None, chatid=None):
    try:
        if webhook:
            logger("Sending New feeds to Discord", "INF")
            discordmessage = create_message_discord(message, filtered_words)
            if message == "filtered":
                return
            webhook_url = DiscordWebhook(url=webhook)
            embed = DiscordEmbed(title='◾️ New Writeup', color=0xFF5733)
            embed.add_embed_field(name='◾️ Date', value=discordmessage["date"], inline=False)
            embed.add_embed_field(name='◾️ Title', value=discordmessage["title"], inline=False)
            embed.add_embed_field(name='◾️ Link', value=discordmessage["url"], inline=False)
            embed.add_embed_field(name='◾️ Tags', value=discordmessage["tags"], inline=False)
            webhook_url.add_embed(embed)
            response = webhook_url.execute()
            if response.status_code != 200:
                logger("Discord Error : "+req.text, "ERR")
                exit(1)
        else:
            logger("Sending New feeds to Telegram", "INF")
            text = create_message(message, filtered_words)
            if text == "filtered":
                return
            
            payload = {
            "chat_id": chatid,
            "text": text,
            "parse_mode": "HTML",
            "is_disabled": False,
            "link_preview_options": {
            "url": message["url"],
            "prefer_small_media": True,
            "prefer_large_media": False,
            "show_above_text": False
            }
        }
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            req = requests.post(url, json=payload)
            time.sleep(2)

            if req.status_code != 200:
                time.sleep(30)
                logger("Telegram Error : "+req.text, "ERR")

    except Exception as e:
        logger("{}".format(e), "ERR")
        exit(1)
        
    logger("New feed sent successfully", "OK")
