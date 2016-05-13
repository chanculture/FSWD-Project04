"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
import urllib2
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


# ========== USER ==========
class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()


# ========== GAME ==========
class Game(ndb.Model):
    """Game object"""
    word = ndb.StringProperty(required=True)
    attempts_allowed = ndb.IntegerProperty(required=True, default=8)
    attempts_remaining = ndb.IntegerProperty(required=True, default=8)
    game_over = ndb.BooleanProperty(required=True, default=False)
    guesses = ndb.StringProperty(repeated=True)
    # guess_status represents the word with correct guesses filled
    # in, and letters not yet guessed filled with a '_' character
    # This will be a computed value.
    # guess_status = ndb.StringProperty(required=True)
    user = ndb.KeyProperty(required=True, kind='User')
    difficulty = ndb.StringProperty(default='NORMAL')

    @classmethod
    def new_game(cls, user, difficulty='NORMAL'):
        """Creates and returns a new game"""
        # determine word length based on difficulty selected
        word_length = get_word_length(difficulty)
        url = ('http://randomword.setgetgo.com/get.php?len=%s'
           % word_length)
        word = urllib2.urlopen(url).read()
        # uppercase the word
        word = word.upper()
        # DEVELOPMENT
        # print word
        if len(word) < 4:
            raise ValueError('Unable to generate a word to guess!')
        # determine the number of incorrect guesses are allowed.
        attempts = get_attempts_allowed(difficulty)

        game = Game(user=user,
                    word=word,
                    attempts_allowed=attempts,
                    attempts_remaining=attempts,
                    game_over=False,
                    difficulty=str(difficulty).upper(),
                )
        game.put()
        return game

    def get_guess_status(self):
        """This is a computed getter"""
        val = ""
        found = False
        for c in self.word:
            if val == self.word:
                break
            for guess in self.guesses:
                if len(guess) == 1 and guess == c:
                    val += c
                    found = True
                    break
                elif len(guess) > 1 and guess == self.word:
                    val = guess
                    found = True
                    break
            if found:
                found = False
            else:
                val += "_"
        return val

    def is_guess_correct(self, guess):
        return self.word.find(guess) >= 0

    def to_form(self, message=''):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        # convert GameDifficulty string to Enum
        form.difficulty = getattr(GameDifficulty, getattr(self, 'difficulty'))
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.guesses = self.guesses
        form.guess_status = self.get_guess_status()
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, game=self.key,
                      date=date.today(), won=won,
                      guesses=self.attempts_allowed - self.attempts_remaining,
                      difficulty=self.difficulty
                      )
        score.put()


class GameDifficulty(messages.Enum):
    """GameDifficulty enumeration value"""
    EASY = 1
    NORMAL = 2
    HARD = 3
    EXPERT = 4


# ========== SCORE ==========
class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    game = ndb.KeyProperty(required=True, kind='Game')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)
    difficulty = ndb.StringProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses,
                         difficulty=getattr(GameDifficulty, self.difficulty))


# ========== FORMS ==========
class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    guesses = messages.StringField(5, repeated=True)
    guess_status = messages.StringField(6, required=True)
    user_name = messages.StringField(7, required=True)
    difficulty = messages.EnumField('GameDifficulty', 8)


class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    difficulty = messages.EnumField('GameDifficulty', 2)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)
    difficulty = messages.EnumField('GameDifficulty', 5,
        required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class RankingForm(messages.Message):
    """RankingForm for outbound User Ranking information"""
    user_name = messages.StringField(1, required=True)
    difficulty = messages.EnumField('GameDifficulty', 2,
        required=True)
    win_percentage = messages.FloatField(3, required=True)
    wins = messages.IntegerField(4, required=True)


class RankingForms(messages.Message):
    """Return multiple RankingForms"""
    items = messages.MessageField(RankingForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)


# ========== GAME HELPER FUNCTIONS ==========
def get_attempts_allowed(difficulty):
    """
    This method determines the number of incorrect guesses
    allowed, based on the difficulty of the game.
    inputs:
        :difficulty <GameDifficulty:enum>
    output:
        :<Int> the number of incorrect guesses allowed before
    """
    if difficulty == GameDifficulty.EASY:
        attempts = 9
    elif difficulty == GameDifficulty.NORMAL:
        attempts = 8
    elif difficulty == GameDifficulty.HARD:
        attempts = 7
    elif difficulty == GameDifficulty.EXPERT:
        attempts = 5
    else:
        attempts = 8
    return attempts


def get_word_length(difficulty):
    """
    This method determines the length of the word that will be
    created for the game, based on the difficulty of the game.
    inputs:
        :difficulty <GameDifficulty:enum>
    output:
        :<Int> the length of the word
    """
    if difficulty == GameDifficulty.EASY:
        word_length = random.choice(range(4, 6))
    elif difficulty == GameDifficulty.NORMAL:
        word_length = random.choice(range(6, 9))
    elif difficulty == GameDifficulty.HARD:
        word_length = random.choice(range(9, 13))
    elif difficulty == GameDifficulty.EXPERT:
        word_length = random.choice(range(7, 18))
    else:
        word_length = random.choice(range(6, 8))
    return word_length
