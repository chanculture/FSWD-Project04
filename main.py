#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import HangmanApi

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email to make.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()

        games = Game.query(Game.game_over == False)
        for game in games:
            user = User.query(User.key == game.user).get()
            subject = 'Your Hangman move is waiting for you'
            body = "Hi {}, don't forget to make your move in Hangman!\n"\
                .format(user.name)
            body += "The current status of your game is {}, "\
                .format(game.get_guess_status())
            body += "and you have {} guesses left."\
                .format(str(game.attempts_remaining))
            if user.email != None:
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                                user.email,
                                subject,
                                body)


class UpdateAverageMovesRemaining(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        HangmanApi._cache_average_attempts()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_attempts', UpdateAverageMovesRemaining),
], debug=True)
