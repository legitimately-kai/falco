#!/usr/bin/python3
# -*- coding: utf-8 -*-


import socket, glob, sys, re, os, time, imp
import json
import threading
import subprocess
import traceback
import concurrent.futures
from ssl import wrap_socket
from app.logs.log import log

import app.utils.lib as utils       
from app import hooks

def reload_plugins(init=False):
    plugins_folder = [os.path.join(os.getcwd(), 'app/plugins')]
    plugins = set(glob.glob(os.path.join(os.getcwd() + "app/plugins", "*.py")))
    for plugin in plugins:
        _plugin = os.path.join(os.getcwd(), plugin)
        mtime = os.stat(_plugin).st_mtime
        if mtime != mtimes.get(_plugin):
            mtimes[_plugin] = mtime
            try:
                moduleinfo = imp.find_module(plugin.split(os.path.sep)[1].split(".")[0], plugins_folder)
                pl = imp.load_source(plugin, moduleinfo[1])
            except ImportError as e:
                if str(e).startswith('No module named'):
                    log.error('Failed to load plugin %r: the plugin could not be found.', plugin)
                else:
                    log.error('Failed to load plugin %r: import error %s', plugin, str(e))
                    if init:
                        sys.exit(1)
            except BaseException as e:
                traceback.print_exc()
                log.error(e)
                if init == True:
                    sys.exit(1)
                pass
            else:
                if hasattr(pl, 'main'):
                    for server in utils.connections.values():
                        pl.main(server)
                        log.debug('(%s) Calling main() function of plugin %r', server.netname, plugin)
            log.debug("(Re)Loaded %s", plugin)

def reload_config():
    for irc in utils.connections.values():
        if irc.conf_mtime != os.stat(config_file).st_mtime:
            with open(config_file, "r") as f:
                conf = json.load(f)
            irc.conf_mtime = os.stat(config_file).st_mtime
            irc.conf = conf["servers"][irc.netname]
            irc.reloadConfig()
            log.debug("(%s) Reloaded config", irc.netname)
            
def connectall():
    for server in utils.connections.values():
        log.info("Starting %s connection thread" % server.name)
        server.daemon = True
        server.start()
        
mtimes = dict()
        
class IRC(threading.Thread):
    
    def __init__(self, conf, config_file):
        threading.Thread.__init__(self) 
        self.data_dir = "app/data" + os.path.sep
        os.makedirs(self.data_dir, exist_ok=True)
        self.conf = conf
        self.conf_mtime = os.stat(config_file).st_mtime
        self.address = self.conf["address"]
        self.port = self.conf["port"]
        self.netname = self.conf["netname"]
        self.ssl = self.conf["ssl"]
        self.name = self.netname
        self.autojoin = self.conf["autojoin"]
        self.nick = self.conf["nick"]
        self.gecos = self.conf["gecos"]
        self.user = self.conf["ident"]
        self.password = self.conf["password"]
        self.setmodes = self.conf["modes"]
        self.modes = []
        self.prefixmodes = {'q': '~', 'a': '&', 'v': '+', 'o': '@', 'h': '%'}
        self.connected = False
        self.enabled = False
        self.ver = "v0.0.8"
        self.rx = 0
        self.tx = 0
        self.txmsgs = 0
        self.rxmsgs = 0
        self.cap = []
        self.capdone = False
        self.chanmodes = {}
        self.hasink = True
        self.color = 14
        self.buffermaxlen = 16003
        self.identified = False
        
        self.users = {}
        self.chans = {}
        
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        
        try:
            self.nicks = json.load(open(self.data_dir + "{}-nicks.json".format(self.netname)))
            self.channels = json.load(open(self.data_dir + "{}-channels.json".format(self.netname)))
        except FileNotFoundError:
            self.channels = {}
            self.nicks = {}
        except json.decoder.JSONDecodeError as e:
            sys.exit("{} - {}".format(e, self.netname))
            
        self.reloadConfig()

    def reloadConfig(self):
        self.prefix = self.conf["prefix"]
        self.admins = self.conf["admins"]
        self.ignored = self.conf["ignored"]
        
    def get_channel(self, channelname):
        if channelname not in self.chans.keys():
            self.chans[channelname] = utils.Channel(self, channelname)
        return self.chans[channelname]

    def get_user(self, nickname):
        if nickname in self.users.keys():
            return self.users[nickname]
        else:
            return utils.User("", "", "", "")
            
    def connect(self):
        self.ibuffer = ""
        self.cap = []
        self.capdone = False
        self.started = time.time()
        log.info("(%s) Attempting to connect to %s/%s as %s",
                  self.netname, self.address, self.port, self.nick)
    
        self.socket = socket.create_connection((self.address, self.port))
        if self.ssl:
            self.socket = wrap_socket(self.socket)

        self.send("CAP LS")

        if self.conf.get("password"):
            self.send("PASS {}".format(self.conf["password"]))

        self.send("USER {} 0 * :{}".format(self.user, self.gecos))
        self.send("NICK {}".format(self.nick))
        self.connected = True
        log.debug("(%s) Running main loop", self.netname)
            
    def run(self, override=False):

        if not self.conf.get("active", False) and not override:
            return

        self.connect()
        while self.connected:
            data = utils.decode(self.socket.recv(2048))
            self.ibuffer += data
            while "\r\n" in self.ibuffer:
                reload_plugins()
                reload_config()

                line, self.ibuffer = self.ibuffer.split("\r\n", 1)
                line = line.strip()
                log.debug("(%s) -> %s", self.netname, line)

                self.rx += len(line)
                self.rxmsgs += 1
                #print("Line: ", line)
                
                parsed = utils.parseArgs(line)
                #print(parsed.args)

                try:
                    for hook in utils.command_hooks[parsed.type]:
                        #log.info("(%s) Calling handle %r with args %r", self.netname, hook.__name__, parsed.args)
                        hook(self, parsed)
                except TypeError as e:
                    log.warn("(%s) %s for %r", self.netname, e, hook)
                    traceback.print_exc()
                except:
                    traceback.print_exc()
                    pass
                    
    def send(self, data):
        data = data.replace('\n', ' ').replace("\a", "")
        data = data.encode("utf-8") + b"\r\n"
        stripped_data = data.decode("utf-8").strip("\n")

        log.debug("(%s) <- %s", self.netname, data)

        self.tx += len(data)
        self.txmsgs += 1

        try:
            self.socket.send(data)
        except AttributeError:
            log.warn("(%s) Dropping message %r; network isn't connected!", self.netname, stripped_data)
            self.connected = False
            
    def disconnect(self, quit=None, terminate=True):
        self.send("QUIT :{}".format("Goodbye" if not quit else quit))
        self.connected = False
        try:
            self.socket.close()
        except AttributeError:
            pass
        if terminate:
            sys.exit(0)

    def reconnect(self):
        self.socket.close()
        self.connected = False
        self.run()
        
    def msg(self, target, message, reply=None):
        time.sleep(0.3)

        if self.hasink:
            self.send("{} {} :\x03{}│\x0f {}".format(reply or self.reply, target, self.color, message))
            return

        self.send("{} {} :{}".format(reply, target, message))
 
                    
if __name__ == "__main__":

    log.info("Starting Kybot")

    try:
    
        config_file = "app/configs/config.json"
        global conf

        with open(config_file, 'r') as f:
            conf = json.load(f)

    except ValueError as e:
        log.critical("Error parsing config: {}".format(e))
        sys.exit(1)

    except FileNotFoundError as e:
        log.critical(e)
        sys.exit(1)

    except:
        log.critical("No config file supplied.")
        sys.exit(1)

    utils.api_keys = conf["api_keys"]
    reload_plugins(init=True)

    for server in conf["servers"].values():
        utils.connections[server["netname"]] = IRC(server, config_file)

    reload_plugins(init=True)
    hooks.main()

    connectall()

    while True:
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            sys.stdout.write("\r")
            for server in utils.connections.values():
                server.disconnect("CTRL-C at console", terminate=False)
            sys.exit()


        