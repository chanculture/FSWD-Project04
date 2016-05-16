import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, GameForms,\
    MakeMoveForm, ScoreForm, ScoreForms, RankingForm, RankingForms,\
    HistoryForm
from models import GameDifficulty
from utils import get_by_urlsafe
from utils import validateGameDifficultyValue

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1),
    email=messages.StringField(2))
HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.IntegerField(1, default=10),
    difficulty=messages.StringField(2, required=True))
RANKINGS_REQUEST = endpoints.ResourceContainer(
    difficulty=messages.StringField(1))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Game API"""

# ========== USERS ENDPOINT API METHODS ==========
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))


# ========== GAME ENDPOINT API METHODS ==========
    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')

        difficulty = validateGameDifficultyValue(request)
        if len(difficulty) > 0:
            game = Game.new_game(user.key, difficulty)
        else:
            game = Game.new_game(user.key)

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        # taskqueue.add(url='/tasks/cache_average_attempts')

        return game.to_form('Good luck playing! Take a guess, letter or word!')


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                return game.to_form('Game is over.')
            else:
                return game.to_form('Make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='user/{user_name}/games',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all the requested User's games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')

        games = Game.query(Game.user == user.key)
        return GameForms(items=[game.to_form() for game in games])


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='POST')
    def cancel_game(self, request):
        """Cancel an active game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                return game.to_form('Game is over. Cannot cancel game.')
            else:
                game.history.append('Game canceled!')
                game.end_game(False)
                return game.to_form('Game canceled!')
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')
        # Check to see if guess is in the request
        if getattr(request, 'guess') in (None, []):
            raise endpoints.BadRequestException('The request is missing a guess!')
        if len(request.guess) < 1:
            raise endpoints.BadRequestException('The guess is missing a value')
        # Check that user has entered a guess with only letters?
        if not request.guess.isalpha():
            raise endpoints.BadRequestException('The guess contains non-alphabet characters')
        # Request checks out, extract value
        guess = str(request.guess).upper()

        # Check the user, has not already guessed this letter or word
        if guess in game.guesses:
            # Return with a message, so client gets 200 status
            return game.to_form('You have already guessed this value.  Try something else!')
        # All checks out, add the guess to the guesses repeatable
        game.guesses.append(guess)
        msg = game.get_guess_status()
        # If guess.length > 1, then user guessed a word
        # Check if guess matches word
        if len(guess) > 1:
            if guess == game.word:
                game.end_game(True)
                return game.to_form('You win! Word is: ' + game.word)
            else:
                game.attempts_remaining -= 1
                msg += ' Incorrect Guess!'
        else: # User Guessed a single letter
            if msg == game.word:
                game.end_game(True)
                return game.to_form('You win! Word is: ' + msg )
            else:
                if not game.is_guess_correct(guess):
                    game.attempts_remaining -= 1
                    msg += ' Incorrect Guess!'

        if game.attempts_remaining < 1:
            msg = msg + ' Game over! The word was ' + game.word
            game.history.append('guess:' + guess + ', result:' + msg)
            game.end_game(False)
        else:
            msg = msg + ' Keep Going!'
            game.history.append('guess:' + guess + ', result:' + msg)
            game.put()
        return game.to_form(msg)


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=HistoryForm,
                      path='game/history/{urlsafe_game_key}',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Returns the Game's History"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        return HistoryForm(history=[history for history in game.history])


# ========== SCORES (SPECIFIC USER) ENDPOINT API METHODS ==========
    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])


# ========== SCORES (GENERAL POPULATION ENDPOINT API METHODS ==========
    @endpoints.method(request_message=HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='scores/{difficulty}/high',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """
        Returns the highest scores given a GameDifficulty level,
        limited by the number_of_results sorted by best first,
        then the most recent
        """
        difficulty = validateGameDifficultyValue(request, True)
        type(request)
        scores = Score.query()
        scores = scores.order(Score.guesses)
        scores = scores.order(-Score.date)
        # Filter by game difficulty and only wons that resulted in a win
        scores = scores.filter(Score.difficulty == difficulty,\
            Score.won == True)
        # Get only the limit of results requested
        scores = scores.fetch(int(request.number_of_results))
        return ScoreForms(items=[score.to_form() for score in scores])


    @endpoints.method(request_message=RANKINGS_REQUEST,
                      response_message=RankingForms,
                      path='user/rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """
        Returns all user rankings given a GameDifficulty level,
        Determined first by winning percentage then by number
        if total wins as the tie breaker.
        """
        difficulty = validateGameDifficultyValue(request, True)
        users = User.query().fetch()
        items = []
        total_games = 0
        wins = 0
        for user in users:
            scores = Score.query().filter(Score.user == user.key)
            for score in scores:
                total_games += 1
                if score.won:
                    wins += 1
            items.append(
                RankingForm(user_name=user.name,
                    difficulty=getattr(GameDifficulty, difficulty),
                    win_percentage=round(float(wins)/total_games*100, 2),
                    wins=wins)
                        )
            total_games = 0
            wins = 0
        return RankingForms(items=items)


    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')


    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([HangmanApi])
