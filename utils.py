"""utils.py - File for collecting general utility functions."""

import logging
from google.appengine.ext import ndb
import endpoints
from models import GameDifficulty

GAME_DIFFICULTY_VALUE_ERROR_MESSAGE = \
    'Attribute error, parameter: difficulty.  ' \
    'Valid values: EASY, NORMAL, HARD, EXPERT'

def get_by_urlsafe(urlsafe, model):
    """Returns an ndb.Model entity that the urlsafe key points to. Checks
        that the type of entity returned is of the correct kind. Raises an
        error if the key String is malformed or the entity is of the incorrect
        kind
    Args:
        urlsafe: A urlsafe key string
        model: The expected entity kind
    Returns:
        The entity that the urlsafe Key string points to or None if no entity
        exists.
    Raises:
        ValueError:"""
    try:
        key = ndb.Key(urlsafe=urlsafe)
    except (TypeError, RuntimeError):
        raise endpoints.BadRequestException('Invalid Key')
    except Exception, e:
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            raise endpoints.BadRequestException('Invalid Key')
        else:
            raise

    entity = key.get()
    if not entity:
        return None
    if not isinstance(entity, model):
        raise ValueError('Incorrect Kind')
    return entity


def validateGameDifficultyValue(request, required=False):
    """Returns a valid GameDifficulty Enum value if one if is provided.
        Raises an Bad BadRequestException if a value is not provided and the
        required parameter = True.  Also if a value was provided, and is not
        valid.
    Args:
        request: The http request object
        required: Indicates whether the difficulty parameter was required in
            the API method
    Returns:
        The entity that the urlsafe Key string points to or None if no entity
        exists.
    Raises:
        ValueError:"""
    if required:
        if not hasattr(request, 'difficulty'):
            raise endpoints.BadRequestException(
                'The request is missing a difficulty parameter!')
        if getattr(request, 'difficulty') in [(None, []), '']:
           raise endpoints.BadRequestException(
                'The difficulty parameter is missing a value!')
    # difficulty parameter name is present, now validate the value
    difficulty = str(getattr(request, 'difficulty'))
    if difficulty.upper() in ['NONE', '']:
        if required:
            raise endpoints.BadRequestException(
                GAME_DIFFICULTY_VALUE_ERROR_MESSAGE)
        else:
            # Default value
            difficulty = 'NORMAL'
    try:
        getattr(GameDifficulty, difficulty)
    except AttributeError:
        raise endpoints.BadRequestException(
            GAME_DIFFICULTY_VALUE_ERROR_MESSAGE)
    return difficulty

