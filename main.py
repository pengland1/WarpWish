import discord, json, random, time, math, os, calendar
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime

#region Setup
#   Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

#   Setting up the Discord Intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)

#   Setting up the command tree for slash commands
tree = app_commands.CommandTree(client)
#endregion

#region Regular Functions
def getLowestTimeSpan(userRoles):
    """
    Function to find the lowest time span in the config.json file.
    """
    #   Open the config.json file and load the data into a variable
    file = open("config.json")
    configData = json.load(file)
    file.close()

    # Extract the IDs from userRoles into a set for efficient lookup
    userRoleIds = set(str(role.id) for role in userRoles)

    #   Loop through the roles in the config.json file and find the lowest time span
    timespan = None
    for role in configData["roles"]:
        # Check if the user has this role by comparing IDs
        if str(role["id"]) in userRoleIds:
            # If this is the first role we're checking, or the timespan is lower than the current lowest timespan, update the lowest timespan.
            if timespan == None:
                timespan = int(role["time_span"])
            if int(role["time_span"]) < timespan:
                timespan = int(role["time_span"])
    return timespan

def getFirstAvailableTimespan(userRoles):
    #   Open the config.json file and load the data into a variable
    file = open("config.json")
    configData = json.load(file)
    file.close()

    # Extract the IDs from userRoles into a set for efficient lookup
    userRoleIds = set(str(role.id) for role in userRoles)

    for role in configData["roles"]:
        if str(role["id"]) in userRoleIds:
            return int(role["time_span"])
    
def isAccessible(userRoles):
    
    file = open("config.json")
    configData = json.load(file)
    file.close()
    userRoleIDS = [str(role.id) for role in userRoles]
    for role in configData["roles"]:
        if role["id"] in userRoleIDS:
            return True
    return False

def getRandomResponseTimestamp(responseType, rawTimeStampText):
    """
    Function to get a random response from the config.json file and replace the {timeStamp} with the appropriate timestamp text.
    """
    #   Parse the rawTimeStampText from a string into a JSON object
    timeStamp = json.loads(rawTimeStampText)

    #   Open the config.json file and load the data into a variable
    configFile = open("config.json")
    configData = json.load(configFile)
    configFile.close()

    #   Select random response
    responseLength = len(configData["responses"][responseType])
    randomChoice = random.randint(1,responseLength - 1)

    #   Replace {timeStamp} with the appropriate timestamp text
    timeStampText = ""
    if responseType == "wait":
        timeStampText = f"<t:{math.trunc(timeStamp['userTime'] + timeStamp['timeSpan'])}:R>"
    else:
        timeStampText = f"<t:{math.trunc(time.time() + timeStamp['timeSpan'])}:R>"
    return configData["responses"][responseType][str(randomChoice)].replace("{timeStamp}", (timeStampText))

def getRandomResponse(responseType):
    """
    Function (overload, so same as above) to get a random response from the config.json file without timestamp text.
    """
    configFile = open("config.json")
    configData = json.load(configFile)
    configFile.close()
    responseLength = len(configData["responses"][responseType])
    randomChoice = random.randint(1,responseLength - 1)
    return configData["responses"][responseType][str(randomChoice)]

def getRandomWarpLocation():
    """
    Function to get a random warp location from the config.json file.
    """
    configFile = open("config.json")
    configData = json.load(configFile)
    configFile.close()
    responseLength = len(configData["warp_locations"])
    randomChoice = random.randint(1, responseLength - 1)
    return configData["warp_locations"][randomChoice]

def getSettings():
    """
    Function to read settings from config.json
    """
    file = open("config.json")
    configData = json.load(file)
    file.close()
    return configData["settings"]

def getRollHistory(userID):
    """
    Function to get the roll history of a user from the warpJournal.json file
    """
    file = open("warpJournal.json")
    data = json.load(file)
    file.close()
    for entry in data["warpHistory"]:
        if entry["id"] == userID:
            if "roll_history" not in entry:
                return []
            else:
                return entry["roll_history"]
    return None

def getUserWinSum(userID):
    """
    Function to get the sum of all wins of a user from the warpJournal.json file
    """
    wins = 0
    for roll in getRollHistory(userID):
        if roll["warp_result"] == "win":
            wins = wins + 1
    return wins

def convert_seconds(total_seconds):
    """
    Convert a number of seconds into hours, minutes, and seconds.

    :param total_seconds: int, The total number of seconds
    :return: tuple, A tuple containing hours, minutes, and seconds
    """

    # Calculate hours
    hours = total_seconds // 3600

    # Calculate the remaining seconds after the hours are accounted for
    remaining_seconds = total_seconds % 3600

    # Calculate minutes
    minutes = remaining_seconds // 60

    # Calculate the remaining seconds after the minutes are accounted for
    seconds = remaining_seconds % 60

    return hours, minutes, seconds
#endregion

#region Events

@client.event
async def on_ready():
    """
    Event function that is called when the bot has connected to Discord
    """
    await tree.sync()
    print(f'{client.user} has connected to Discord!')
#endregion

#region Slash Commands
@tree.command(name = getSettings()["log_command_name"], description = getSettings()["log_command_description"])
async def warpLog_command(interaction):
    """
    Slash command function for the warpLog command. Shows the user's lottery history.
    """
    userID = interaction.user.id
    history = getRollHistory(userID)
    wins = 0 if len(history) == 0 else getUserWinSum(userID)
    cooldownHours, cooldownMinutes, cooldownSeconds = convert_seconds(getLowestTimeSpan(interaction.user.roles))
    cooldownString = f"{cooldownHours} hours, {cooldownMinutes} minutes, and {cooldownSeconds} seconds"

    embedVar = discord.Embed(title=f":rocket: Warp Log", description="----------------------------", color=0x00ff00)
    embedVar.add_field(name=f":chart_with_upwards_trend: Total Warps: ```{len(history)}```", value="" , inline=False)

    if len(history) > 0:
        latestWarp = history[len(history) - 1]

        embedVar.add_field(name=f":white_check_mark: Wins: ```{0 if wins == None else wins}```", value="", inline=False)
        embedVar.add_field(name=f":hourglass: Cooldown ```{cooldownString}```", value="", inline=False)
        embedVar.add_field(name=f"\n", value="", inline=False)
        embedVar.add_field(name=f"\nLatest Warp", value="----------------------------", inline=False)
        if "date" in latestWarp:
            latestWarpDate = datetime.strptime(latestWarp["date"] + " " + latestWarp["time_rolled"], "%m-%d-%Y %H:%M:%S")
            embedVar.add_field(name=f":calendar_spiral: Date: ```{calendar.month_name[latestWarpDate.month]} {latestWarpDate.day}, {latestWarpDate.year}```", value="" , inline=False)
            embedVar.add_field(name=f":clock: Time: <t:{int(time.mktime(latestWarpDate.timetuple()))}:R>", value="" , inline=False)
        if "location" in latestWarp:
            latestWarpLocation = latestWarp["location"]
            embedVar.add_field(name=f":round_pushpin: Location: ```{latestWarpLocation}```", value="" , inline=False)
        if "warp_result" in latestWarp:
            latestWarpResult = "Failure" if latestWarp["warp_result"] == "lose" else "Success"
            embedVar.add_field(name=f":trophy: Result: ```{latestWarpResult}```", value="" , inline=False)

    embedVar.set_thumbnail(url=interaction.user.display_avatar)
    await interaction.response.send_message(embed=embedVar)

@tree.command(name = getSettings()["command_name"], description = getSettings()["command_description"])
async def warp_command(interaction):
    """
    Slash command function for the warp command
    """
    # Get time span and check if user has access
    timeSpan = getFirstAvailableTimespan(interaction.user.roles)
    hasAccess = isAccessible(interaction.user.roles)

    #   If user does not have access, send a message saying so
    if not hasAccess:
        print(f"User {interaction.user.id} prompted permission response.")
        await interaction.response.send_message(f"<@{interaction.user.id}> - {getRandomResponse('permission')}", ephemeral = True, delete_after = 15)
    else:
        isReturningUser = False
        isWithinHour = False

        #   Open the warpJournal.json file and load the data into a variable
        file = open("warpJournal.json")
        data = json.load(file)
        file.close()
        indexOfExistingUser = 0

        #   Loop through the warpJournal.json file and check if the user has warped within the last hour
        #   Also check if the user has warped before
        for entry in data["warpHistory"]:
            userID = entry["id"]
            userTime = entry["time"]
            if userID == interaction.user.id:
                isReturningUser = True
                #   If the user has already warped within their timeSpan, send a message saying so
                if time.time() - userTime < timeSpan:
                    print(f"User {interaction.user.id} prompted wait response.")
                    timeStampJSON = "{\"userTime\": " + f"{userTime}" + ", \"timeSpan\": " + f"{timeSpan}" + "}"
                    await interaction.response.send_message(f"<@{interaction.user.id}> - {getRandomResponseTimestamp('wait', timeStampJSON)}", ephemeral = True, delete_after = 15)
                    isWithinHour = True
                    break
                else:
                    break
            indexOfExistingUser += 1

        #   If the user has not warped within the last hour, roll the dice and send a response
        if not isWithinHour:
            currentTime = time.time()
            roll = random.randint(0, getSettings()["odds"])

            if(roll == 1):
                print(f"User {interaction.user.id} prompted win response.")
                timeStampJSON = "{\"userTime\": " + f"{currentTime}" + ", \"timeSpan\": " + f"{timeSpan}" + "}"
                await interaction.response.send_message(f"<@{interaction.user.id}> - {getRandomResponseTimestamp('win', timeStampJSON)}")
            
            else:
                print(f"User {interaction.user.id} prompted lose response.")
                timeStampJSON = "{\"userTime\": " + f"{currentTime}" + ", \"timeSpan\": " + f"{timeSpan}" + "}"
                await interaction.response.send_message(f"<@{interaction.user.id}> - {getRandomResponseTimestamp('lose', timeStampJSON)}")
            """ OLD CODE, BUT KEEPING FOR TESTING / REFERENCE
            # Define function to write dictionary data into a json format
            def writeToWarpJournal(file_data, tempDict):
                if isReturningUser:
                    current_times_warped = file_data["warpHistory"][indexOfExistingUser].get("times_rolled", 0)
                    file_data["warpHistory"][indexOfExistingUser].update({"time": time.time(), 
                                                                          "times_rolled": current_times_warped + 1, 
                                                                          "warp_result": "win" if roll == 1 else "lose",
                                                                          "date": time.strftime("%m-%d-%Y", time.localtime(currentTime)),
                                                                          "time_rolled": time.strftime("%H:%M:%S", time.localtime(currentTime))})
                else:
                    file_data["warpHistory"].append(tempDict)
                with open("warpJournal.json", "w") as file:  # write file
                    json.dump(file_data, file, indent = 4)

            # Create a dictionary to insert into the json file
            tempDict = {
                "id": interaction.user.id,
                "time": currentTime,
                "name": interaction.user.name,
                "discriminator": interaction.user.discriminator,
                "date": time.strftime("%m-%d-%Y", time.localtime(currentTime)),
                "time_rolled": time.strftime("%H:%M:%S", time.localtime(currentTime)),
                "warp_result": "win" if roll == 1 else "lose",
                "times_rolled": 1
            }
            """
            # Define function to write dictionary data into a json format
            def writeToWarpJournal(file_data, tempDict):
                if isReturningUser:
                    file_data["warpHistory"][indexOfExistingUser].update({"time": time.time()})
                    if "roll_history" in file_data["warpHistory"][indexOfExistingUser]:
                        file_data["warpHistory"][indexOfExistingUser]["roll_history"].append({"date": time.strftime("%m-%d-%Y", time.localtime(currentTime)),
                                                                                                "time_rolled": time.strftime("%H:%M:%S", time.localtime(currentTime)),
                                                                                                "warp_result": "win" if roll == 1 else "lose",
                                                                                                "location": getRandomWarpLocation()["name"]
                                                                                            })
                    else:
                        file_data["warpHistory"][indexOfExistingUser].update({"roll_history": [
                                {
                                    "date": time.strftime("%m-%d-%Y", time.localtime(currentTime)),
                                    "time_rolled": time.strftime("%H:%M:%S", time.localtime(currentTime)),
                                    "warp_result": "win" if roll == 1 else "lose",
                                    "location": getRandomWarpLocation()["name"]
                                }
                            ]
                        })
                        if "date" in file_data["warpHistory"][indexOfExistingUser]:
                            del file_data["warpHistory"][indexOfExistingUser]["date"]
                        if "time_rolled" in file_data["warpHistory"][indexOfExistingUser]:
                            del file_data["warpHistory"][indexOfExistingUser]["time_rolled"]
                        if "warp_result" in file_data["warpHistory"][indexOfExistingUser]:
                            del file_data["warpHistory"][indexOfExistingUser]["warp_result"]
                        if "times_rolled" in file_data["warpHistory"][indexOfExistingUser]:
                            del file_data["warpHistory"][indexOfExistingUser]["times_rolled"]
                else:
                    file_data["warpHistory"].append(tempDict)
                with open("warpJournal.json", "w") as file:  # write file
                    json.dump(file_data, file, indent = 4)

            # Create a dictionary to insert into the json file
            tempDict = {
                "id": interaction.user.id,
                "time": currentTime,
                "name": interaction.user.name,
                "discriminator": interaction.user.discriminator,
                "roll_history": [
                    {
                        "date": time.strftime("%m-%d-%Y", time.localtime(currentTime)),
                        "time_rolled": time.strftime("%H:%M:%S", time.localtime(currentTime)),
                        "warp_result": "win" if roll == 1 else "lose",
                        "location": getRandomWarpLocation()["name"]
                    }
                ]
            }
            writeToWarpJournal(data, tempDict)
        file.close()
#endregion

client.run(TOKEN)