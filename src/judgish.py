#!/usr/bin/env python

"""
Analyze Twitter timelines for information about the users posting to it and
to find patterns in the posts themselves.
"""

import ConfigParser
import json
import logging
import os
import sys
import tempfile
import time
from collections import Counter, defaultdict
from hashlib import md5

import twitter
from text.blob import TextBlob

CACHE_TIME = 3600
BATCH_SIZE = 200  # <= 200 per Twitter API spec
BATCH_THRESHOLD = 5  # Stop fetching when returned batches are <= this size


class Judge(object):
    """Mine a Twitter timeline's metadata"""

    def __init__(self, username, topcount=20, onlyretweets=False):
        """Set up bookkeeping"""
        self.onlyretweets = onlyretweets
        self.topcount = topcount
        self.namehash = md5(username).hexdigest()

        self._cachefile = os.path.join(tempfile.gettempdir(),
                                       'judgish-tweets-%s' % self.namehash)
        self._tweets = None
        self._twitter = None
        self._uniqueusers = None

    def _loadfromcache(self):
        """Attempt to load recent tweets from a cache file"""
        try:
            with open(self._cachefile) as infile:
                age = time.time() - os.fstat(infile.fileno()).st_mtime
                if age <= CACHE_TIME:
                    logging.debug('Loading cachefile %s (%d seconds old)',
                                  self._cachefile, age)
                    return json.load(infile)
                logging.debug('Not using cachefile %s - too old at %d seconds',
                              self._cachefile, age)
        except Exception as exc:  # pylint: disable=W0703
            logging.info('Unable to read the cache file: %s', exc)
            return None

    def _valueseries(self, values, itemcount):
        """Yield a series of most common item counts, values, and their
        cumulative percentage."""
        runtotal = 0
        for index, (value, count) in enumerate(values.most_common()):
            if index >= self.topcount:
                break
            runtotal += count
            yield {
                'value': value,
                'count': count,
                'cum_count': runtotal,
                'cum_perc': 100.0 * runtotal / itemcount
            }

    @property
    def tweets(self):
        """Return as many of the user's timeline tweets as possible"""
        if self._tweets is not None:
            return self._tweets
        tweets = self.getavailabletweets()

        if self.onlyretweets:
            self._tweets = [tweet for tweet in tweets if 'retweeted_status'
                            in tweet]
        else:
            self._tweets = tweets

        return self._tweets

    def getavailabletweets(self):
        """Return the user's most recent cached or fresh tweets"""
        tweets = self._loadfromcache()
        if tweets is not None:
            return tweets

        tweets = self.twitter.statuses.home_timeline(count=BATCH_SIZE)
        logging.debug('Got %d tweets', len(tweets))

        while True:
            moretweets = self.twitter.statuses.home_timeline(
                count=BATCH_SIZE, max_id=tweets[-1]['id'])
            logging.debug('Got %d more tweets', len(moretweets))
            tweets.extend(moretweets)
            if len(moretweets) < BATCH_THRESHOLD:
                break

        for tweet in tweets:
            sentiment = TextBlob(tweet['text']).sentiment
            tweet['polarity'] = sentiment[0]
            tweet['subjectivity'] = sentiment[1]

        with open(self._cachefile, 'w') as outfile:
            outfile.write(json.dumps(tweets))

        return tweets

    @property
    def twitter(self):
        """Connect to Twitter on demand"""
        if self._twitter is not None:
            return self._twitter

        credfile = os.path.expanduser('~/.judgish-%s' % self.namehash)

        config = ConfigParser.RawConfigParser()
        config.read('client.ini')

        consumer_key = config.get('Consumer', 'key')
        consumer_secret = config.get('Consumer', 'secret')

        if not os.path.exists(credfile):
            twitter.oauth_dance("Judgish", consumer_key, consumer_secret,
                                credfile)

        oauth_token, oauth_secret = twitter.read_token_file(credfile)

        self._twitter = twitter.Twitter(auth=twitter.OAuth(
            oauth_token, oauth_secret, consumer_key, consumer_secret))

        return self._twitter

    @property
    def uniqueusers(self):
        """Return a list of unique users from the timeline"""
        if self._uniqueusers is None:
            uniquemap = {tweet['user']['screen_name']: tweet['user']
                         for tweet in self.tweets}
            self._uniqueusers = uniquemap.values()
        return self._uniqueusers

    def process_alltweets(self, key):
        """Analyze `key` from every tweet in the timeline"""
        values = Counter(tweet[key] for tweet in self.tweets)
        return self._valueseries(values, len(self.tweets))

    def process_allusers(self, key):
        """Analyze user[key] from every tweet in the timeline"""
        values = Counter(tweet['user'][key] for tweet in self.tweets)
        return self._valueseries(values, len(self.tweets))

    def process_uniqueusers(self, key):
        """Analyze user[key] from the set of unique users in the timeline"""
        values = Counter(user[key] for user in self.uniqueusers)
        return self._valueseries(values, len(self.uniqueusers))

    def average_attribute_by_user(self, key):
        """Return the per-user average value of the given attribute"""
        userscores = defaultdict(list)
        for tweet in self.tweets:
            userscores[tweet['user']['screen_name']].append(tweet[key])

        def average(tweetscores):
            """Return the mean of the list of scores"""
            return sum(tweetscores) / len(tweetscores)

        scores = [(average(scorelist), user)
                  for user, scorelist in userscores.items()]

        return reversed(sorted(scores))


def main():
    """Handle the command line"""

    if len(sys.argv) < 2:
        print 'Usage: %s username' % sys.argv[0]
        return

    username = sys.argv[-1]
    onlyretweets = '-r' in sys.argv[1:]

    j = Judge(username, onlyretweets=onlyretweets)

    print 'Tweet count:', len(j.tweets)
    print 'Newest tweet:', j.tweets[0]['created_at']
    print 'Oldest tweet:', j.tweets[-1]['created_at']
    print

    stdformat = '  %(count)d (%(cum_count)d - %(cum_perc).1f%%): %(value)s'
    scoreformat = '  %.3f: %s'

    print 'Most common screen name:'
    for value in j.process_allusers('screen_name'):
        print stdformat % value
    print

    for key in ['time_zone', 'location']:
        print 'Most common unique user %s:' % key
        for value in j.process_uniqueusers(key):
            print stdformat % value
        print

    for key in ['lang', 'source']:
        print 'Most common %s:' % key
        for value in j.process_alltweets(key):
            print stdformat % value
        print

    for key in ['polarity', 'subjectivity']:
        print '%s in decreasing order:' % key.title()
        for value in j.average_attribute_by_user(key):
            print scoreformat % value
        print


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
