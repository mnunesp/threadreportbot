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

USERNAME = "ThreadReportBot"
PASSWORD = ""

MAX_POSTS = 100 # Max # of posts to consider in data gathering
MAX_SUBREDDITS = 25 #
MAX_DATE = 55 # How many days ago submissions are counted

WAIT_TIME = 15

#logging.basicConfig(level=logging.DEBUG)

# Collect username strings from submission comments into a set and return set
def get_usernames(submission):
    usernames = set()
    
    
    submission.comments.replace_more(limit=0)
    comment_queue = submission.comments[:]
    
    # Gather comments
    while comment_queue:
        comment = comment_queue.pop()
        author = comment.author
        
        # Don't count the bot the bot's submission and pass deleted comments
        if author == None or author.name == USERNAME:
            # Get more comments
            comment_queue.extend(comment.replies)
            continue
        # Add name to list if not already added
        if author.name not in usernames: 
            usernames.add(author.name)
            
        #Get more comments
        comment_queue.extend(comment.replies)
    
    return usernames

# Collect data of users' visted subreddits
# Currently only handles comments
def get_data(usernames):
    
    data_start = time.clock()
    data = {}
    
    print 'Begin data gather'
    
    while len(usernames) != 0:
        current_username = usernames.pop()
        visited_subreddits = set()
        
        # Check each submission made by user
        for submission in reddit.redditor(current_username).comments.new(limit = MAX_POSTS):
            subreddit_display_name = submission.subreddit.display_name
            
            # Difference of current date/time and submission date/time
            date = datetime.datetime.now() - datetime.datetime.fromtimestamp(submission.created)
            
            print date.days, "Days ago"
            # Stop checking if submissions are older than MAX_DATE
            if date.days > MAX_DATE:
                print date.days, "breaking"
                break
            
            if subreddit_display_name not in visited_subreddits:
                visited_subreddits.add(subreddit_display_name)
                data[subreddit_display_name] = data.get(subreddit_display_name, 0) + 1    
        
    print "Total data gather time: %f" %(time.clock() - data_start)

    return data

# Begin gathering then posting process
def begin(submission):
    #Start time
    #start = time.clock()
    
    #try:
    usernames = get_usernames(submission)
    unique_users = len(usernames)
    data = get_data(usernames);
        #total_time = (time.clock() - start)
    #except Exception as e:
    #    print "Fail:", e        
    
    # Organize and print data
    sorted_data = sorted(data.items(), key=operator.itemgetter(1), reverse = True)
    
    POST = "Displaying top %d subreddits commented in, in the last %d days for redditors in this post\n\nSubreddit | Count\n---|---\n" %(MAX_SUBREDDITS,MAX_DATE)
    
    count = 0
    for i in sorted_data:
        if count >= MAX_SUBREDDITS:
            break
        #ingnore subreddits with only 1 post
        #if i[1] == 1:
            #continue
        POST = POST + "%s | %s\n" %(i[0], i[1])
    
    try:
        message.reply(POST)
    except Exception as e:
        print "Fail:", e
    print "unique users: %d" %(unique_users)
    #print total_time                

# Check message for command
# TODO: Improve checking so only specific message is accepted rather than
# looking for phrase in entire message
def process_message(message):
    body = message.body
    body = body.lower()
    if body.find("give a report") != -1:
        print "Found phrase"
        return True
    return False

if __name__ == "__main__":
    

        # Authentication via OAuth
        reddit = praw.Reddit(username = USERNAME,
                             password = PASSWORD,
                             client_id = "",
                             client_secret = "",
                             user_agent = "") 
        
        submission = None
        
        while True:
            
            print "Searching inbox"
            # Respond to username mentions in inbox
            for message in reddit.inbox.unread(limit = 1):
                reddit.inbox.mark_read([message])            
                if isinstance(message, Comment):
                    print "Found comment"
                    submission = message.submission
                    if process_message(message):
                        begin(submission)
            
            print "Waiting for %d seconds" %(WAIT_TIME)
            time.sleep(WAIT_TIME)