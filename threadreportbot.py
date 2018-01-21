"""
ThreadReportBot. Collects data of users' visited subreddits in a given
reddit thread to examine subreddit crossover.
Developed by /u/pirateprunes
"""

import praw
import operator
import time
import datetime
import logging

from praw.models import Comment
from prawcore.exceptions import Forbidden, NotFound

USERNAME = "ThreadReportBot"
PASSWORD = ""

MAX_POSTS = 100  # Max number of posts to consider in data gathering testing
MAX_SUBREDDITS = 15  # Max number of subreddits to display
MAX_DATE = 30  # How many days ago submissions are counted

WAIT_TIME = 15


# logging.basicConfig(level=logging.DEBUG)

# Collect username strings from submission comments into a set and return set
def get_usernames(submission):
    usernames = set()

    submission.comments.replace_more(limit=0)
    comment_queue = submission.comments[:]

    # Gather comments
    while comment_queue:
        comment = comment_queue.pop()
        author = comment.author

        # Pass deleted comments and don't count the bot's comments
        if author is None or author.name == USERNAME:
            # Get more comments
            comment_queue.extend(comment.replies)
            continue
        # Add name to list if not already added
        if author.name not in usernames:
            usernames.add(author.name)

        # Get more comments
        comment_queue.extend(comment.replies)

    return usernames


# Collect data of users' visited subreddits
# Currently only handles comments
def get_data(usernames, commands):
    data_start = time.clock()
    data = {}

    print('Begin data gather')

    while len(usernames) != 0:
        current_username = usernames.pop()
        visited_subreddits = set()


        try:
            # Check each submission made by user
            for submission in reddit.redditor(current_username).comments.new():
                subreddit_display_name = submission.subreddit.display_name


                # Difference of current date/time and submission date/time
                date = datetime.datetime.now() - datetime.datetime.fromtimestamp(submission.created)

                # Stop checking if submissions are older than MAX_DATE
                if date.days > MAX_DATE:
                    break

                # If subreddit is not listed to be blocked and not already visited
                if subreddit_display_name.lower() not in commands[0] and subreddit_display_name not in visited_subreddits:
                    visited_subreddits.add(subreddit_display_name)
                    data[subreddit_display_name] = data.get(subreddit_display_name, 0) + 1
        except NotFound:
            print("User %s not found" % (current_username))
        except Forbidden:
            print("User %s suspended" % (current_username))

    print("Total data gather time: %f" % (time.clock() - data_start))

    return data


# Determines subreddits to be blocked
def parse_blocked(paragraph):
    paragraph = paragraph.lstrip('block:')

    sub_list = paragraph.split(',')

    # Prune empty entries
    while ('' in sub_list):
        sub_list.remove('')

    for i in range(0, len(sub_list)):
        new_string = sub_list[i]
        new_string = new_string.lstrip().rstrip()
        sub_list[i] = new_string

    return sub_list

# Parses and handles any additional commands
# Can be extended by adding additional slots to command_list
def parse_message(message_string):
    command_list = [[]]

    paragraphs = message_string.split('\n\n')

    # Prune "empty" paragraphs
    while ('' in paragraphs):
        paragraphs.remove('')

        # Check if more commands might be available
    if (len(paragraphs) > 1):

        # Check for block command
        if (paragraphs[1].find('block:') == 0):
            command_list[0] = parse_blocked(paragraphs[1])

    return command_list


# Begin gathering then posting process
def begin(submission, body):
    # Start time
    # start = time.clock()

    usernames = get_usernames(submission)
    unique_users = len(usernames)
    commands = parse_message(body)




    data = get_data(usernames, commands)

    # Organize and print data
    sorted_data = sorted(data.items(), key=operator.itemgetter(1), reverse=True)

    POST = "Displaying top %d subreddits that redditors in this post commented in," \
           " in the last %d days\n\n" % (MAX_SUBREDDITS, MAX_DATE)

    if len(commands[0]) > 0:
        new_string = "Blocked subreddits = ("
        for i in commands[0]:
            new_string = new_string + i + ', '

        new_string = new_string.rstrip(', ') + ')\n\n'

        POST = POST + new_string

    POST = POST + "Subreddit | Count\n---|---\n"

    count = 0
    for i in sorted_data:
        if count >= MAX_SUBREDDITS:
            break
            # ingnore subreddits with only 1 post
            # if i[1] == 1:
            # continue
        POST = POST + "%s | %s\n" % (i[0], i[1])
        count += 1

    POST = POST + "\nI'm a bot. Contact /u/pirateprunes with any issues."

    # Try to post message
    try:
        message.reply(POST)
        print("Successfully posted! \nUnique users: %d\n" % (unique_users))
    except Exception as e:
        print ("Post Fail:", e)





# print total_time

# Check message for command
# looking for phrase in entire message
def valid_message(message):
    body = message.body
    body = body.lower()

    if body.find("/u/threadreportbot give a report") == 0 or body.find("u/threadreportbot give a report") == 0:
        print("Found phrase")
        return True

    return False


if __name__ == "__main__":

    # Authentication via OAuth
    reddit = praw.Reddit(username=USERNAME,
                         password=PASSWORD,
                         client_id="",
                         client_secret="",
                         user_agent="")

    submission = None

    while True:

        print("Searching inbox")
        # Respond to username mentions in inbox
        for message in reddit.inbox.unread(limit=1):
            reddit.inbox.mark_read([message])
            if isinstance(message, Comment):
                print("Found comment")
            submission = message.submission
            if valid_message(message):
                begin(submission, message.body.lower())

        print("Waiting for %d seconds" % (WAIT_TIME))
        time.sleep(WAIT_TIME)