import discord
from discord.ext import commands
from discord import app_commands
import requests
import json
import os
from dotenv import load_dotenv


load_dotenv()
intents = discord.Intents.all()
client = commands.Bot(command_prefix="/", intents=intents)


@client.event
async def on_ready():
    print("Bot is ready.")
    try:
        synced = await client.tree.sync()
        print("Synced commands:", synced)
    except Exception as e:
        print("Failed to sync commands:", e)


@client.tree.command(name="item")
async def item(interaction: discord.Interaction, ign: str):
    player = requests.get(
        f"https://api.mojang.com/users/profiles/minecraft/{ign}"
    ).json()

    # If the player doesn't exist return error
    if "errorMessage" in player:
        await interaction.response.send_message(player["errorMessage"])
        return

    # Get the player uuid
    player_uuid = player["id"]
    response = requests.get(f"https://api.slothpixel.me/api/skyblock/profile/{ign}")
    data = response.json()

    # If the player doesn't have a skyblock profile return error
    if data == {}:
        await interaction.response.send_message(
            f"{ign} doesn't have a skyblock profile."
        )
        return

    inventory = data["members"][player_uuid]["inventory"]
    ender_chest = data["members"][player_uuid]["ender_chest"]
    backpacks = data["members"][player_uuid]["backpack"]

    types_of_farming_tools = [
        "PUMPKIN_DICER",
        "PUMPKIN_DICER_2",
        "PUMPKIN_DICER_3",
        "MELON_DICER",
        "MELON_DICER_2",
        "MELON_DICER_3",
        "THEORETICAL_HOE_WHEAT",
        "THEORETICAL_HOE_WHEAT_2",
        "THEORETICAL_HOE_WHEAT_3",
        "THEORETICAL_HOE_POTATO",
        "THEORETICAL_HOE_POTATO_2",
        "THEORETICAL_HOE_POTATO_3",
        "COCO_CHOPPER",
        "CACTUS_KNIFE",
        "THEORETICAL_HOE_WARTS",
        "THEORETICAL_HOE_WARTS_2",
        "THEORETICAL_HOE_WARTS_3",
        "THEORETICAL_HOE_CANE",
        "THEORETICAL_HOE_CANE_2",
        "THEORETICAL_HOE_CANE_3",
        "THEORETICAL_HOE_CARROT",
        "THEORETICAL_HOE_CARROT_2",
        "THEORETICAL_HOE_CARROT_3",
        "FUNGI_CUTTER",
    ]

    farming_tools = []
    best_fortune_tool = {}
    best_cultivating_tool = {}
    best_counter_tool = {}

    # Find all farming tools in inventory
    for item in inventory:
        # Check if attributes exists
        if "attributes" in item:
            if item["attributes"]["id"] in types_of_farming_tools:
                farming_tools.append(item)

    # Find all farming tools in ender chest
    for item in ender_chest:
        # Check if attributes exists
        if "attributes" in item:
            if item["attributes"]["id"] in types_of_farming_tools:
                farming_tools.append(item)

    # Find all farming tools in backpacks
    for bp in backpacks:
        for item in bp:
            # Check if attributes exists
            if "attributes" in item:
                if item["attributes"]["id"] in types_of_farming_tools:
                    farming_tools.append(item)

    if len(farming_tools) == 0:
        await interaction.response.send_message(f"{ign} has no farming tools.")
        return

    # Find the best tool
    for tool in farming_tools:
        # Check if we have a best_cultivating_tool yet
        if best_cultivating_tool:
            if get_cultivating_number(tool) > get_cultivating_number(
                best_cultivating_tool
            ):
                best_cultivating_tool = tool
        else:
            best_cultivating_tool = tool
        if best_counter_tool:
            if get_counter_number(tool) > get_counter_number(best_counter_tool):
                best_counter_tool = tool
        else:
            best_counter_tool = tool
        if best_fortune_tool:
            if get_farming_fortune_number(tool) > get_farming_fortune_number(
                best_fortune_tool
            ):
                best_fortune_tool = tool
        else:
            best_fortune_tool = tool

    # If there is no best_cultivating_tool return string of 'No item with cultivating'
    if not best_cultivating_tool:
        best_cultivating_tool_name = "No item with cultivating"
    else:
        best_cultivating_tool_name = (
            best_cultivating_tool["name"][2:]
            + " : "
            + str(get_cultivating_number(best_cultivating_tool))
        )

    # If there is no best_counter_tool return string of 'No item with counter'
    if not best_counter_tool:
        best_counter_tool_name = "No item with counter"
    else:
        best_counter_tool_name = (
            best_counter_tool["name"][2:]
            + " : "
            + str(get_counter_number(best_counter_tool))
        )

    # If there is no best_fortune_tool return string of 'No item with fortune'
    if not best_fortune_tool:
        best_fortune_tool_name = "No item with fortune"
    else:
        best_fortune_tool_name = (
            best_fortune_tool["name"][2:]
            + " : "
            + str(get_farming_fortune_number(best_fortune_tool))
        )

    await interaction.response.send_message(
        f"{ign}'s best farming tools are:\n"
        + f"Best cultivating tool: {best_cultivating_tool_name}\n"
        + f"Best counter tool: {best_counter_tool_name}\n"
        + f"Best fortune tool: {best_fortune_tool_name}"
    )


def get_cultivating_number(tool):
    # Get the cultivating number
    for line in tool["lore"]:
        if "Cultivating" in line:
            if "§8" not in line:
                return 0
            cultivating_number = line.split("§8")[1]
            cultivating_number = int(cultivating_number.replace(",", ""))
            return cultivating_number

    return 0


def get_counter_number(tool):
    # Get the counter number
    for line in tool["lore"]:
        if "Counter" in line:
            # Split between "§e" and the next space
            counter_number = line.split("§e")[1].split(" ")[0]
            counter_number = int(counter_number.replace(",", ""))
            return counter_number

    return 0


def get_farming_fortune_number(tool):
    # Get the farming fortune number
    if "farming_fortune" in tool["stats"]:
        return tool["stats"]["farming_fortune"]
    else:
        return 0


client.run(os.environ.get("BOT_TOKEN"))
