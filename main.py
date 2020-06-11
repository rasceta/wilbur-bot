import discord
import os
from tinydb import TinyDB, Query
from discord.ext import commands

client = commands.Bot('!wilbur ')
BOT_PREFIX = client.command_prefix
TOKEN = os.environ.get('WILBUR_TOKEN')

client.remove_command("help")       # Remove the default help command

async def get_db(filename):
    return TinyDB(filename, indent=4, separators=(',', ': '))

async def check_referral_rank(db,n_people,referral_rank,message,member):
    # Rank Up
    if (n_people >= 20) and (referral_rank != "Host"): # If referrers count is 20 or more and rank is not Host
        try: # try to get role and removes it if there is existing role
            role_old = discord.utils.get(message.guild.roles, name=referral_rank)
            await member.remove_roles(role_old)
        except:
            pass
        role_new = discord.utils.get(message.guild.roles, name="Host")
        db.update({"referral_rank":"Host"}, Query().member_id == member.id)
        await member.add_roles(role_new)
        await message.channel.send(f"Roger! <@{str(member.id)}> is a Host. To check your referral info, use `{BOT_PREFIX}check` command.")
    elif (n_people >= 15) and (n_people < 20) and (referral_rank != "Recruiter"): # If referrers count is in between 15 and 19 and rank is not Recruiter
        try: # try to get role and removes it if there is existing role
            role_old = discord.utils.get(message.guild.roles, name=referral_rank)
            await member.remove_roles(role_old)
        except:
            pass
        role_new = discord.utils.get(message.guild.roles, name="Recruiter")
        db.update({"referral_rank":"Recruiter"}, Query().member_id == member.id)
        await member.add_roles(role_new)
        if referral_rank == "Host":
            await message.channel.send(f"<@{str(member.id)}>'s referred friends decreased to {n_people}. Your rank is now down to Recruiter! Check your referral info with `{BOT_PREFIX}info`")
        else:
            await message.channel.send(f"Roger! <@{str(member.id)}> is a Recruiter. To check your referral info, use `{BOT_PREFIX}info` command.")
    elif (n_people >= 5) and (n_people < 15) and (referral_rank != "Broadcaster"): # If referrers count is in between 5 and 14 and rank is not Broadcaster
        try: # try to get role and removes it if there is existing role
            role_old = discord.utils.get(message.guild.roles, name=referral_rank)
            await member.remove_roles(role_old)
        except:
            pass
        role_new = discord.utils.get(message.guild.roles, name="Broadcaster")
        db.update({"referral_rank":"Broadcaster"}, Query().member_id == member.id)
        await member.add_roles(role_new)
        if referral_rank in ["Recruiter","Host"]:
            await message.channel.send(f"Roger! <@{str(member.id)}>'s referred friends decreased to {n_people}. Your rank is now Broadcaster! Check your referral info with `{BOT_PREFIX}info`")
        else:
            await message.channel.send(f"Roger! <@{str(member.id)}> is a Broadcaster. To check your referral information, use `{BOT_PREFIX}info` command.")
    elif (n_people < 5) and (referral_rank != "Unranked"): # If referrer count is below 5 and rank is not Unranked
        try: # try to get role and removes it if there is existing role
            role_old = discord.utils.get(message.guild.roles, name=referral_rank)
            await member.remove_roles(role_old)
        except:
            pass
        db.update({"referral_rank":"Unranked"}, Query().member_id == member.id)
        if referral_rank in ["Broadcaster","Recruiter","Host"]:
            await message.channel.send(f"Roger! <@{str(member.id)}> is now Unranked. To check your referral information, use `{BOT_PREFIX}info` command.")

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
        DB_CONFIG.insert({'server_id' : guild.id, 'server_name': guild.name, 'referral_channel_id':'' ,'channels_aliases':{}})

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
    if (message.content.startswith('!wilber')):
        await message.channel.send(f"Wilber?! Did you just misspell my name? It's Wilbur! Please use `{BOT_PREFIX}help` to see what I can do")

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
    embed = discord.Embed(title="**Admin's Wilbur Command List**",
                        description=f"All Wilbur's usable commands. You just need to type {BOT_PREFIX}command to see how it works.",
                        color=discord.Color.blue()
                        )
    embed.add_field(name="1. Check referral information (referrals count, referral rank, etc.)", value=f"{BOT_PREFIX}info")
    embed.add_field(name="2. Check my invitation links info (if You made some)", value=f"{BOT_PREFIX}invites")
    embed.add_field(name="3. Give referral to the person who invited you to this server", value=f"{BOT_PREFIX}referral")
    embed.add_field(name="4. Rollback (unrefer) your referral if you referred to anyone", value=f"{BOT_PREFIX}unrefer")
    embed.add_field(name="5. Show Referrals Leaderboard (Top 10)", value=f"{BOT_PREFIX}leaderboard")
    embed.add_field(name="6. Update Members' Referral rank", value=f"{BOT_PREFIX}update_rank")
    embed.add_field(name="7. Set current channel as referral channel", value=f"{BOT_PREFIX}set_referral_channel")
    embed.add_field(name="8. Get where the referral channel is", value=f"{BOT_PREFIX}referral_channel")
    embed.add_field(name="9. Get all channels aliases", value=f"{BOT_PREFIX}channels_aliases")
    embed.add_field(name="10. Set current channel's alias", value=f"{BOT_PREFIX}set_channel [alias]")
    embed.add_field(name="11. Get channel for alias", value=f"{BOT_PREFIX}get_channel [alias]")
    embed.add_field(name="12. Delete channel alias", value=f"{BOT_PREFIX}delete_channel [alias]")
    embed.add_field(name="13. Send message using wilbur to alias channel", value=f"{BOT_PREFIX}send_channel [alias] [message]")
    await ctx.send(embed=embed)

@help.error
async def help_error(ctx,error):
    embed = discord.Embed(title="**Wilbur Command List**",
                        description=f"All Wilbur's usable commands. You just need to type {BOT_PREFIX}command to see how it works.",
                        color=discord.Color.blue()
                        )
    embed.add_field(name="1. Check referral information (referrals count, referral rank, etc.)", value=f"{BOT_PREFIX}info")
    embed.add_field(name="2. Check my invitation links info (if You made some)", value=f"{BOT_PREFIX}invites")
    embed.add_field(name="3. Give referral to the person who invited you to this server", value=f"{BOT_PREFIX}referral")
    embed.add_field(name="4. Rollback (unrefer) your referral if you referred to anyone", value=f"{BOT_PREFIX}unrefer")
    embed.add_field(name="5. Show Referrals Leaderboard (Top 10)", value=f"{BOT_PREFIX}leaderboard")
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
        DB_CONFIG.insert({'server_id' : ctx.guild.id, 'server_name': ctx.guild.name, 'referral_channel_id':ctx.channel.id, 'channels_aliases':{}})

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
        await ctx.send(f"Roger! You haven't set a referral channel. Please type `{BOT_PREFIX}set_referral_channel` in a channel to make it into referral channel")

# -------- End set and get referral channel command -------- #

# --------------- Admin's update rank command -------------- #

@commands.has_permissions(administrator=True)
@client.command('update_rank')
async def update_rank(ctx):
    DB_REFERRAL = await get_db('referral.json')
    Member = Query()

    for row in DB_REFERRAL.all():
        referral_rank = row["referral_rank"]
        member_id = row["member_id"]
        member = discord.utils.find(lambda m: m.id == member_id, ctx.channel.guild.members)
        if referral_rank == "Samaritan":
            DB_REFERRAL.update({"referral_rank": "Broadcaster"},Member.member_id == member_id)
            role = discord.utils.get(ctx.message.guild.roles, name="Broadcaster")
            await member.add_roles(role)
        elif referral_rank == "Believer":
            DB_REFERRAL.update({"referral_rank": "Recruiter"},Member.member_id == member_id)
            role = discord.utils.get(ctx.message.guild.roles, name="Recruiter")
            await member.add_roles(role)
        elif referral_rank == "Evangelist":
            DB_REFERRAL.update({"referral_rank": "Host"},Member.member_id == member_id)
            role = discord.utils.get(ctx.message.guild.roles, name="Host")
            await member.add_roles(role)
        elif referral_rank in ["Broadcaster", "Recruiter", "Host"]:
            role = discord.utils.get(ctx.message.guild.roles, name=referral_rank)
            await member.add_roles(role)

# ------------- End admin's update rank command ------------ #

# --- referral and unrefer command to refers to @member ---- #

@commands.has_role('Members')
@client.command(name='referral',aliases=['refer','r'])
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
                await ctx.message.add_reaction("✅")
        elif (len(referral_row) == 0) and (len(check_row) == 0):
            print(f"Member {member} does not exist yet in referral.json. {referrer} has referred to {member}")
            referral_rank = "Unranked"
            referrer_count = 1
            DB_REFERRAL.insert(dict(member_id=member.id,member_name=member.name,referral_rank=referral_rank,list_referrer_id=[referrer.id],
                                        list_referrer_name=[referrer.name],referrer_count=referrer_count))
            DB_CHECK.insert(dict(referrer_id=referrer.id, referrer_name=referrer.name, member_id=member.id, member_name=member.name))
            await ctx.message.add_reaction("✅")
        elif (len(check_row) == 1):
            await ctx.send(f"Uh Oh! Looks like <@{referrer.id}> already referred to <@{check_row[0]['member_id']}>. You cannot change your referral now.")
            await ctx.message.add_reaction("❌")
    elif (ctx.channel.id != referral_channel_id):
        await ctx.send(f"Roger! You should use this command on referral channel. To get referral channel, type `{BOT_PREFIX}referral_channel` command.")
        await ctx.message.add_reaction("❌")
    elif (member.id == ctx.author.id):
        await ctx.send(f"Uh Oh! You **cannot** refer to yourself. Be thankful to the person who invited you by typing `{BOT_PREFIX}referral @[Your friend]`.")
        await ctx.message.add_reaction("❌")

@referral.error
async def referral_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"```You can only use this command on referral channel (type {BOT_PREFIX}referral_channel to get referral channel). Example of proper usage:\n\n{BOT_PREFIX}referral @Username```")

@commands.has_role('Members')
@client.command('unrefer')
async def unrefer(ctx):
    DB_CHECK = await get_db('check_referral.json')
    DB_REFERRAL = await get_db('referral.json')
    DB_CONFIG = await get_db('config.json')

    Check = Query()
    Referral = Query()
    Config = Query()

    referrer = ctx.author
    referrer_id = referrer.id
    referrer_name = referrer.name
    check_row = DB_CHECK.search(Check.referrer_id == referrer_id)
    config_row = DB_CONFIG.search(Config.server_id == ctx.guild.id)
    referral_channel_id = config_row[0]["referral_channel_id"]

    if (ctx.channel.id == referral_channel_id):
        if (len(check_row) == 1):
            member_id = check_row[0]["member_id"]
            referral_row = DB_REFERRAL.search(Referral.member_id == member_id)
            list_referrer_id = referral_row[0]["list_referrer_id"]
            list_referrer_name = referral_row[0]["list_referrer_name"]
            list_referrer_id.remove(referrer_id)
            list_referrer_name.remove(referrer_name)
            DB_CHECK.remove(Check.referrer_id == referrer_id)
            DB_REFERRAL.update({"list_referrer_id":list_referrer_id, "list_referrer_name":list_referrer_name, "referrer_count":len(list_referrer_id)}, Check.member_id == member_id)
            await ctx.send(f"Roger! <@{referrer_id}> has unreferred <@{member_id}>")
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send(f"Roger! You cannot unrefer when you haven't referred to a Member yet.")
            await ctx.message.add_reaction("❌")

# ------------ End referral and unrefer command ------------ #

# ------------------- leaderboard command ------------------ #

@client.command('leaderboard')
async def leaderboard(ctx):
    DB_REFERRAL = await get_db('referral.json')

    list_all_referrals = [{'Member':m['member_name'], 'Referrals': m['referrer_count'], 'Rank': m['referral_rank']} for m in DB_REFERRAL.all()]
    list_leaderboard = sorted(list_all_referrals, key=lambda k: k['Referrals'], reverse=True)

    response = ""
    if len(list_leaderboard) <= 10:
        for i in range(0,len(list_leaderboard)):
            response =  response + f"#**{i+1}** Member : **{list_leaderboard[i]['Member']}**, Referrals : **{list_leaderboard[i]['Referrals']}**, Rank : **{list_leaderboard[i]['Rank']}** \n"
    else:
        for i in range(0,10):
            response =  response + f"#**{i+1}** Member : **{list_leaderboard[i]['Member']}**, Referrals : **{list_leaderboard[i]['Referrals']}**, Rank : **{list_leaderboard[i]['Rank']}** \n"

    embed = discord.Embed(title="**Referrals Leaderboard (Top 10)**",
                            description=response,
                            color=discord.Color.blue()
                            )
    await ctx.send(embed=embed)

# ----------------- End leaderboard command ---------------- #

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
        await ctx.send(f"```You don't have any referral information. Ask your invited friends to refer to you by typing '{BOT_PREFIX}referral @[Your Username]' command on referral channel (type {BOT_PREFIX}referral_channel to get referral channel)```")

# --------------------- End Info command --------------------- #

# ----------------------- guide command ---------------------- #

@client.command('guide')
async def guide(ctx):
    response = '''
Hello, I am Wilbur. Your referral partner.

I am here to help you to get the number of how many people referred to you. In order to refer to someone you need to use `{0} referral @Member` on referral channel.
If you don't know where the referral channel is, you can use `{0} referral_channel` command. Here is how I work:

1. You have to be in referral channel to use `{0} referral @Member` command
2. Once you typed that, the member you mentioned gains 1 number of referrals count
3. You can only use `{0} referral @Member` command **once**. So, use it wisely to refer to your friend who invited you.
4. If you want to check your referral info, type `{0} info`

I am looking forward to work with you guys. Please use my commands correctly. If you want to know what commands are available, type `{0} help`.

Thank you guys! You are Awesome!
    '''.format(BOT_PREFIX)
    await ctx.send(response)

# -------------------- End guide command --------------------- #

# ----- Set, Get, and Delete custom alias for a channel ------ #

@commands.has_permissions(administrator=True)
@client.command('channels_aliases')
async def channels_aliases(ctx):
    DB_CONFIG = await get_db('config.json')
    Server = Query()
    server_row = DB_CONFIG.search(Server.server_id == ctx.guild.id)
    channels_aliases = list(server_row[0]["channels_aliases"].keys())
    await ctx.send(f'```Your custom channels aliases are : {channels_aliases}. You can find them by typing {BOT_PREFIX}get_channel [channel alias]```')

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
        response = f"```You haven't set a channel as {alias} channel. Please enter a channel and type {BOT_PREFIX}set_channel {alias}```"
        await ctx.send(response)
    
# ---------------- End custom alias command ----------------- #

client.run(TOKEN)