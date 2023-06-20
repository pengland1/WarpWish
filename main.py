import discord, json, random, time, math, os
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

#   Regular Functions
def getLowestTimeSpan():
    file = open("config.json")
    configData = json.load(file)
    file.close()
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

def getRandomResponse(responseType, rawTimeStampText):
    timeStamp = json.loads(rawTimeStampText)
    configFile = open("config.json")
    configData = json.load(configFile)
    configFile.close()
    responseLength = len(configData["responses"][responseType])
    randomChoice = random.randint(1,responseLength - 1)
    timeStampText = ""
    if responseType == "wait":
        timeStampText = f"<t:{math.trunc(timeStamp['userTime'] + timeStamp['timeSpan'])}:R>"
    else:
        timeStampText = f"<t:{math.trunc(time.time() + timeStamp['timeSpan'])}:R>"
        
    return configData["responses"][responseType][str(randomChoice)].replace("{timeStamp}", (timeStampText))

#  Events
@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")

#   Slash Commands
@tree.command(name = "warp", description = "Make a warp wish to the Cosmic Council, and the energies of the universe may grant you a boon.")
async def warp_command(interaction):
    timeSpan = getLowestTimeSpan()
    hasAccess = isAccessible(interaction.user.roles)

    if not hasAccess:
        print(f"User {interaction.user.id} prompted permission response.")
        await interaction.response.send_message(f"<@{interaction.user.id}> - {getRandomResponse('permission')}")
    else:
        isReturningUser = False
        isWithinHour = False
        file = open("warpJournal.json")
        data = json.load(file)
        file.close()
        indexOfExistingUser = 0

        for entry in data["warpHistory"]:
            userID = entry["id"]
            userTime = entry["time"]
            if userID == interaction.user.id:
                isReturningUser = True
                if time.time() - userTime < timeSpan:
                    print(f"User {interaction.user.id} prompted wait response.")
                    timeStampJSON = "{\"userTime\": " + f"{userTime}" + ", \"timeSpan\": " + f"{timeSpan}" + "}"
                    await interaction.response.send_message(f"<@{interaction.user.id}> - {getRandomResponse('wait', timeStampJSON)}")
                    isWithinHour = True
                    break
                else:
                    break
            indexOfExistingUser += 1

        if not isWithinHour:
            currentTime = time.time()
            roll = random.randint(0, 500)

            if(roll == 1):
                print(f"User {interaction.user.id} prompted win response.")
                timeStampJSON = "{\"userTime\": " + f"{currentTime}" + ", \"timeSpan\": " + f"{timeSpan}" + "}"
                await interaction.response.send_message(f"<@{interaction.user.id}> - {getRandomResponse('win', timeStampJSON)}")
                
            else:
                print(f"User {interaction.user.id} prompted lose response.")
                timeStampJSON = "{\"userTime\": " + f"{currentTime}" + ", \"timeSpan\": " + f"{timeSpan}" + "}"
                await interaction.response.send_message(f"<@{interaction.user.id}> - {getRandomResponse('lose', timeStampJSON)}")
                
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