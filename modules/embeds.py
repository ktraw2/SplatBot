import discord
import config
import math

help_embed_fields = {
    "lobby_commands":
        {"title": "Lobby Commands",
         "body": "`s!lobby` - display the currently active lobby, if there is one\n"
                 "`s!lobby start [optional:Lobby Name] [optional:Lobby Start Time] [optional:Number of Players]` - "
                    "create a new lobby, can be customized with the optional arguments. Naming the lobby something with "
                    "\"league\" in the name will also embed league battle information into the lobby for the lobby "
                    "start time.\n"
                 "`s!lobby join` - join the currently active lobby\n"
                 "`s!lobby leave` - leave the currently active lobby\n"
                 "`s!lobby delete` - delete the current lobby\n"
                 "`s!lobby edit [players|name|time] [New Value]` - "
                    "change the number of players, lobby name, or lobby start time"},
    "schedule_commands":
        {"title": "Schedule Commands",
         "body": "`s!schedule [regular|ranked|league] [optional:Time]` - get the scheduled mode and maps for the given"
                    "battle type. If no time is given, the current rotation is sent."},
    "misc_commands":
        {"title": "Misc. Commands",
         "body": "`s!help` - view the help for SplatBot"},
    "command_syntax":
        {"title": "Command Syntax",
         "body": "Commands are formatted like this: `s!command [argument]`. "
                 "Some commands have more than one argument, in which case arguments are separated by a space. "
                 "You *do not* type the brackets around the command argument.\n"
                 "**Examples:**\n"
                 "1. `s!lobby create \"Weekly 3v3\" 10PM 6`\n"
                 "2. `s!schedule regular`"}
}


def add_list_embed_fields(output_string, embed, header, cutoff_mode=False):
    if len(output_string) <= 1024:
        embed.add_field(name=header, value=output_string)
    else:
        sections = []
        num_sections = math.ceil(len(output_string) / 1024)
        index_of_first_newline = 0
        index_of_last_newline = 0
        for i in range(0, num_sections):
            n = index_of_first_newline
            for c in output_string[index_of_first_newline:index_of_first_newline + 1024]:
                if c == '\n' or cutoff_mode:
                    index_of_last_newline = n
                n += 1
            sections.append(output_string[index_of_first_newline:index_of_last_newline + 1])
            index_of_first_newline = index_of_last_newline
        continued_string = ""
        for section in sections:
            embed.add_field(name=header + continued_string, value=section)
            continued_string = " (Continued)"


def generate_base_help_embed(bot):
    help_embed = discord.Embed(title=bot.user.name + " Help", color=config.embed_color)
    help_embed.set_thumbnail(
        url=bot.user.avatar_url)
    help_embed.set_footer(text="Developed by ktraw2#9962 and AdamWang#1770")
    return help_embed


def add_help_embed_field(help_embed, key):
    help_embed.add_field(name=help_embed_fields[key]["title"], value=help_embed_fields[key]["body"])


def add_help_embed_footer_links(help_embed, bot):
    help_embed.add_field(name=":globe_with_meridians: " + bot.user.name + " Website",
                         value="Visit " + bot.user.name + " on the World Wide Web at "
                                                          "https://ktraw2.github.io/SplatQueues")
    help_embed.add_field(name="<:discord:545143558789791755> " + bot.user.name + " Discord",
                         value="Join the official " + bot.user.name + " Discord at https://discord.gg/A2aWm9 "
                                                                      "for information, support, or just to have a chat!")
    help_embed.add_field(name="<:SplatBot:548052186337116164> Bring " + bot.user.name + " to Your Discord",
                         value="[Click here](https://discordapp.com/oauth2/authorize?"
                               "client_id=545107229842472971&scope=bot&permissions=16384) "
                               "to invite " + bot.user.name + " to your own Discord server")
    help_embed.add_field(name=":arrow_up: Support " + bot.user.name,
                         value="Support " + bot.user.name + " by upvoting it "
                                                            "[here](https://google.com)!")
