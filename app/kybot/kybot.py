import socket, glob, sys, re, os, time
import threading
import subprocess
import imp
import lib
#import irc_parser
from log import log

import app.configs.config as config



def send(self, msg):
    msg = msg.replace('\n', ' ').replace("\a", "")
    msg = msg.encode("utf-8") + b"\r\n"
    stripped_msg = msg.decode("utf-8").strip("\n")
    log.debug("(%s) <- %s", self.netname, stripped_msg)
    try:
        self.irc.send(msg)
    except AttributeError:
        log.debug("(%s) Dropping message %r; network isn't connected!", self.netname, stripped_msg)
    
def connect(self):
    self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.irc.connect((self.server, self.port))
    print("({}) Attempting to connect to {}/{} as {}".format(self.netname, self.server, self.port, self.nick))
    print('(%s) Connecting...' % self.netname)
    self.send("PASS {}".format(self.password))
    print('Sending password..')
    self.send("USER {} 0 * :{}".format(self.gecos, self.username))
    print("Sending USER {} 0 * :{}".format(self.gecos, self.username))
    self.send("NICK {}".format(self.nick))
    print("Setting nickname to {}".format(self.nick))
    print('(%s) Connected!' % (self.netname))
    log.debug('(%s) Connected!' % (self.netname))
    
    self.connected = True
    self.verification()
    
def get_data(self):
    try:
        self.buffer += lib.decode(self.irc.recv(4096))
        line = ''
        args = []
        lines = self.buffer.split('\r\n')
        self.buffer = lines[-1]
        for line in lines[0:-1]:  
         
            if ' :' in line:
                (first_args, last_args) = line.split(' :', 1)
                args = first_args.split(' ')
                args.append(last_args)
            else:
                args = line.split(' ')
                
            #print(line)
            #print(args)
    
    except KeyboardInterrupt:
            self.disconnect("Exiting.. (CTRL-C at console)")
            print("Exiting.. (CTRL-C at console)")
    
def verification(self):

    print('Verifying connection...')
    
    self.connecting = True
    
    while self.connecting == True:
    
        try:
            
            #line, args = self.get_data()
            #print("(RECV) "+line) 
            #print(args)
            #print(args)
            #print("LINE: "+line)
            buffer = ''
            buffer += lib.decode(self.irc.recv(4096))
            lines = buffer.split('\r\n')
            buffer = lines[-1]
            for line in lines[0:-1]:  
                print(line)
         
                if ' :' in line:
                    (first_args, last_args) = line.split(' :', 1)
                    args = first_args.split(' ')
                    args.append(last_args)
                else:
                    args = line.split(' ')
                print(args)
                
                if 'PING ' in line:
                    pong = line.split(' :')[1]
                    print('Sending PONG', pong)
                    self.send('PONG ' + pong)
                    
                if args[0].startswith(':'):
                    if args[1] == "376":
                        for chans in self.autojoins:
                            self.join_chan(chans)

                if "are now recognized" in line:
                    for chans in self.autojoins:
                        self.join_chan(chans)

                if ('MODE ' + self.nick) in line or args[1] == "366":
                    self.connecting = False
                    print("Breaking the connection loop..")
                    self.enabled = True
                    self.main()
                    break
            
        except KeyboardInterrupt:
            self.disconnect("Exiting.. (CTRL-C at console)")
            print("Exiting.. (CTRL-C at console)")
    
def reconnect(self, quit=None):
    self.send("QUIT :{}".format("Hold up, need a beer.." if not quit else quit))
    self.irc.close()
    self.connected = False
    self.run()
    
def run(self):
    self.connect()
    self.connected = True
    
    while self.connected:
        try:
            running = True
            
        except Exception:
            running = False 
        except KeyboardInterrupt:
            self.disconnect("Exiting.. (CTRL-C at console)")
            print("Exiting.. (CTRL-C at console)")
        
def disconnect(self, quit=None, terminate=True):
    self.send("QUIT :{}".format("Oh well.. Back to being fingered again! (debugging mode)" if not quit else quit))
    self.connected = False
    self.enabled = False
    self.irc.close()
    if terminate:
        sys.exit(0)
        
    
# EX: add_cmd('<prefix>', '<command>', '[options/reason]' , '[options/reason]')
# EX: add_cmd('!', 'kick', get_channel, 'you were kicked from the channel')
# EX: add_cmd ('!', 'join', [option])

         
def msg_chan(self, chan, msg):
    self.irc.send(bytes('PRIVMSG %s :%s\r\n' % (chan, msg), 'UTF-8'))

def msg_nick(self, nick, msg):
    self.irc.send(bytes('PRIVMSG %s :%s\r\n' % (nick, msg), 'UTF-8'))
    
def send_notice(self, nick, msg):
    self.irc.send(bytes('NOTICE %s :%s\r\n' % (nick, msg), 'UTF-8'))

def join_chan(self, chan):
    self.irc.send(bytes('JOIN %s\r\n' % chan, 'UTF-8'))
    print("Joining %s" % chan)

def part_chan(self, chan, reason=None):
    self.irc.send(bytes('PART %s %s\r\n' % (chan, "Sec.. Need a beer!" if not reason else reason), 'UTF-8'))
    print("Parting %s" % chan)
    
def cycle_chan(self, chan, reason=None):
    self.irc.send(bytes('PART %s %s\r\n' % (chan, "Moment.." if not reason else reason), 'UTF-8'))
    self.irc.send(bytes('JOIN %s\r\n' % chan, 'UTF-8'))
    print("Cycling %s" % chan)

def kick(self, chan, target, message="Goodbye"):
    self.send("KICK {} {} :{}".format(chan, target, message))        
    
def quit(self, msg=None):
    self.irc.send(bytes('QUIT :%s\r\n' % ("Oh well.. Back to being fingered again! (debugging mode)" if not msg else msg), 'UTF-8'))
    print("(Network) Quitting..")
            
def message(self): 
    line = self.main.line()
    if ' :' in line:
        if args[1] != "MODE": 
            message = last_args
        else:
            message = None
        print("Message: "+message)
        return message
            
def main(self):
    print("Launching the main loop..")

    if self.enabled:
    
        while self.connected == True:
        
            try:
            
                buffer = ''
                buffer += lib.decode(self.irc.recv(4096))
                lines = buffer.split('\r\n')
                buffer = lines[-1]
                for line in lines[0:-1]:  
             
                    if ' :' in line:
                        (first_args, last_args) = line.split(' :', 1)
                        args = first_args.split(' ')
                        args.append(last_args)
                    else:
                        args = line.split(' ')
                    
                    if args[0].startswith(':'):
                        if len(args) < 5:
                            self.usernick = args[0]
                            self.usernick = self.usernick.split(':')[1]
                            self.usernick = self.usernick.split('!')[0]
                            #print('Usernick: ' + self.usernick)
                        else:
                            self.usernick = None
                              
                    if args[0].startswith(':'):
                        if len(args) < 5: 
                            self.userident = args[0]
                            if '!' in args[0]:
                                self.userident = self.userident.split('!')[1]
                                self.userident = self.userident.split('@')[0]
                                #print("Userident:" + self.userident)
                            else:
                                self.userident = None
                                                                    
                    if args[0].startswith(':'):
                        if len(args) < 5: 
                            self.userhost = args[0]
                            if '@' in args[0]:
                                self.userhost = self.userhost.split('@')[1]
                                #print("userhost:" + self.userhost)
                            else:
                                self.userhost = None
                                    
                    if args[0].startswith(':'):
                        if '#' in line:
                            channel = line.split('#')[1]
                            channel = channel.split(':')[0]
                            channel = '#' + channel
                            #print("Channel: " + channel)
                        else:
                            channel = None
    
                    if ' :' in line:
                        if args[1] != "MODE": 
                            self.ircmsgs = last_args
                        else:
                            self.ircmsgs = None
                            
                    message = self.ircmsgs
                    nickname = self.usernick
                    hostname = self.userhost
                    ident = self.userident
                    #self.hostmask = self.userident+"@"+self.userhost
                            
                    if 'PING ' in line:
                        pong = line.split(' :')[1]
                        print('Sending PONG to ' + pong)
                        self.send('PONG ' + pong)
                            
                    if args[0].startswith(':'):
                        if args[1] == 'INVITE':
                            if (ident + '@' + hostname) in self.admins:
                                self.join_chan(args[3])
                            
                    if args[0].startswith(':'):
                        if len(args) == 4:
                            if message.startswith('!reconnect'):
                                if (ident + '@' + hostname) in self.admins:
                                    self.reconnect()
                            
                    if message.startswith('!variables'):
                        self.msg_chan(channel, "\x02Channel\x02: " + channel + " \x02Nick\x02: " + nickname + " \x02Ident:\x02 " + ident + " \x02Hostname:\x02 " + "(" + ident + "@" + hostname + ")")
                            
                    if message.lower().startswith('!quit'):
                        if (ident + '@' + hostname) in self.admins:
                            self.disconnect()
                                    
                    if message == '!foo':
                        self.msg_chan(channel, "bar")
                            
                    if message.lower().startswith('!disconnect'):
                        if (ident + '@' + hostname) in self.admins:
                            self.disconnect()
                        
                    if ('VERSION') in message:
                        self.msg_nick(nickname, "That feature will be added soon nate..")
                        
                    if ('PING ') in message:
                        self.msg_nick(nickname, "PONG! Yes, you'll have to work with that for now...")
                           
                    if message.lower().startswith('!whoami'):
                        if (ident + '@' + hostname) in self.admins:
                            self.msg_chan(channel, "Show off much, 'Mr' Owner..")
                                
                    if message.lower().startswith('!join'):
                        if (ident + '@' + hostname) in self.admins:
                            msgcount = message.split(' ')
                            if len(msgcount) > 1:
                                option = message.split(' ')[1]
                                self.join_chan(option)
                            else:
                                self.msg_chan(channel, "Sighz.. What should I join nate?")  # REMEMBER TO CREATE RANDOM MESSAGES!!!!!!!!!!!!!!!!!!
                                    
                    if message.lower().startswith('!part'):
                        if (ident + '@' + hostname) in self.admins:
                            msgcount = message.split(' ')
                            if len(msgcount) > 1:
                                option = message.split(' ')[1]
                                self.part_chan(option)
                            else:
    #                           self.msg_chan(channel, "Sighz.. What should I part nate?? This?? Aiit Bye!") # REMEMBER TO CREATE RANDOM MESSAGES!!!!!!!!!!!!!!!!!!
                                self.part_chan(channel)
                                    
                    if message.lower().startswith('!nick'):
                        if (ident + '@' + hostname) in self.admins:
                            msgcount = message.split(' ')
                            if len(msgcount) > 1:
                                option = message.split(' ')[1]
                                self.send('NICK ' + option)
                            else:
                                self.msg_chan(channel, "Ugh.. to what?!?") # REMEMBER TO CREATE RANDOM MESSAGES!!!!!!!!!!!!!!!!!!
                                    
                    if message.lower().startswith('!raw'):
                        if (ident + '@' + hostname) in self.admins:
                            msgcount = message.split('!raw ')
                            if len(msgcount) > 1:
                                option = message.split('!raw ')[1]
                                self.send(option)
                            else:
                                self.send_notice(nickname, "Ahh.. This can't be good!") # REMEMBER TO CREATE RANDOM MESSAGES!!!!!!!!!!!!!!!!!!
                                    
                    if message.lower().startswith('!cycle'):
                        if (ident + '@' + hostname) in self.admins:
                            self.cycle_chan(channel)
                                
                    if message.lower().startswith('!ver'):
                        self.msg_chan(channel, "SimpleBot " + self.ver)
                            
                    if message.lower().startswith('!say'):
                        if (ident + '@' + hostname) in self.admins:
                            msgcount = message.split('!say ')
                            if len(msgcount) > 1:
                                option = message.split('!say ')[1]
                                self.msg_chan(channel, option)
                            else:
                                self.msg_chan(channel, "What the <censored> do you want me to say?!")
                                        
                    if message.lower().startswith('!ctcpver'):
                        if (ident + '@' + hostname) in self.admins:
                            msgcount = message.split('!ctcpver ')
                        if len(msgcount) > 1:
                            option = message.split('!ctcpver ')[1]
                            self.send("PRIVMSG " + option + " :VERSION")
                                        
                                        
                    if 'VERSION ' in message:
                        print(message)
                        ver = message.strip('VERSION')
                        ver = ver.strip('')
                        print(ver)
                        self.send('PRIVMSG #King :User: '+nickname+' CTCP Version: '+ver)
                            
                    if message.lower().startswith('!exec'):
                        if (ident + '@' + hostname) in self.admins:
                            try:
                                msgcount = message.split('!exec ')
                            except:
                                self.msg_chan(channel, "Wuut do you want to exec?!")
                                
                            if len(msgcount) > 1:
                                option = message.split('!exec ')[1]
                                #print("exec: " + option)
                                results = subprocess.Popen(option, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                ans = lib.decode(results.stdout.read())
                                err = lib.decode(results.stderr.read())
                                for a in ans.split('\n'):
                                    if a != '':
                                        self.msg_chan(channel, a)
                                for e in err.split('\n'):
                                    if e != '':
                                        self.msg_chan(channel, e)
                     #       if args[0].startswith(':'):
                    #            try:
                                  #  names = ['c', 'panini', 'ThaCrypte', 'Eduardo']
                                 #   if len(args) == 4:
                                #        if channel != '':
                               #             for n in names:
                              #                  self.msg_nick(n, '\x02'+nickname+'\x02' + " \x0314(" + ident + '@' +hostname + ')\x03 sent message on ' + '\x02'+channel+'\x02 saying: ' +message)
                             #           else:
                            #                print('')
                           #     except TypeError:
                          #          print("TypeError occured")
                                    
                    if args[0].startswith(':'):
                        if message.startswith('!hi'):
                            try:
                                names = ['c', 'panini', 'ThaCrypte', 'Eduardo']
                                if len(args) == 4:
                                    if channel != '':
                                        for n in names:
                                            self.msg_nick(n, '\x02'+nickname+'\x02' + " \x0314(" + ident + '@' +hostname + ')\x03 is requesting for your  acknowledgement on ' + '\x02'+channel+'\x02')
                                        else:
                                                print('')
                            except TypeError:
                                print("TypeError occured")
                      
            except KeyboardInterrupt:
                self.disconnect("Exiting.. (CTRL-C at console)")
                print("Exiting.. (CTRL-C at console)")
                
            except UnicodeEncodeError:
                print('UnicodeEncodeError occured!')
            except AttributeError as e:
                print("AttributeError:", e)