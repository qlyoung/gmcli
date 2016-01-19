import groupy
import re
import emoji
import time
import requests
import yaml
from html.parser import HTMLParser

# default config, overridden by config.yaml
config = {
    'api-key': '',
    'bot-avatar': '',
    'prompt': '~>',
    'greeting': 'gmcli by Quentin Young, version 1.0 -- type /help for help'
}


def main():
    """Loads config and starts client."""
    loadconfig()
    print( config['greeting'] )
    prompt()

def loadconfig():
    """Loads configuration from config.yaml, using defaults for unspecified options."""
    with open('config.yaml') as configfile:
        conf = yaml.load(configfile)
        for key in conf:
            config[key] = conf[key] if conf[key] else config[key]

    log('Loaded config.yaml')

    # can't do much without an api key!
    if not config['api-key'] and not groupy.config.API_KEY:
        log('No API key set', 'e')
        exit()
    
    # config api key overrides ~/.groupy.key
    if config['api-key']:
        with open(config['api-key']) as keyfile:
            groupy.config.API_KEY = keyfile.readline().strip()

def prompt():
    """Prompts for, parses and executes commands."""
    command = input( config['prompt'] )
    # /help
    if re.match('/help.*', command):
        showhelp()
    # /groups
    if re.match('/groups.*', command):
        groups()
    # /users [groupid]
    if re.match('/users.*', command):
        if re.match('/users\s([0-9]+).*', command):
            groupid = re.match('/users\s([0-9]+).*', command).group(1)
            users(groupid)
        else:
            users()
    # /msg <groupid> <message>
    if re.match('/msg\s([0-9]+)(.+)', command):
        match = re.match('/msg\s([0-9]+)(.+)', command)
        groupid = match.group(1).strip()
        message = match.group(2)
        msg(groupid, message)
    # /msgall <message>
    if re.match('/msgall\s(.+)', command):
        match = re.match('/msgall\s(.+)', command)
        message = match.group(1)
        msgall(message)
    # /messages <groupid>
    if re.match('/messages\s([0-9]+).*', command):
        groupid = re.match('/messages\s([0-9]+).*', command).group(1)
        messages(groupid)
    # /like <groupid>
    if re.match('/like\s([0-9]+)\s([0-9]+).*', command):
        match = re.match('/like\s([0-9]+)\s([0-9]+).*', command)
        groupid = match.group(1)
        like(groupid)
    # /botsay <botname> <groupid> <message>
    if re.match('/botsay\s(.+)\s([0-9]+)\s(.+)', command):
        match = re.match('/botsay\s(.+)\s([0-9]+)\s(.+)', command)
        botname = match.group(1)
        groupid = match.group(2)
        message = match.group(3)
        botsay(groupid, botname, message)
    # /readd <groupid>
    if re.match('/readd\s([0-9]+).*', command):
        groupid = re.match('/readd\s([0-9]+).*', command).group(1)
        readd(groupid)
    # /dm <userid> <message>
    if re.match('/dm\s([0-9]+)(.+)', command):
        match = re.match('/dm\s([0-9]+)(.+)', command)
        user_id = match.group(1)
        message = match.group(2)
        dm(user_id, message)
    # /dmspam <userid> <n> [message]
    if re.match('/dmspam\s([0-9]+)\s([0-9]+).*', command):
        match = re.match('/dmspam\s([0-9]+)\s([0-9]+)(.*)', command)
        user_id = match.group(1)
        n = match.group(2)
        message = match.group(3)
        dmspam(user_id, message, n)
    # /spam <groupid> <n> [message]
    if re.match('/spam\s([0-9]+)\s([0-9]+).*', command):
        match = re.match('/spam\s([0-9]+)\s([0-9]+)(.*)', command)
        group_id = match.group(1)
        n = match.group(2)
        message = match.group(3)
        spam(group_id, message, n)

    prompt()

def showhelp():
    """Prints a synopsis of all available commands."""
    print('Available commands:')
    print('  /help -- display help')
    print('  /groups -- list available groups')
    print('  /users -- display all known users')
    print('  /users [group] -- display all users in a group, or all known users if no '
             'group is specified')
    print('  /msg <group> <message> -- send a message to a group')
    print('  /msgall <message> -- send message to all known groups')
    print('  /messages <groupid> -- get recent messages from group')
    print('  /like <groupid> -- like the latest message in <groupid> times')
    print('  /botsay <botname> <groupid> <message> -- send a message from a bot')
    print('  /dm <userid> <message> -- send direct message to user')
    print('  /dmspam <userid> <n> [message] -- send direct message to user, n times. '
             'If no message is specified, a random unicode smiley will be sent.')
    print('  /spam <groupid> <n> [message] -- send message to group, n times. '
             'If no message is specified, a random unicode smiley will be sent.')
    print('  /readd <groupid> -- remove and re-add all users of a group '
             '(except you and the creator)')

def groups():
    """Lists all available groups."""
    groups = groupy.Group.list()
    for group in groups:
        print(group.group_id.rjust(8) + ' | ' + group.name)

def users(groupid=None):
    """
    Lists members of the identified group. If no group id is supplied, all known users
    are listed.
    """
    if groupid is None:
        allmembers = groupy.Member.list()
        for member in allmembers:
            print(member.user_id.rjust(10) + ' | ' + member.nickname)
    else:
        group = findgroup(groupid)
        if group is not None:
            for member in group.members():
                print(member.user_id.rjust(10) + ' | ' + member.nickname)
        else:
            print(groupid + ' -- no such group.')

def msg(groupid, message):
    """Sends a message to the identified group."""
    group = findgroup(groupid)
    if group is not None:
        message = emoji.emojize(message, use_aliases=True)
        group.post(message)

def msgall(message):
    """Sends a message to all known groups."""
    for group in groupy.Group.list():
        message = emoji.emojize(message)
        group.post(message)

def dm(userid, message):
    """Sends a direct message to the identified user."""
    members = groupy.Member.list()
    for member in members:
        if member.user_id == userid:
            member.post(message)

def messages(groupid):
    """
    Lists the first 15 characters of each message in the latest page of messages
    for the identified group.
    """
    group = findgroup(groupid)
    if group is not None:
        messages = group.messages()
        for message in messages:
            if message is not None and message.text is not None:
                print(message.text[:15])

def like(groupid):
    """Likes the last message sent to the identified group."""
    group = findgroup(groupid)
    if group is not None:
        group.messages().newest.like()

def botsay(groupid, botname, message):
    """Sends a message to the identified group from a bot with name botname."""
    group = findgroup(groupid)
    if group is not None:
        bot = groupy.Bot.create(botname, group, config['bot-avatar'])
        bot.post(message)
        bot.destroy()

def dmspam(userid, message=None, n=1):
    """
    Repeatedly DM's the identified user with the given message.
    If the message is empty, a random unicode smiley will be sent.
    """
    if message:
        message = emoji.emojize(message, use_aliases=True)

    for i in range(1, int(n)):
        dm(userid, message if message else randomsmiley())
        time.sleep(2)

def spam(groupid, message=None, n=1):
    """
    Repeatedly messages the identified group with the given message.
    If the message is empty, a random unicode smiley will be sent.
    """
    if message:
        message = emoji.emojize(message, use_aliases=True)

    for i in range(1, int(n)):
        msg(groupid, message if message else randomsmiley())
        time.sleep(2)

def readd(groupid):
    """
    Removes and re-adds all members of the identified group
    except yourself and the creator.
    """
    group = findgroup(groupid)
    members = group.members()
    if group is not None:
        for member in group.members():
            myid = groupy.User.get().user_id
            creatorid = group.creator_user_id
            if (member.user_id != creatorid) and (member.user_id != myid):
                group.remove( member )
        time.sleep(3)
        group.add( *members )

def findgroup(groupid):
    """
    Gets the group object corresponding to the given id, or None if there is
    no such group.
    """
    groups = groupy.Group.list()
    for group in groups:
        if group.group_id == groupid:
            return group

def randomsmiley():
    """Fetches a random unicode smiley from this neat website."""
    h = HTMLParser()
    response = requests.get('http://dominick.p.elu.so/fun/kaomoji/get.php')
    smiley = h.unescape(response.text)
    return smiley

prefixes = {
    'd': '[+]',
    'w': '[!]',
    'e': '[X] ERROR:'
}
def log(message, mode='d'):
    """
    Prints a log message to stdout. Mode defines message prefix.
    Modes: d (debug), w (warning), e (error).
    """
    print(prefixes[mode] + ' ' + message)


main()
