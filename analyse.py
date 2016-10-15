#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python 2.7.12

# 
# A command line utility to analyse twitter sentiment for any given topic and
# writes output to a CSV file.
# - Saurabh Mathur


import os
import dotenv
import argparse
import tweepy
import textblob
import codecs
import csv
import re

#
# Configure 

# define command-line arguments
parser = argparse.ArgumentParser(description = "Analyse tweet sentiment for a query")
parser.add_argument("query", type = str,
                   help="search term for which sentiment is to be computed")

parser.add_argument("outfile", type = str,
                   help="filepath for output csv file")

parser.add_argument("--limit", type = int,
                   help="maximum number of tweets to be analysed (default = 50)", default = 50, required = False)

parser.add_argument("--threshold", type = float,
                   help="polarity threshold for a tweet to be labelled positiver (default = 0)", default = 0, required = False)

args = parser.parse_args()

# load environment variables 
dotenv_path = os.path.join(os.getcwd(), ".env")
dotenv.load_dotenv(dotenv_path)


#
# Authenticate

# create OAuth Handler
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
oauth_handler = tweepy.OAuthHandler(consumer_key, consumer_secret)

# set access token
access_token = os.environ.get("ACCESS_TOKEN")
access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")
oauth_handler.set_access_token(access_token, access_token_secret)

# authenticate
twitter = tweepy.API(oauth_handler)

# pull tweets containing search term
tweets = twitter.search(q = args.query, count = args.limit, lang = "en")


#
# Analyse tweets

def preprocess(tweet):
    text = tweet.lower()
    # URLs
    text = re.sub("((www\.[^\s]+)|(https?://[^\s]+))", "URL", text)
    # @user mentions
    text = re.sub("@[^\s]+","AT_USER", text)
    # whitespaces
    text = re.sub("[\s]+", " ", text)
    # hashtags
    text = re.sub("#([^\s]+)", "\1", text)
    return text.strip()


try:
    with open(args.outfile, "wb") as outfile:
        fieldnames = [u"name", u"screen_name", u"text", u"polarity", u"subjectivity", u"label"]
        writer = csv.DictWriter(outfile, fieldnames = fieldnames, quoting = csv.QUOTE_ALL)
        writer.writeheader()
        for tweet in tweets:
            analysis = textblob.TextBlob(preprocess(tweet.text))
            row = {}
            row[u"name"] = unicode(tweet.user.name).encode("utf8")
            row[u"screen_name"] = unicode(tweet.user.screen_name).encode("utf8")
            row[u"text"] = unicode(tweet.text).encode("utf8")
            row[u"polarity"] = "{0:.2f}".format(round(analysis.sentiment.polarity, 2))
            row[u"subjectivity"] = "{0:.2f}".format(round(analysis.sentiment.subjectivity, 2))
            row[u"label"] = "POSITIVE" if analysis.sentiment.polarity > args.threshold else "NEGATIVE"
            writer.writerow(row)
except IOError:
    print "Unable to open file : {0} for writing.".format(args.outfile)