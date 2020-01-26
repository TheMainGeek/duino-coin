#!/usr/bin/env python3
##############################################
# Duino-Coin PoT Miner (Beta v2) © revox 2020
# https://github.com/revoxhere/duino-coin 
##############################################
import socket, statistics, threading, time, numpy, re, configparser, sys, datetime, os, signal, subprocess # Import libraries
from decimal import Decimal
from pathlib import Path
from signal import signal, SIGINT

if os.name != 'nt': # Check if running on Windows
  win = input("✗ You can use Proof-Of-Time miner only on Windows. Type 'y' to continue.")
  if win != "y":
    os._exit(1)

if not Path("PoT_auto.exe").is_file(): # Check for PoT exe
  print("✗ PoT executable is missing. Exiting in 15s.")
  time.sleep(15)
  os._exit(1)
 

try: # Check if colorama is installed
  from colorama import init, Fore, Back, Style
except:
  print("✗ Colorama is not installed. Please install it using pip install colorama. Exiting in 15s.")
  time.sleep(15)
  os._exit(1)

try: # Check if requests is installed
  import requests
except:
  print("✗ Requests is not installed. Please install it using pip install requests. Exiting in 15s.")
  time.sleep(15)
  os._exit(1)

# Setting variables
res = "https://raw.githubusercontent.com/revoxhere/duino-coin/gh-pages/serverip.txt" # Serverip file
income = 0
timer = 30
reward = 0.025219
config = configparser.ConfigParser()
VER = "0.8" # "Big" version number  (0.8 = Beta 2)
timeout = 10 # Socket timeout


def handler(signal_received, frame): # If CTRL+C or SIGINT received, send CLOSE request to server in order to exit gracefully.
  print("\n✓ SIGINT detected - exiting gracefully. See you soon!")
  try:
        subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=process.pid), shell=True, stderr=subprocess.DEVNULL) # Exit Magi Miner
  except:
        pass
  try:
        soc.send(bytes("CLOSE", encoding="utf8")) # Let the server niecely close the connection
  except:
        pass
  os._exit(0)

signal(SIGINT, handler) # Enable signal handler

def Greeting(): # Greeting message depending on time :)
  global greeting, message
  print(Style.RESET_ALL)
  
  current_hour = time.strptime(time.ctime(time.time())).tm_hour
  
  if current_hour < 12 :
    greeting = "Good morning"
  elif current_hour == 12 :
    greeting = "Good noon"
  elif current_hour > 12 and current_hour < 18 :
    greeting = "Good afternoon"
  elif current_hour >= 18 :
    greeting = "Good evening"
  else:
        greeting = "Hello"
    
  message  = "║ Duino-Coin Proof-of-Time Miner (Beta v2) © revox 2019-2020\n" # Startup message
  message += "║ https://github.com/revoxhere/duino-coin\n"
  message += "║ "+str(greeting)+", "+str(username)+" \U0001F44B\n\n"
  
  for char in message:
    sys.stdout.write(char)
    sys.stdout.flush()
    time.sleep(0.01)


def loadConfig(): # Config loading section
  global pool_address, pool_port, username, password, efficiency
  cmd = "PoT_auto -o stratum+tcp://xmg.minerclaim.net:3333 -u revox.duinocoin -p x -e 50 -s 4" # Miner command
  
  if not Path("PoTConfig_beta.2.ini").is_file(): # Initial configuration section
    print(Style.BRIGHT + "Initial configuration, you can edit 'MinerConfig_beta.1.ini' file later.")
    print(Style.RESET_ALL + "Don't have an account? Use " + Fore.YELLOW + "Wallet" + Fore.WHITE + " to register.\n")

    username = input("Enter your username: ")
    password = input("Enter your password: ")
    
    config['miner'] = { # Format data
    "username": username,
    "password": password}
    
    with open("PoTConfig_beta.2.ini", "w") as configfile: # Write data to file
      config.write(configfile)

  else: # If config already exists, load from it
    config.read("PoTConfig_beta.2.ini")
    username = config["miner"]["username"]
    password = config["miner"]["password"]
    

def Connect(): # Connect to pool section
  global soc, connection_counter, res, pool_address, pool_port
  
  while True: # Grab data grom GitHub section
    try:
      try:
        res = requests.get(res, data = None) #Use request to grab data from raw github file
      except:
        pass
      if res.status_code == 200: #Check for response
        content = res.content.decode().splitlines() #Read content and split into lines
        pool_address = content[0] #Line 1 = pool address
        pool_port = content[1] #Line 2 = pool port

        now = datetime.datetime.now()
        break # Continue
      else:
        time.sleep(0.025) # Restart if wrong status code
        
    except:
      now = datetime.datetime.now()
      print(now.strftime(Style.DIM + "%H:%M:%S ") + Fore.RED + "✗ Cannot receive pool address and IP. Exiting in 15 seconds.")
      time.sleep(15)
      os._exit(0)
      
    time.sleep(0.025)
    
  while True:
    try: # Shutdown previous connections if any
      soc.shutdown(socket.SHUT_RDWR)
      soc.close()
    except:
      pass
    
    try:
      soc = socket.socket()
    except:
      Connect() # Reconnect if pool down
    
    try: # Try to connect
      soc.connect((str(pool_address), int(pool_port)))
      soc.settimeout(timeout)
      break # If connection was established, continue
    
    except: # If it wasn't, display a message and exit
      now = datetime.datetime.now()
      print(now.strftime(Style.DIM + "%H:%M:%S ") + Fore.RED + "✗ Cannot connect to the server. It is probably under maintenance. Retrying in 15 seconds...")
      time.sleep(15)
      os._exit(0)
      
    Connect()  
    time.sleep(0.025)
    

def checkVersion():
  try:
    try:
      SERVER_VER = soc.recv(1024).decode() # Check server version
    except:
      Connect() # Reconnect if pool down
      
    if SERVER_VER == VER: # If miner is up-to-date, display a message and continue
      now = datetime.datetime.now()
      print(now.strftime(Style.DIM + "%H:%M:%S ") + Fore.YELLOW + "✓ Connected to the server (v"+str(SERVER_VER)+")")
    else:
      now = datetime.datetime.now()
      print(now.strftime(Style.DIM + "%H:%M:%S ") + Fore.RED + "✗ Miner is outdated (v"+VER+"), server is on v"+SERVER_VER+" please download latest version from https://github.com/revoxhere/duino-coin/releases/\nExiting in 15 seconds.")
      time.sleep(15)
      os._exit(0)
  except:
    Connect() # Reconnect if pool down


def Login():
  while True:
    try:
      try:
        soc.send(bytes("LOGI," + username + "," + password, encoding="utf8")) # Send login data
      except:
        Connect() # Reconnect if pool down
        
      try:
        resp = soc.recv(1024).decode()
      except:
        Connect() # Reconnect if pool down
        
      if resp == "OK": # Check wheter login information was correct
        now = datetime.datetime.now()
        print(now.strftime(Style.DIM + "%H:%M:%S ") + Fore.YELLOW + "✓ Logged in successfully")
        break # If it was, continue
      
      if resp == "NO":
        now = datetime.datetime.now()
        print(now.strftime(Style.DIM + "%H:%M:%S ") + Fore.RED + "✗ Error! Wrong credentials or account doesn't exist!\nIf you don't have an account, register using Wallet!\nExiting in 15 seconds.")
        soc.close()
        time.sleep(15)
        os._exit(0) # If it wasn't, display a message and exit
    except:
      Connect() # Reconnect if pool down

    time.sleep(0.025) # Try again if no response


def Mine(): # "Mining" section
    global process, timer, reward, income
    try: # Start Magi Miner
        process = subprocess.Popen(cmd, shell=True, stderr=subprocess.DEVNULL) # Open command
        now = datetime.datetime.now()
        print(now.strftime(Style.DIM + "%H:%M:%S ") + Fore.YELLOW + "✓ Proof of Time thread started")
    except:
        now = datetime.datetime.now()
        print(now.strftime(Style.DIM + "%H:%M:%S ") + Fore.RED + "✗ Error while launching PoT executable!\nExiting in 15s.")
        time.sleep(15)
        os._exit(0)

    now = datetime.datetime.now()
    print(now.strftime(Style.DIM + "\n") + Fore.YELLOW + "ⓘ　Duino-Coin network is a completely free service and will always be. You can really help us maintain the server and low-fee payouts by donating - visit " + Fore.GREEN + "https://revoxhere.github.io/duino-coin/donate" + Fore.YELLOW + " to learn more.\n")

    while True:
        print("", end = Style.DIM + Fore.YELLOW + f"\r⏲　Next reward in {timer:02} seconds " + Style.RESET_ALL + Style.DIM + "▓"*timer + " ")
        timer -= 1
        time.sleep(1)
        if timer <= 0: # Ask for reward every 60s; btw. even if you'd change it, server wouldn't allow for faster submission. You can check it.
            income += reward
            income = round(float(income), 8)
            timer = 30 # Reset the timer
            soc.send(bytes("PoTr", encoding="utf8")) # Send Proof-of-Time-reward request
            now = datetime.datetime.now()
            print("", end=f"\r" + now.strftime(Style.DIM + "%H:%M:%S ") + Style.RESET_ALL + Style.BRIGHT + Fore.YELLOW + "» You've been rewarded! This session estimated income is " + str(income) + " DUCO\n")

init(autoreset=True) # Enable colorama

while True:
  try:
      loadConfig() # Load configfile
  except:
      print(Style.BRIGHT + Fore.RED + "✗ There was an error loading the configfile. Try removing it and re-running configuration."  + Style.RESET_ALL)

  try:
    Greeting() # Display greeting message
  except:
    print(Style.BRIGHT + Fore.RED + "✗ You somehow managed to break the greeting message!"  + Style.RESET_ALL)

  try:
      Connect() # Connect to pool
  except:
      print(Style.BRIGHT + Fore.RED + "✗ There was an error connecting to pool. Check your config file." + Style.RESET_ALL)

  try:
      checkVersion() # Check version
  except:
      print(Style.BRIGHT + Fore.RED + "✗ There was an error checking version. Restarting." + Style.RESET_ALL)

  try:
      Login() # Login
  except:
      print(Style.BRIGHT + Fore.RED + "✗ There was an error while logging in. Restarting." + Style.RESET_ALL)

  try:
      Mine() # "Mine"
  except:
      print(Style.BRIGHT + Fore.RED + "✗ There was an error in PoT section. Restarting." + Style.RESET_ALL)

  print(Style.RESET_ALL)
  time.sleep(0.025) # Restart if error