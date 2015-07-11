# Judgish

Analyze and judge the people you follow on App.net and Twitter

# Motivation

I found myself mostly reading lists of just a few select users because my
"home" timeline was far too busy to stay current with it. I had an epiphany:
maybe I'd be better off unfollowing or muting the chattiest users if I wasn't
reading their posts anyway.

Judgish stems from my attempt to reclaim my Twitter timeline.

# Getting Started

Create a [Twitter app](https://apps.twitter.com). This is
inconvenient, but required because developers are forbidden from
sharing their credentials. That is, you can't have my Twitter app
login - you have to get your own.

Create a file called `client.ini` with these contents:

    [Consumer]
    key: <your new Twitter app's "Consumer Key (API Key)">
    secret: <your new Twitter app's "Consumer Secret (API Secret)">

From that directory, run the Judgish command like:

    $ judgish.py your_twitter_username

# License

Judgish is available under the permissive, GPL-compatible MIT License.

# Authors

Kirk Strauser <kirk@strauser.com>

# Terms of Service, Privacy Policy, etc.

Judgish will never modify or post to your accounts in any way. It will not
retransmit messages that it has downloaded for analysis, either in whole or in
part. It downloads messages from your account to your local machine for the
sole purpose of examining their content and presenting the results to you.
