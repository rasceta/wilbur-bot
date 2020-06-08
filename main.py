import discord
import os
from tinydb import TinyDB, Query
from discord.ext import commands

client = commands.Bot('!wilbur ')
TOKEN = os.environ.get('WILBUR_TOKEN')

client.remove_command("help")       # Remove the default help command

async def get_db(filename):
    return TinyDB(filename, indent=4, separators=(',', ': '))

async def check_referral_rank(db,n_people,referral_rank,message,member):
    # Rank Up
    if (n_people >= 20) and (referral_rank != "Evangelist"): # If referrers count is 20 or more and rank is not Evangelist
        try: # try to get role and removes it if there is existing role
            role_old = discord.utils.get(message.guild.roles, name=referral_rank)
            await member.remove_roles(role_old)
        except:
            pass
        role_new = discord.utils.get(message.guild.roles, name="Evangelist")
        db.update({"referral_rank":"Evangelist"}, Query().member_id == member.id)
        await member.add_roles(role_new)
        await message.channel.send(f"Roger! <@{str(member.id)}> is an Evangelist. To check your referral info, use `.wilbur check` command.")
    elif (n_people >= 15) and (n_people < 20) and (referral_rank != "Believer"): # If referrers count is in between 15 and 19 and rank is not Believer
        try: # try to get role and removes it if there is existing role
            role_old = discord.utils.get(message.guild.roles, name=referral_rank)
            await member.remove_roles(role_old)
        except:
            pass
        role_new = discord.utils.get(message.guild.roles, name="Believer")
        db.update({"referral_rank":"Believer"}, Query().member_id == member.id)
        await member.add_roles(role_new)
        if referral_rank == "Evangelist":
            await message.channel.send(f"<@{str(member.id)}>'s referred friends decreased to {n_people}. Your rank is now down to Believer! Check your referral info with `!wilbur info`")
        else:
            await message.channel.send(f"Roger! <@{str(member.id)}> is a Believer. To check your referral info, use `!wilbur info` command.")
    elif (n_people >= 5) and (n_people < 15) and (referral_rank != "Samaritan"): # If referrers count is in between 5 and 14 and rank is not Samaritan
        try: # try to get role and removes it if there is existing role
            role_old = discord.utils.get(message.guild.roles, name=referral_rank)
            await member.remove_roles(role_old)
        except:
            pass
        role_new = discord.utils.get(message.guild.roles, name="Samaritan")
        db.update({"referral_rank":"Samaritan"}, Query().member_id == member.id)
        await member.add_roles(role_new)
        if referral_rank in ["Believer","Evangelist"]:
            await message.channel.send(f"Roger! <@{str(member.id)}>'s referred friends decreased to {n_people}. Your rank is now Samaritan! Check your referral info with `!wilbur info`")
        else:
            await message.channel.send(f"Roger! <@{str(member.id)}> is a Samaritan. To check your referral information, use `!wilbur info` command.")
    elif (n_people < 5) and (referral_rank != "Unranked"): # If referrer count is below 5 and rank is not Unranked
        try: # try to get role and removes it if there is existing role
            role_old = discord.utils.get(message.guild.roles, name=referral_rank)
            await member.remove_roles(role_old)
        except:
            pass
        db.update({"referral_rank":"Unranked"}, Query().member_id == member.id)
        if referral_rank in ["Samaritan","Believer","Evangelist"]:
            await message.channel.send(f"Roger! <@{str(member.id)}> is now Unranked. To check your referral information, use `!wilbur info` command.")

@client.event
async def on_ready():
    print("Wilbur bot is ready!")
    await client.change_presence(activity = discord.Activity(name = "joins", type = 2))

@client.event
async def on_guild_join(guild):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == guild.id)
    if len(server_row) == 0:
        DB_CONFIG.insert({'server_id' : guild.id, 'server_name': guild.name,'prefix': '.', 'referral_channel_id':'' ,'channels_aliases':{}})

@client.event
async def on_member_remove(member):
    DB_CHECK = await get_db('check_referral.json')
    DB_REFERRAL = await get_db('referral.json')
    Check = Query()
    Referral = Query()
    referrer_id = member.id
    referrer_name = member.name
    check_row = DB_CHECK.search(Check.referrer_id == referrer_id)

    if (len(check_row) == 1):
        member_id = check_row[0]["member_id"]
        member_name = check_row[0]["member_name"]
        referral_row = DB_REFERRAL.search(Referral.member_id == member_id)
        list_referrer_id = referral_row[0]["list_referrer_id"]
        list_referrer_name = referral_row[0]["list_referrer_name"]
        list_referrer_id.remove(referrer_id)
        list_referrer_name.remove(referrer_name)
        DB_CHECK.remove(Check.referrer_id == referrer_id)
        DB_REFERRAL.update({"list_referrer_id":list_referrer_id, "list_referrer_name":list_referrer_name, "referrer_count":len(list_referrer_id)}, Check.member_id == member_id)
        print(f"Referrer {referrer_name} has been removed from {member_name} referral")

@client.event
async def on_message(message):
    member = message.author
    Member = Query()
    DB_REFERRAL = await get_db('referral.json')

    try: 
        row = DB_REFERRAL.search(Member.member_id == member.id)[0]
        referrer_count = row["referrer_count"]
        referral_rank = row["referral_rank"]
        await check_referral_rank(db=DB_REFERRAL,n_people=referrer_count,referral_rank=referral_rank,message=message,member=member)
    except:
        pass

    await client.process_commands(message)

# ---------------------- help command ---------------------- #

@commands.has_permissions(administrator=True)
@client.command('help')
async def help(ctx):
    embed = discord.Embed(title="**Wilbur Command List**",
                        description="All Wilbur's usable commands. You just need to type !wilbur command to see how it works.",
                        color=discord.Color.blue()
                        )
    embed.add_field(name="1. Check referral information (referrals count, referral rank, etc.)", value="!wilbur info")
    embed.add_field(name="2. Check my invitation links info (if You made some)", value="!wilbur invites")
    embed.add_field(name="3. Give referral to the person who invited you to this server", value="!wilbur referral")
    embed.add_field(name="4. Set current channel as referral channel", value="!wilbur set_referral_channel")
    embed.add_field(name="5. Get where the referral channel is", value="!wilbur referral_channel")
    embed.add_field(name="6. Get all channels aliases", value="!wilbur channels_aliases")
    embed.add_field(name="7. Set current channel's alias", value="!wilbur set_channel [alias]")
    embed.add_field(name="8. Get channel for alias", value="!wilbur get_channel [alias]")
    embed.add_field(name="9. Delete channel alias", value="!wilbur delete_channel [alias]")
    embed.add_field(name="10. Send message using wilbur to alias channel", value="!wilbur send_channel [alias] [message]")
    await ctx.send(embed=embed)

@help.error
async def help_error(ctx,error):
    embed = discord.Embed(title="**Wilbur Command List**",
                        description="All Wilbur's usable commands. You just need to type !wilbur command to see how it works.",
                        color=discord.Color.blue()
                        )
    embed.add_field(name="1. Check referral information (referrals count, referral rank, etc.)", value="!wilbur info")
    embed.add_field(name="2. Check my invitation links info (if You made some)", value="!wilbur invites")
    embed.add_field(name="3. Give referral to the person who invited you to this server", value="!wilbur referral")
    await ctx.send(embed=embed)

# --------------------- End help command -------------------- #

# -------------- set and get referral channel -------------- #

@commands.has_permissions(administrator=True)
@client.command('set_referral_channel')
async def set_referral_channel(ctx):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    if len(server_row) == 1:
        DB_CONFIG.update({'referral_channel_id':ctx.channel.id},Server.server_id == ctx.guild.id)
    else:
        DB_CONFIG.insert({'server_id' : ctx.guild.id, 'server_name': ctx.guild.name,'prefix': '.', 'referral_channel_id':ctx.channel.id, 'channels_aliases':{}})

@commands.has_permissions(administrator=True)
@client.command('referral_channel')
async def referral_channel(ctx):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    if len(server_row) == 1 and server_row[0]["referral_channel_id"] != "":
        channel = client.get_channel(server_row[0]["referral_channel_id"])
        await ctx.send(f"Roger! Your server's referral channel is {channel.mention}")
    else:
        await ctx.send("Roger! You haven't set a referral channel. Please type `!wilbur set_referral_channel` in a channel to make it into referral channel")

# -------- End set and get referral channel command -------- #

# --------- referral command to refers to @member ---------- #

@commands.has_role('Members')
@client.command('referral')
async def referral(ctx, member : discord.User):
    DB_REFERRAL = await get_db('referral.json')
    DB_CHECK = await get_db('check_referral.json')
    DB_CONFIG = await get_db('config.json')

    referrer = ctx.author
    Member = Query()

    referral_row = DB_REFERRAL.search(Member.member_id == member.id)
    check_row = DB_CHECK.search(Member.referrer_id == referrer.id)
    config_row = DB_CONFIG.search(Query().referral_channel_id == ctx.channel.id)

    referral_channel_id = config_row[0]["referral_channel_id"]

    if (ctx.channel.id == referral_channel_id) and (member.id != referrer.id): 
        if (len(referral_row) == 1) and (len(check_row) == 0):
            print(f"Member {member} already exist in referral.json. {referrer} has referred to {member}")
            list_referrer_id = referral_row[0]["list_referrer_id"]
            list_referrer_name = referral_row[0]["list_referrer_name"]
            if (referrer.id not in list_referrer_id):
                list_referrer_id.append(referrer.id)
                list_referrer_name.append(referrer.name)
                DB_REFERRAL.update({"list_referrer_id":list_referrer_id}, Member.member_id == member.id)
                DB_REFERRAL.update({"list_referrer_name":list_referrer_name}, Member.member_id == member.id)
                DB_REFERRAL.update({'referrer_count':len(set(list_referrer_id))}, Member.member_id == member.id)
                DB_CHECK.insert(dict(referrer_id=referrer.id, referrer_name=referrer.name, member_id=member.id, member_name=member.name))
                
        elif (len(referral_row) == 0) and (len(check_row) == 0):
            print(f"Member {member} does not exist yet in referral.json. {referrer} has referred to {member}")
            referral_rank = "Unranked"
            referrer_count = 1
            DB_REFERRAL.insert(dict(member_id=member.id,member_name=member.name,referral_rank=referral_rank,list_referrer_id=[referrer.id],
                                        list_referrer_name=[referrer.name],referrer_count=referrer_count))
            DB_CHECK.insert(dict(referrer_id=referrer.id, referrer_name=referrer.name, member_id=member.id, member_name=member.name))
    elif (ctx.channel.id != referral_channel_id):
        await ctx.send("Roger! You should use this command on referral channel. To get referral channel, type `!wilbur referral_channel` command")

@referral.error
async def referral_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("```You can only use this command on referral channel (type !wilbur referral_channel to get referral channel). Example of proper usage:\n\n!wilbur referral @Username```")

# ------------------ End referral command ------------------ #

# -------- invites command to show invitation links -------- #

@client.command('invites')
async def invites(ctx):
    guild = client.get_guild(ctx.guild.id)
    invites = await guild.invites()
    embed = discord.Embed(title="My Invitation Links",
                            description="Information about my Invitation Links",
                            color=discord.Color.blue()
                            )
    for i in invites:
        if i.inviter.id == ctx.author.id:
            embed.add_field(name="Link", value=i, inline=True)
            embed.add_field(name="Creator", value=i.inviter, inline=True)
            embed.add_field(name="Uses", value=i.uses, inline=True)
            embed.add_field(name="Expire time (days)", value=int(i.max_age/86400), inline=False)
    
    await ctx.send(embed=embed)

# ------------------ End invites command ------------------- #

# ----------- Info command to show referral info ------------ #

@client.command('info')
async def info(ctx):
    DB_REFERRAL = await get_db('referral.json')

    try:
        referrer_row = DB_REFERRAL.search(Query().member_id == ctx.author.id)[0]
        embed = discord.Embed(title="Referral Information",
                            description=f"This is your referral info. If you want to check your benefits, use '!judy check' command in #❄-check-cooldown channel",
                            color=discord.Color.blue()
                            )
        embed.add_field(name="Member Name", value=referrer_row["member_name"], inline=True)
        embed.add_field(name="Referral Rank", value=referrer_row["referral_rank"], inline=True)
        embed.add_field(name="Referrals Count", value=referrer_row["referrer_count"], inline=True)
        await ctx.send(embed=embed)
    except:
        await ctx.send(f"```You don't have any referral information. Ask your invited friends to refer to you by typing '!wilbur referral @[Your Username]' command on referral channel (type !wilbur referral_channel to get referral channel)```")

# --------------------- End Info command --------------------- #

# ----------------------- guide command ---------------------- #

@client.command('guide')
async def guide(ctx):
    response = '''
    Hello, I am Wilbur. Your referral partner.

    I am here to help you to get the number of how many people referred to you. In order to refer to someone you need to use `!wilbur referral @Member` on referral channel.
    If you don't know where the referral channel is, you can use `!wilbur referral_channel` command. Here is how I work:

    1. You have to be in referral channel to use `!wilbur referral @Member` command
    2. Once you typed that, the member you mentioned gains 1 number of referrals count
    3. You can only use `!wilbur referral @Member` command **once**. So, use it wisely to refer to your friend who invited you.
    4. If you want to check your referral info, type `!wilbur info`

    I am looking forward to work with you guys. Please use my commands correctly. If you want to know what commands are available, type `!wilbur help`.
    Thank you guys! You are Awesome!
    '''
    ctx.send(response)

# -------------------- End guide command --------------------- #

# ----- Set, Get, and Delete custom alias for a channel ------ #

@commands.has_permissions(administrator=True)
@client.command('channels_aliases')
async def channels_aliases(ctx):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    channels_aliases = list(server_row[0]["channels_aliases"].keys())
    await ctx.send(f'```Your custom channels aliases are : {channels_aliases}. You can find them by typing .get_channel [channel alias]```')

@commands.has_permissions(administrator=True)
@client.command('set_channel')
async def set_channel(ctx, alias):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    current_aliases = server_row[0]["channels_aliases"]
    new_alias = {alias:ctx.channel.id}
    DB_CONFIG.update({'channels_aliases':{**current_aliases, **new_alias}},Server.server_id == ctx.guild.id)
    await ctx.send(f'```You have set this channel as {alias} channel```')

@commands.has_permissions(administrator=True)
@client.command('delete_channel')
async def delete_channel(ctx, alias):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    current_aliases = server_row[0]["channels_aliases"]
    if alias in current_aliases.keys():
        del current_aliases[alias]
        DB_CONFIG.update({"channels_aliases":current_aliases}, Server.server_id == ctx.guild.id)
        await ctx.send(f'```You are no longer have {alias} channel now```')
    else:
        await ctx.send(f"```You haven't set a channel as {alias} channel```")

@commands.has_permissions(administrator=True)
@client.command('get_channel')
async def get_channel(ctx, alias):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    current_aliases = server_row[0]["channels_aliases"]

    if alias in current_aliases:
        channel = client.get_channel(current_aliases[alias])
        await ctx.send(f'{channel.mention} is your {alias} channel')
    else:
        await ctx.send(f"```You haven't set a channel as {alias} channel```")

@commands.has_permissions(administrator=True)
@client.command('send_channel')
async def send_channel(ctx, alias, *, message):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    current_aliases = server_row[0]["channels_aliases"]
    try: 
        channel_id = current_aliases[alias]
        if (channel_id != '') or (channel_id is not None):
            channel = client.get_channel(channel_id)
            await channel.send(message)
        else:
            response = f"```Key not found in json for {alias} channel```"
            await ctx.send(response)
    except:
        response = f"```You haven't set a channel as {alias} channel. Please enter a channel and type !wilbur set_channel {alias}```"
        await ctx.send(response)
    
# ---------------- End custom alias command ----------------- #

client.run(TOKEN)