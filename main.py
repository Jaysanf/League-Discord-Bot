import discord
import os
import requests
from keep_alive import keep_alive
import time 
from replit import db
from riotwatcher import LolWatcher




# Basic for discord.py
intents = discord.Intents.default()
intents.members = True
intents.presences = True
client = discord.Client(intents=intents)


# Basic for riotwatcher
server = "na1"
api_key = os.getenv('api_key')
lol_watcher = LolWatcher(api_key)



#### LEAGUE API COMMANDS ####

def get_champion_list():
    '''
    returns a dict containing key data with all champions in 
    the version of the game
    '''
    versions = lol_watcher.data_dragon.versions_for_region(server)
    champions_version = versions['n']['champion']
    return lol_watcher.data_dragon.champions(champions_version)

def champion_played(current_champ_list, last_match):
    '''
    takes current_champ_list(DICT about champions) and last_match info
    to return the champion played
    '''
    for champ in current_champ_list['data']:
        if f"{current_champ_list['data'][champ]['key']}" == f"{last_match['champion']}":
            return champ
        
def specific_player_info(match, AccountId):
    '''
    For a specific match and accountid,
    return the name of the player and a dict with his stats
    '''
    for participant in match['participantIdentities']:
        if participant['player']['accountId'] == AccountId:
            participantID = participant['participantId']
            player_name = participant['player']['summonerName'] 
            break
    for participant in match['participants']:
        if participant['participantId'] == participantID:
            player_participant = participant  
            break
    return player_name, player_participant

def winornot(player_participant):
    '''
    Return a str telling if the player won or not
    '''
    if player_participant['stats']['win']:
        return'VICTORY'
    else:
        return 'DEFEAT'

def check_for_account(user):
    '''
    Looks for user.id in database, if there is not raise exception,
    if there is return the the accountid
    '''
    keys = db.keys()
    if user.id in keys:
        return (db[f"{user.id}"])['accountId']
    else:
        raise Exception("There isn't a LoL account registered to this Discord user.")

def total_damage_in_team(match_detail, player_participant):
    team_id = player_participant['teamId']
    total_team_dmg = 0
    for player in match_detail['participants']:
        if player['teamId'] == team_id:
            total_team_dmg += player['stats']['totalDamageDealtToChampions']
    return(total_team_dmg)

def last_match(user):
        '''
        Take as an input a user object of discord
        and then return information on the last game of league he played
        name (STR) : Discord name and league name
        state_of_game (STR) : win or lost
        score (STR) : kda of player
        player_champion (STR): champion he played
        dmg_dealt_to_champions(STR): DMG DEALT TO ENEMIES
        
        '''

        # Goes through DB to get the riot accountID
        AccountId = check_for_account(user)
        # Gets last match dict
        last_match = (lol_watcher.match.matchlist_by_account(server, AccountId, [0, 2, 4, 6, 7, 8, 9, 14, 16, 17, 25, 31, 32, 33, 41, 42, 52, 61, 65, 67, 70, 72, 73, 75, 76, 78, 83, 91, 92, 93, 96, 98, 100, 300, 310, 313, 315, 317, 318, 325, 400, 410, 420, 430, 440, 450, 460, 470, 600, 610, 700, 800, 810, 820, 830, 840, 850, 900, 910, 920, 940, 950, 960, 980, 990, 1000, 1010, 1020, 1030, 1040, 1050, 1060, 1070, 1090, 1100, 1110, 1111, 1200, 1300, 2000, 2010, 2020]))['matches'][0]

        # gets info on last_match
        match_detail = lol_watcher.match.by_id(server, last_match['gameId'])

        queue = match_detail['queueId']
        game_duration = match_detail['gameDuration']

        # gets info of specific player in last match
        player_name, player_participant = specific_player_info(match_detail, AccountId)
        
        #GETS VERSION
        current_champ_list = get_champion_list()

        # GETS THE CHAMPION
        player_champion =  champion_played(current_champ_list, last_match)
        
        # Stores Discord name and League of legend name
        name = f"{player_name} ({user.name}#{user.discriminator}) "

        # Store the KDA of the player
        score = f"{player_participant['stats']['kills']} / {player_participant['stats']['deaths']} / {player_participant['stats']['assists']}"

        team_dmg = total_damage_in_team(match_detail,player_participant)
        percentdmg = round((player_participant['stats']['totalDamageDealtToChampions']/team_dmg  * 100),2)


        lane = player_participant['timeline']['lane']
        

        dmg_dealt_to_champions = f"{player_participant['stats']['totalDamageDealtToChampions']} DMG ({percentdmg}%)"
        # Store if the player won or lost
        state_of_game = winornot(player_participant)
        csgold = f"{player_participant['stats']['totalMinionsKilled'] + player_participant['stats']['neutralMinionsKilled'] } Cs / {player_participant['stats']['goldEarned']} Gold"


        return name, state_of_game, score, player_champion, dmg_dealt_to_champions, queue, game_duration, user, csgold, lane

def find_queue_type(queueID_of_game):
    all_queues = [
    {
        "queueId": 0,
        "map": "Custom games",
        "description": None,
        "notes": None
    },
    {
        "queueId": 2,
        "map": "Summoner's Rift",
        "description": "5v5 Blind Pick games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 430"
    },
    {
        "queueId": 4,
        "map": "Summoner's Rift",
        "description": "5v5 Ranked Solo games",
        "notes": "Deprecated in favor of queueId 420"
    },
    {
        "queueId": 6,
        "map": "Summoner's Rift",
        "description": "5v5 Ranked Premade games",
        "notes": "Game mode deprecated"
    },
    {
        "queueId": 7,
        "map": "Summoner's Rift",
        "description": "Co-op vs AI games",
        "notes": "Deprecated in favor of queueId 32 and 33"
    },
    {
        "queueId": 8,
        "map": "Twisted Treeline",
        "description": "3v3 Normal games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 460"
    },
    {
        "queueId": 9,
        "map": "Twisted Treeline",
        "description": "3v3 Ranked Flex games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 470"
    },
    {
        "queueId": 14,
        "map": "Summoner's Rift",
        "description": "5v5 Draft Pick games",
        "notes": "Deprecated in favor of queueId 400"
    },
    {
        "queueId": 16,
        "map": "Crystal Scar",
        "description": "5v5 Dominion Blind Pick games",
        "notes": "Game mode deprecated"
    },
    {
        "queueId": 17,
        "map": "Crystal Scar",
        "description": "5v5 Dominion Draft Pick games",
        "notes": "Game mode deprecated"
    },
    {
        "queueId": 25,
        "map": "Crystal Scar",
        "description": "Dominion Co-op vs AI games",
        "notes": "Game mode deprecated"
    },
    {
        "queueId": 31,
        "map": "Summoner's Rift",
        "description": "Co-op vs AI Intro Bot games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 830"
    },
    {
        "queueId": 32,
        "map": "Summoner's Rift",
        "description": "Co-op vs AI Beginner Bot games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 840"
    },
    {
        "queueId": 33,
        "map": "Summoner's Rift",
        "description": "Co-op vs AI Intermediate Bot games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 850"
    },
    {
        "queueId": 41,
        "map": "Twisted Treeline",
        "description": "3v3 Ranked Team games",
        "notes": "Game mode deprecated"
    },
    {
        "queueId": 42,
        "map": "Summoner's Rift",
        "description": "5v5 Ranked Team games",
        "notes": "Game mode deprecated"
    },
    {
        "queueId": 52,
        "map": "Twisted Treeline",
        "description": "Co-op vs AI games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 800"
    },
    {
        "queueId": 61,
        "map": "Summoner's Rift",
        "description": "5v5 Team Builder games",
        "notes": "Game mode deprecated"
    },
    {
        "queueId": 65,
        "map": "Howling Abyss",
        "description": "5v5 ARAM games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 450"
    },
    {
        "queueId": 67,
        "map": "Howling Abyss",
        "description": "ARAM Co-op vs AI games",
        "notes": "Game mode deprecated"
    },
    {
        "queueId": 70,
        "map": "Summoner's Rift",
        "description": "One for All games",
        "notes": "Deprecated in patch 8.6 in favor of queueId 1020"
    },
    {
        "queueId": 72,
        "map": "Howling Abyss",
        "description": "1v1 Snowdown Showdown games",
        "notes": None
    },
    {
        "queueId": 73,
        "map": "Howling Abyss",
        "description": "2v2 Snowdown Showdown games",
        "notes": None
    },
    {
        "queueId": 75,
        "map": "Summoner's Rift",
        "description": "6v6 Hexakill games",
        "notes": None
    },
    {
        "queueId": 76,
        "map": "Summoner's Rift",
        "description": "Ultra Rapid Fire games",
        "notes": None
    },
    {
        "queueId": 78,
        "map": "Howling Abyss",
        "description": "One For All: Mirror Mode games",
        "notes": None
    },
    {
        "queueId": 83,
        "map": "Summoner's Rift",
        "description": "Co-op vs AI Ultra Rapid Fire games",
        "notes": None
    },
    {
        "queueId": 91,
        "map": "Summoner's Rift",
        "description": "Doom Bots Rank 1 games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 950"
    },
    {
        "queueId": 92,
        "map": "Summoner's Rift",
        "description": "Doom Bots Rank 2 games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 950"
    },
    {
        "queueId": 93,
        "map": "Summoner's Rift",
        "description": "Doom Bots Rank 5 games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 950"
    },
    {
        "queueId": 96,
        "map": "Crystal Scar",
        "description": "Ascension games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 910"
    },
    {
        "queueId": 98,
        "map": "Twisted Treeline",
        "description": "6v6 Hexakill games",
        "notes": None
    },
    {
        "queueId": 100,
        "map": "Butcher's Bridge",
        "description": "5v5 ARAM games",
        "notes": None
    },
    {
        "queueId": 300,
        "map": "Howling Abyss",
        "description": "Legend of the Poro King games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 920"
    },
    {
        "queueId": 310,
        "map": "Summoner's Rift",
        "description": "Nemesis games",
        "notes": None
    },
    {
        "queueId": 313,
        "map": "Summoner's Rift",
        "description": "Black Market Brawlers games",
        "notes": None
    },
    {
        "queueId": 315,
        "map": "Summoner's Rift",
        "description": "Nexus Siege games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 940"
    },
    {
        "queueId": 317,
        "map": "Crystal Scar",
        "description": "Definitely Not Dominion games",
        "notes": None
    },
    {
        "queueId": 318,
        "map": "Summoner's Rift",
        "description": "ARURF games",
        "notes": "Deprecated in patch 7.19 in favor of queueId 900"
    },
    {
        "queueId": 325,
        "map": "Summoner's Rift",
        "description": "All Random games",
        "notes": None
    },
    {
        "queueId": 400,
        "map": "Summoner's Rift",
        "description": "5v5 Draft Pick games",
        "notes": None
    },
    {
        "queueId": 410,
        "map": "Summoner's Rift",
        "description": "5v5 Ranked Dynamic games",
        "notes": "Game mode deprecated in patch 6.22"
    },
    {
        "queueId": 420,
        "map": "Summoner's Rift",
        "description": "5v5 Ranked Solo games",
        "notes": None
    },
    {
        "queueId": 430,
        "map": "Summoner's Rift",
        "description": "5v5 Blind Pick games",
        "notes": None
    },
    {
        "queueId": 440,
        "map": "Summoner's Rift",
        "description": "5v5 Ranked Flex games",
        "notes": None
    },
    {
        "queueId": 450,
        "map": "Howling Abyss",
        "description": "5v5 ARAM games",
        "notes": None
    },
    {
        "queueId": 460,
        "map": "Twisted Treeline",
        "description": "3v3 Blind Pick games",
        "notes": "Deprecated in patch 9.23"
    },
    {
        "queueId": 470,
        "map": "Twisted Treeline",
        "description": "3v3 Ranked Flex games",
        "notes": "Deprecated in patch 9.23"
    },
    {
        "queueId": 600,
        "map": "Summoner's Rift",
        "description": "Blood Hunt Assassin games",
        "notes": None
    },
    {
        "queueId": 610,
        "map": "Cosmic Ruins",
        "description": "Dark Star: Singularity games",
        "notes": None
    },
    {
        "queueId": 700,
        "map": "Summoner's Rift",
        "description": "Clash games",
        "notes": None
    },
    {
        "queueId": 800,
        "map": "Twisted Treeline",
        "description": "Co-op vs. AI Intermediate Bot games",
        "notes": "Deprecated in patch 9.23"
    },
    {
        "queueId": 810,
        "map": "Twisted Treeline",
        "description": "Co-op vs. AI Intro Bot games",
        "notes": "Deprecated in patch 9.23"
    },
    {
        "queueId": 820,
        "map": "Twisted Treeline",
        "description": "Co-op vs. AI Beginner Bot games",
        "notes": None
    },
    {
        "queueId": 830,
        "map": "Summoner's Rift",
        "description": "Co-op vs. AI Intro Bot games",
        "notes": None
    },
    {
        "queueId": 840,
        "map": "Summoner's Rift",
        "description": "Co-op vs. AI Beginner Bot games",
        "notes": None
    },
    {
        "queueId": 850,
        "map": "Summoner's Rift",
        "description": "Co-op vs. AI Intermediate Bot games",
        "notes": None
    },
    {
        "queueId": 900,
        "map": "Summoner's Rift",
        "description": "URF games",
        "notes": None
    },
    {
        "queueId": 910,
        "map": "Crystal Scar",
        "description": "Ascension games",
        "notes": None
    },
    {
        "queueId": 920,
        "map": "Howling Abyss",
        "description": "Legend of the Poro King games",
        "notes": None
    },
    {
        "queueId": 940,
        "map": "Summoner's Rift",
        "description": "Nexus Siege games",
        "notes": None
    },
    {
        "queueId": 950,
        "map": "Summoner's Rift",
        "description": "Doom Bots Voting games",
        "notes": None
    },
    {
        "queueId": 960,
        "map": "Summoner's Rift",
        "description": "Doom Bots Standard games",
        "notes": None
    },
    {
        "queueId": 980,
        "map": "Valoran City Park",
        "description": "Star Guardian Invasion: Normal games",
        "notes": None
    },
    {
        "queueId": 990,
        "map": "Valoran City Park",
        "description": "Star Guardian Invasion: Onslaught games",
        "notes": None
    },
    {
        "queueId": 1000,
        "map": "Overcharge",
        "description": "PROJECT: Hunters games",
        "notes": None
    },
    {
        "queueId": 1010,
        "map": "Summoner's Rift",
        "description": "Snow ARURF games",
        "notes": None
    },
    {
        "queueId": 1020,
        "map": "Summoner's Rift",
        "description": "One for All games",
        "notes": None
    },
    {
        "queueId": 1030,
        "map": "Crash Site",
        "description": "Odyssey Extraction: Intro games",
        "notes": None
    },
    {
        "queueId": 1040,
        "map": "Crash Site",
        "description": "Odyssey Extraction: Cadet games",
        "notes": None
    },
    {
        "queueId": 1050,
        "map": "Crash Site",
        "description": "Odyssey Extraction: Crewmember games",
        "notes": None
    },
    {
        "queueId": 1060,
        "map": "Crash Site",
        "description": "Odyssey Extraction: Captain games",
        "notes": None
    },
    {
        "queueId": 1070,
        "map": "Crash Site",
        "description": "Odyssey Extraction: Onslaught games",
        "notes": None
    },
    {
        "queueId": 1090,
        "map": "Convergence",
        "description": "Teamfight Tactics games",
        "notes": None
    },
    {
        "queueId": 1100,
        "map": "Convergence",
        "description": "Ranked Teamfight Tactics games",
        "notes": None
    },
    {
        "queueId": 1110,
        "map": "Convergence",
        "description": "Teamfight Tactics Tutorial games",
        "notes": None
    },
    {
        "queueId": 1111,
        "map": "Convergence",
        "description": "Teamfight Tactics test games",
        "notes": None
    },
    {
        "queueId": 1200,
        "map": "Nexus Blitz",
        "description": "Nexus Blitz games",
        "notes": "Deprecated in patch 9.2"
    },
    {
        "queueId": 1300,
        "map": "Nexus Blitz",
        "description": "Nexus Blitz games",
        "notes": None
    },
    {
        "queueId": 2000,
        "map": "Summoner's Rift",
        "description": "Tutorial 1",
        "notes": None
    },
    {
        "queueId": 2010,
        "map": "Summoner's Rift",
        "description": "Tutorial 2",
        "notes": None
    },
    {
        "queueId": 2020,
        "map": "Summoner's Rift",
        "description": "Tutorial 3",
        "notes": None
    }
    ]
    for queue in all_queues:
        if queue['queueId'] == int(queueID_of_game):
            the_map = queue['map']
            description = queue['description']
            return the_map, description
    
    raise Exception('No map found?')
#### DISCORD FUNCTIONS ####

async def add_user(message):
    '''
    Gets message object and send a message through
    '''
    # Gets username in the message

    try:
        username = message.content.replace('!add', '')

        users_tagged = message.raw_mentions


        if len(users_tagged) > 1:
            raise Exception('You must Only input one user')
        elif len(users_tagged) == 1:
            if message.author.guild_permissions.administrator:
                key = users_tagged[0]
                pos = username.find('<@')
                username = username[:pos]
            else:
                raise Exception('You must be an Admin to run this command')
        else:
            key = message.author.id


        # checks for blank username
        if not username:
            raise Exception('You did not put a Username')

        # Gets Summoner ID
        user = lol_watcher.summoner.by_name(server, username)
        
        # Checks for non_existing user
        if not(user):
            raise Exception("User Not Found")
        
        if key == message.author.id:
            ### url to request
            x =(f"https://na1.api.riotgames.com/lol/platform/v4/third-party-code/by-summoner/{user['id']}?api_key={api_key.replace(' ','')}")

            # Requests the third party verification
            response = requests.get(x)
            if response.text != '"JaysanfLeagueDiscordBot"':
                raise Exception('You must enter this third-party verification code in your league client: JaysanfLeagueDiscordBot')
        

        await message.channel.send('The Username was valid!')

        # << Puts user in DB >>
        db[f"{key}"] = user

    except Exception as e:
        await message.channel.send(f'Error: {e}')

async def last_match_info(message):
           
    try:
        # GET the guild and channel
        channel = message.channel
        guild = channel.guild
        
        async with channel.typing():
            parameters = message.content.replace('!last', '') 
            # Gets user
            if parameters:
                # replace the Tag
                users_tagged = message.raw_mentions

                if len(users_tagged) != 1:
                    raise Exception('You must only @ one person')
                
                # put the first user found in user:
                user = guild.get_member(int(users_tagged[0]))
                 
                


            else:
                user = guild.get_member(int(message.author.id))
                

            # Gets info of the last match
            
            name, state_of_game, score, player_champion, dmg_dealt_to_champions, queue, game_duration, loluser, csgold, lane = last_match(user)
            the_map, description = find_queue_type(queue)
            
            
            game_duration = time.strftime('%H:%M:%S', time.gmtime(int(game_duration)))

            champion_image = f"http://ddragon.leagueoflegends.com/cdn/img/champion/splash/{player_champion}_0.jpg"

            user_profile_pic = loluser.avatar_url

            message_embed = discord.Embed(
                title= name)
            
            message_embed.set_image(url=champion_image)

            message_embed.set_author(
                name= description[:-5],
                icon_url=f'{user_profile_pic}')

            message_embed.set_footer(
            text="This bot was made by Djey#0475",
            icon_url="https://cdn.discordapp.com/avatars/220252861227991040/5313e48e69b155e02c5d5399f069b744.webp?size=256")

            message_embed.add_field(name=f"{state_of_game}",value="—————", inline=False)
            message_embed.add_field(name="KDA", value=f"{score}", inline=False)
            message_embed.add_field(name="CS / Gold Earned", value=f"{csgold}", inline=False)
            message_embed.add_field(name="Total Damage Dealt to Champions", value=f"{dmg_dealt_to_champions}", inline=False)

            message_embed.add_field(name="Duration of the game", value=f"{game_duration}", inline=False)

            message_embed.add_field(name="Lane", value=f"{lane}", inline=False)

            message_embed.add_field(name="Champion Played", value=f"{player_champion}", inline=False)

           
                


            await message.channel.send(f"<@{user.id}>")
            await message.channel.send(embed=message_embed)
            return
        

    
    except Exception as e:
        await message.channel.send(f'Error: {e}')

async def del_user(message):
    '''
    Gets message object and send a message through
    '''

    try:
        # GET the guild and channel
       
        
        parameters = message.content.replace('!deluser', '')

        if parameters:
            users_tagged = message.raw_mentions
            if message.author.guild_permissions.administrator:
                #TODO
                for user in users_tagged:
                    del db[f'{user}']
                    await message.channel.send(f'{user} has been deleted')
            else:
                await message.channel.send('You do not have the permisssions to do that')
       
        else:
            # << Remove user in DB >>
            del db[f"{message.author.id}"] 
            await message.channel.send('Your Riot Account linked to this Discord Account has been removed')

    except Exception as e:
        await message.channel.send(f'Error: {e}')

async def del_all(message):
    '''
    Gets message object and send a message through
    '''

    try:
        # GET the guild and channel
        channel = message.channel
        guild = channel.guild
        if message.author.guild_permissions.administrator:
            users_list = db.keys() 
            for user in users_list:
                if guild.get_member(int(user)):
                    del db[f'{user}']
                    await message.channel.send(f'{user} has been deleted')
        else:
            await message.channel.send('You do not have the permisssions to do that')

    except Exception as e:
        await message.channel.send(f'Error: {e}')

async def helpmessage(message):
    """
    send the help message as an embed object in discord
    """
    message_embed = discord.Embed(
    title= "Help -- All functions for League discord Bot")

    message_embed.set_footer(
    text="This bot was made by Djey#0475",
    icon_url="https://cdn.discordapp.com/avatars/220252861227991040/5313e48e69b155e02c5d5399f069b744.webp?size=256")

    if message.author.guild_permissions.administrator:
        message_embed.add_field(name="!add [Riot Username] {User Mentions}",value=(
        "Parameters\n"
        "\n"
        "[Riot Username]: The riot username you want to associate to the discord user\n"
        "\n"
        "{User Mentions}:-ADMIN- (Optional) The discord user you want the Riot \n" 
        "Username associated to, leave blank if you are this user\n"
        "\n"
        "Add a Riot Username linked to a User to the Database ")
        , inline=False)
        
        message_embed.add_field(name="!deluser {User Mentions}",value=(
        "Parameters\n"
        "\n"
        "{User Mentions}:-ADMIN- (Optional) The discord user you want to remove\n"
        "from the Database, leave blank if you are this user\n" 
        "\n"
        "Remove a user from the Database")
        , inline=False)
        
        message_embed.add_field(name="!delall",value=(
        "-ADMIN-\n"
        "\n"
        "Remove all users from the Database")
        , inline=False)

        message_embed.add_field(name="!last {User Mentions}", value=(
        "Parameters\n"
        "\n"
        "{User Mentions}:(Optional) Choose a user you want to see last LoL match\n"
        "from the Database, leave blank if you are this user\n" 
        "\n"
        "Give the stats of the last game of LoL a user played")
        , inline=False)

        message_embed.add_field(name="!help",value="Show This message", inline=False)
    else:
        message_embed.add_field(name="!add [Riot Username]",value=(
        "Parameters\n"
        "\n"
        "[Riot Username]: The riot username you want to associate to the discord user\n"
        "\n"
        "Add a Riot Username linked to a User to the Database")
        , inline=False)
        
        message_embed.add_field(name="!deluser",value=(
        "Remove your user from the Database")
        , inline=False)
        

        message_embed.add_field(name="!last {User Mentions}", value=(
        "Parameters\n"
        "\n"
        "{User Mentions}:(Optional) Choose a user you want to see last LoL match\n"
        "from the Database, leave blank if you are this user\n" 
        "\n"
        "Give the stats of the last game of LoL a user played")
        , inline=False)

        message_embed.add_field(name="!help",value="Show This message", inline=False)
    

    await message.channel.send(embed=message_embed)
    return

async def create_feed_channel_and_command_channel(message):
    
    try:
        if not(message.author.guild_permissions.administrator):
            raise Exception('You need to have admin privilege to run this command')

        channel = message.channel
        guild = channel.guild

        # get all keys
        keys = db.keys()

        # Check for already in key
        if guild.id in keys:
            ids = db[f'{guild.id}']
            feed_channel = client.get_channel(ids['feed_channel']).name
            command_channel = client.get_channel(ids['command_channel']).name
            raise Exception(f'Channels already exists = > Feed Channel: {feed_channel}, Command Channel: {command_channel}')
        overwrites = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False),
        }
        feed_channel = await guild.create_text_channel('LDB-Feed-Channel', overwrites=overwrites)
        command_channel = await guild.create_text_channel('LDB-Command-Channel')

        dbvalue = {'feed_channel':feed_channel.id
        ,'command_channel':command_channel.id }

        db[f"{guild.id}"] = dbvalue
        await command_channel.send('Channels succesfully created and inserted into Database')

    except Exception as e:
        await message.channel.send(f'Error: {e}')
    
async def removechannel(message):
    try:
        if not(message.author.guild_permissions.administrator):
            raise Exception('You need to have admin privilege to run this command')

        channel = message.channel
        guild = channel.guild

        # get all keys
        keys = db.keys()

        # Check for already in key
        if guild.id in keys:
            ids = db[f'{guild.id}']

            feed_channel = client.get_channel(ids['feed_channel'])
            command_channel = client.get_channel(ids['command_channel'])

            await feed_channel.delete(reason="Function !removechannel has been called by an admin")
            await command_channel.delete(reason="Function !removechannel has been called by an admin")


            del db[f'{guild.id}']

        else:
            raise Exception(f'Channels already exists = > Feed Channel: {feed_channel}, Command Channel: {command_channel}')

    except Exception as e:
        await message.channel.send(f'Error: {e}')

async def last_match_by_member(member):
           
    try:
        # GET the guild and channel
        guild = member.guild
        get_channel = client.get_channel(db[f'{guild.id}']['feed_channel'])
        async with get_channel.typing():
                 
        

            # Gets info of the last match
            
            name, state_of_game, score, player_champion, dmg_dealt_to_champions, queue, game_duration, loluser, csgold, lane = last_match(member)
            the_map, description = find_queue_type(queue)
            
            game_duration = time.strftime('%H:%M:%S', time.gmtime(int(game_duration)))

            champion_image = f"http://ddragon.leagueoflegends.com/cdn/img/champion/splash/{player_champion}_0.jpg"

            user_profile_pic = loluser.avatar_url

            message_embed = discord.Embed(
                title= name)
            
            message_embed.set_image(url=champion_image)

            message_embed.set_author(
                name= description[:-5],
                icon_url=f'{user_profile_pic}')

            message_embed.set_footer(
            text="This bot was made by Djey#0475",
            icon_url="https://cdn.discordapp.com/avatars/220252861227991040/5313e48e69b155e02c5d5399f069b744.webp?size=256")

            message_embed.add_field(name=f"{state_of_game}",value="—————", inline=False)
            message_embed.add_field(name="KDA", value=f"{score}", inline=False)
            message_embed.add_field(name="CS / Gold Earned", value=f"{csgold}", inline=False)
            message_embed.add_field(name="Total Damage Dealt to Champions", value=f"{dmg_dealt_to_champions}", inline=False)

            message_embed.add_field(name="Duration of the game", value=f"{game_duration}", inline=False)

            message_embed.add_field(name="Lane", value=f"{lane}", inline=False)

            message_embed.add_field(name="Champion Played", value=f"{player_champion}", inline=False)

           

               
            await get_channel.send(f"<@{member.id}>")
            await get_channel.send(embed=message_embed)
            return
    except Exception as e:
        await get_channel.send(f'Error: {e}')

async def clear_channel(message):
    '''
    Gets message object and send a message through
    '''

    try:
        # GET the guild and channel
        channel = message.channel
        guild = channel.guild
        if message.author.guild_permissions.administrator:
            del db[f'{guild.id}']
            await message.channel.send('Channel has been cleared')
        else:
            await message.channel.send('You do not have the permisssions to do that')

    except Exception as e:
        await message.channel.send(f'Error: {e}')


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="to !help"))
    print("We have logged in as {0.user}".format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
                # Commands that bypass channel restriction
    #### first command to put in a discord ###
    if message.content.startswith('!init'):
        await create_feed_channel_and_command_channel(message)
        return
    elif message.content.startswith('!clearchannel'):
        await clear_channel(message)
        return

    ## Help commands
    if message.content.startswith('!help'):
        await helpmessage(message)
        return
    
    ### ignore non-commands
    if not(message.content.startswith('!')):
        return

    # Gets Info on Channel and Guild
    channel = message.channel
    guild = channel.guild
    keys = db.keys()
    
    # If not in Database, does not let the user input the commands below
    if not(guild.id in keys):
        await message.channel.send('You need to do !init to initialize bot-related channel')
        return

    # Make sure the user use the commands in the command Channel
    if channel.id != db[f'{guild.id}']['command_channel'] :
        command_channel = client.get_channel(db[f'{guild.id}']['command_channel']).name
        
        await message.author.send(f'You need to type commands in the Command channel: {command_channel}')
        await message.delete()
        return

    ##### PUTS USER TO DATABASE #######
    if message.content.startswith('!add'):
        await add_user(message)

    ##### Gives info on last match for specific player #####
    elif message.content.startswith('!last'):
        await last_match_info(message)

    ##### DELETE USER FROM DATABASE #######
    elif message.content.startswith('!deluser'):
        await del_user(message)
    
    #### DELETES ALL USER FROM YOUR DISCORD FROM DATABASE #####
    elif message.content.startswith('!delall'):
        await del_all(message)

    elif message.content.startswith('!removechannel'):
        await removechannel(message)


@client.event
async def on_member_update(before, after):


    if not(before.activity) or not(after.activity):
        return

    if before.activity.type != discord.ActivityType.playing and after.activity.type != discord.ActivityType.playing:
        return
    print(f'............{before.name}...............')
    print("-----------BEFORE------------")
            
    print(before.activity.application_id)
    print(before.activity.assets)
    print(before.activity.details)
    print(before.activity.emoji)
    print(before.activity.end)
    print(before.activity.small_image_text)
    print(before.activity.large_image_text)
    print(before.activity.name)
    print(before.activity.party)
    print(before.activity.start)
    print(before.activity.state)
    print(before.activity.timestamps)
    print(before.activity.type)
    print(before.activity.url)

    print("-----------AFTER------------")

    print(after.activity.application_id)
    print(after.activity.assets)
    print(after.activity.details)
    print(after.activity.emoji)
    print(after.activity.end)
    print(after.activity.small_image_text)
    print(after.activity.large_image_text)
    print(after.activity.name)
    print(after.activity.party)
    print(after.activity.start)
    print(after.activity.state)
    print(after.activity.timestamps)
    print(after.activity.type)
    print(after.activity.url)

    
   
    if before.activity.name == "League of Legends" and after.activity.name == "League of Legends":
        
        if before.activity.state == "In Game" and after.activity.state == None:
            keys  = db.keys()
            print('UNE GAME VIENS DE FINIR')
            print('-----------',before.name,'-----------')
            if f'{before.id}' in keys:
                time.sleep(10)
                await last_match_by_member(before)
    return







    



keep_alive()
client.run(os.getenv('TOKEN'))

