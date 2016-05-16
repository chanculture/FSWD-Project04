Christopher Chan: Full Stack Web Developer Nanodegree
==========

Project 6: Design a Game API
==========
As of April 25, 2016 Design a Game API is now Project 6 (previously project 4).

Requirements
==========
* client to communicate with API (methods defined below)

Technology
==========
* Python 2.7.6
* Google App Engine

Instructions
==========
To view source code, clone or download the zip for git repository located at:
https://github.com/chanculture/FSWD-Project04

Google Application Name: udacity-p4-project

Game Instructions
==========
General API instructions
----------
1. In order to play Hangman through the HangmanApi, the client must first create a user.
To do so, the client should use API endpoint create_user
path: user/create_user
(see API endpoints for details)
2. After a user is created.  A new game must be created.  User API endpoint new_game
path: game
(see API endpoints for details)
3. After a game is create, the user can start making guesses passing the url safe game key
to API endpoint make_move
path: game/{urlsafe_game_key}
(see API endpoints for details)
4. User can continue making guesses until the game has completed, or they can cancel the 
game using API endpoint cancel_game
path: game/cancel/{urlsafe_game_key}'
(see API endpoints for details)

Hangman Rules
----------
Each game starts with a new word that is not disclosed to the player.  The word's 
character length is disclosed to the player.  Dependent on the difficulty level chosen for
the game, the length of the word will be between 4 and 18 characters.  The player guesses 
what letters the game's word contain, or alternatively a whole word can be guessed in an 
attempt to solve the game word and win the game.  Dependent on the difficulty level 
chosen for the game, the user will be given between 5 and 9 guess attempts.  However the 
number of guess attempts that will actually occur depends on the number of guesses that 
result in an incorrect guess.  An incorrect guess is defined as a guess attempt of a 
single English alphabet letter that is not contained in game's target word, or a word in 
an attempt to solve the game's word.  It is important to understand that an attempt to 
solve the word will not give any further information to the player except whether the
guessed word was correct or not.

API Endpoints
==========

Create User
----------
path: user/create_user
http method: POST
URL Params: None
Data Params
----------
(required)user_name[string]:unique user name. Value must be alphanumeric with no spaces
	and unique within the HangmanApi Datastore.
(optional)email[string]:email address of user.

Success Response
----------
Code: 200
Content: { "message": "User Created!" }

Error Response
----------
Code: 409
Content: { "message": "A User with that name already exists!" }


New Game
----------
path: game
http method: POST
URL Params: None
Data Params
----------
(required)user_name[string]:unique user name
(optional)difficulty[string]:The difficulty level of the new game. Valid values: EASY,
	NORMAL, HARD, EXPERT.  If not supplied, the default value is NORMAL.
	See Definitions.

Success Response
----------
Code: 200
Content: {
 "game_over": false,
 "user_name": "{user_name}",
 "attempts_remaining": "8",
 "difficulty": "{EASY,NORMAL,HARD,EXPERT}",
 "urlsafe_key": "{game key}",
 "message": "Good luck playing! Take a guess, letter or word!",
 "guess_status": "______",
 "kind": "hangman#resourcesItem",
 "etag": "\"vKJcvsE34HJrPtpjm3-3iIMZBps/UGimU11yPQFbf-chVhGo1bBm_W4\""
}

game_over[boolean]: indicates whether a game is inactive
user_name[string]: user_name for HangmanAPI who created the game
attempts_remaining[integer]: the number of incorrect guesses left before the game is over
difficulty[enumerator]: EASY, NORMAL, HARD, EXPERT
urlsafe_key[string]: the url safe key, passed to manipulate the game data
message[string]: a message indicating the result of the request
guess_status[string]: the current state of the game guesses
kind[string]: datastore generated value
etag[string]: datastore generated value

Error Response
----------
Code: 400
Content: { "message": "Error parsing ProtoRPC request 
	(Unable to parse request content: Invalid enum value \"\")" }
Reason: Invalid difficulty value in request.  Valid values EASY, NORMAL, HARD, EXPERT
	See Definitions


Code: 404
Content: { "message": "A User with that name does not exist!" }
Reason: Invalid user_name in request


Get Game
----------
path: game/{urlsafe_game_key}
http method: GET
URL Params
----------
(required)urlsafe_game_key[string]: the url safe game key used to manipulate the game
	data in PUT requests

Success Response
----------
Code: 200
Content: See "New Game" for explanation.

Error Response
----------
Code: 400
Content: { "message": "Invalid Key" }
Reason: Given key did not match any records


Get User Games
----------
path: user/{user_name}/games
http method: GET
URL Params
----------
(required)user_name[string]: User's user_name for HangmanAPI
(optional)email[string]: Ignored

Success Response
----------
Code: 200
Content: See "New Game" for explanation.  Multiple games can be returned

Error Response
----------
Code: 404
Content: { "message": "A User with that name does not exist!" }
Reason: Entered a user_name that does not match a user in the HangmanAPI


Cancel Game
----------
path: game/cancel/{urlsafe_game_key}'
http method: POST
URL Params
----------
(required)urlsafe_game_key[string]: the url safe game key used to manipulate the game
	data in PUT requests
Data Params: None

Success Response
----------
Code: 200
Content: { message:"Game canceled!" }

Code: 200
Content: { message:"Game is over. Cannot cancel game." }
Reason: Game was already over, and cannot be modified

Error Response
----------
Code: 404
Content: { "message": "Game not found!" }
Reason: urlsafe_game_key value did not match a record in HangmagAPI


Make Move
----------
path: game/{urlsafe_game_key}
http method: PUT
URL Params
----------
(required)urlsafe_game_key[string]: the url safe game key used to manipulate the game
	data in PUT requests
Data Params
----------
(required)guess[string]:character or string of a guess to solve the word.  A value that is
	greater than 1 character counts as an attempt to solve the word.  If the guess is
	incorrect no further information will be give to the user, but they will be charged
	1 guess attempt.

Success Response
----------
Code: 200
Content: See "New Game" for explanation.

Error Response
----------
Code: 400
Content: { "message": "The guess contains non-alphabet characters" }
Reason: the guess contained non-alphabet characters (English alphabet)

Code: 400
Content: { "message": "The guess is missing a value" }
Reason: the guess field in the request is empty

Code: 400
Content: { "Error parsing ProtoRPC request (Unable to parse request content: 
	Message CombinedContainer is missing required field guess)" }
Reason: the guess field in the request is missing


Get Game History
----------
path: game/history/{urlsafe_game_key}'
http method: GET
URL Params
----------
(required)urlsafe_game_key[string]: the url safe game key used to manipulate the game
	data in PUT requests
Data Params: None

Success Response
----------
Code: 200
Content: { "history": [
  "guess:A, result:___A___ Keep Going!",
  "guess:E, result:_E_A__E Keep Going!"
 ], }
 (This is an example)
 
 Array of move history.  First move is indicated in index 0, and subsequent guesses 
 follow sequentially.  Shows the guess, as well as the result of the guess 
 (current status)

Error Response
----------
Code: 400
Content: { "message": "Invalid Key" }
Reason: the give urlsafe_game_key does not match a record in HangmanAPI


Get Scores
----------
path: scores
http method: GET
URL Params: None
Data Params: None

Success Response
----------
Code: 200
Content: {
 "items": [
  {
   "date": "2016-05-13",
   "difficulty": "NORMAL",
   "won": false,
   "guesses": "8",
   "user_name": "pacman",
   "kind": "hangman#resourcesItem"
  }, ...

Represents a Score Kind

Get User Scores
----------
path: scores/user/{user_name}
http method: GET
URL Params
----------
(required)user_name[string]:User's user name for HangmanAPI
(optional)email[string]: Ignored
Data Params: None

Success Response
----------
Code: 200
Content: {
 "items": [
  {
   "date": "2016-05-13",
   "difficulty": "NORMAL",
   "won": false,
   "guesses": "8",
   "user_name": "pacman",
   "kind": "hangman#resourcesItem"
  }, ...


Error Response
----------
Code: 404
Content: { "message": "A User with that name does not exist!" }
Reason: user_name given did not match a record in HangmanAPI


Get High Scores
----------
path: scores/{difficulty}/high
http method: GET
URL Params
----------
(required)difficulty[string]: The difficulty level as defined in GameDifficulty.
	See definitions.  #TODO: Definitions
(optional)number_of_results[integer]: The limit of results wanted in response
Data Params: None

Success Response
----------
Code: 200
Content: {
 "items": [
  {
   "date": "2016-05-13",
   "difficulty": "NORMAL",
   "won": true,
   "guesses": "2",
   "user_name": "chanculture",
   "kind": "hangman#resourcesItem"
  }, ...
  

Error Response
----------
Code: 400
Content: { "message": "Attribute error, parameter: difficulty.  Valid values: EASY, 
	NORMAL, HARD, EXPERT" }
Reason: difficulty value does not match a valid value. See Definitions


Get User Rankings
----------
path: user/rankings
http method: GET
URL Params
----------
(required)difficulty[string]: The difficulty level as defined in GameDifficulty.
	See definitions.  #TODO: Definitions

Success Response
----------
Code: 200
Content: {
 "items": [
  {
   "wins": "4",
   "difficulty": "NORMAL",
   "user_name": "chanculture",
   "win_percentage": 66.67,
   "kind": "hangman#resourcesItem"
  }, ...

Error Response
----------
Code: 400
Content: { "message": "Attribute error, parameter: difficulty.  Valid values: EASY, 
	NORMAL, HARD, EXPERT" }
Reason: difficulty value does not match a valid value. See Definitions


Get Average Attempts
----------
path: games/average_attempts
http method: GET
URL Params: None
Data Params: None

Success Response
----------
Code: 200
Content: { message:"User Created!" }

Error Response
----------
Code: 409
Content: { "message": "A User with that name already exists!" }


Definitions
==========
GameDifficulty represents the difficulty level of the Hangman game.  Valid values are:
* EASY
* NORMAL
* HARD
* EXPERT
Generally, the more difficult the games the longer the word to guess becomes.  Also, the
more difficulty the game level, the fewer incorrect guesses are given.


Extra
==========
Game Difficulty
----------
A game difficulty was added to the specifications to give more flexibility to the user,
as well as the client consuming the API.  Subsequently, certain API methods require a that
the difficulty is passed into the request via a parameter:
* get_high_scores
* get_user_rankings

The main motivator for this design is to simplify the scoring system e.g. to compare 
games that are of similar difficulty, and also to not penalize users who choose EXPERT 
difficulty more often.

Random Word Generator
----------
The words generated for the games come from the random word generator API at:
randomword.setgetgo.com

Credit
==========
Random Word Generator: randomword.setgetgo.com

License
==========
Copyright Christopher Chan
