# League-Discord-Bot

This is my shot at making my first discord bot. This discord bot is now offline
(because of multiple updates with the API of RiotGames my bot could not fetch the information,
 I have the intention to rewrite a league discord bot with better coding in  the near future
(using AWS, OOP, etc.))

You had to link you discord account to your League of Legends account with a 
3rd party verification tool that I implemented through discord chat with the bot.
Then, the bot would check for discord activities and send the match results of
your last match in a specified discord channel when you finished playing a game.
It would get all the info of the game through the Riot API 
(Had to get an API Key from them by submitting my project) with a library and some JSON
requests.

Here is an example of what it used to send:
![Alt text](DiscordBot.PNG?raw=true "Example")
