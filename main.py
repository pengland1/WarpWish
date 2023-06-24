import discord, json, random, time, math, os
from discord import app_commands
from dotenv import load_dotenv

#   Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

#   Setting up the Discord Intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)

#   Setting up the command tree for slash commands
tree = app_commands.CommandTree(client)

#   Regular Functions
def getLowestTimeSpan():
    """
    Function to find the lowest time span in the config.json file.
    """
    #   Open the config.json file and load the data into a variable
    file = open("config.json")
    configData = json.load(file)
    file.close()

    #   Loop through the roles in the config.json file and find the lowest time span
    index = 0
    timespan = 0
    for role in configData["roles"]:
        if index == 0:
            timespan = int(role["time_span"])
        if int(role["time_span"]) < timespan:
            timespan = int(role["time_span"])
        index = index + 1
    return timespan

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

def getSettings():
    """
    Function to read settings from config.json
    """
    file = open("config.json")
    configData = json.load(file)
    file.close()
    return configData["settings"]

#  Events
@client.event
async def on_ready():
    """
    Event function that is called when the bot has connected to Discord
    """
    await tree.sync()
    print(f'{client.user} has connected to Discord!')

#   Slash Commands
@tree.command(name = getSettings()["command_name"], description = getSettings()["command_description"])
async def warp_command(interaction):
    """
    Slash command function for the warp command
    """
    # Get time span and check if user has access
    timeSpan = getLowestTimeSpan()
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
            writeToWarpJournal(data, tempDict)
        file.close()
client.run(TOKEN)