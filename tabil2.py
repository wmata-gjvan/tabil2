#!/usr/bin/env python
# coding: utf-8

# In[35]:




import requests
import json
import os.path
import csv

#Does config file exist?
if not os.path.exists("config.json"):
    print("No config file found. Starting out of box experience...")
    print("Goodbye!")
    os.system("python -m flask run")
    exit()
#No -> Launch UI to decide location
#Set station code and track circuit IDs. Buffer time (naptime). Arrival countdown & Platform Countdown.
#Yes -> Proceed Headless

#Different time periods per day

api_key = '38142ab0581f40d0ae102dfea30da93b'  # Replace with your actual API key
headers = {'api_key': api_key}


#Set the variables to that of the config file.
with open('config.json') as file:
    settings = json.loads(file.read())

station_code = settings['station']

for row in csv.reader(open("Track Circuits.csv")):
    if row[0] == station_code:
        # circuit_id is the id for the track circuit at the platform
        circuit_id1 = row[2]
        circuit_id2 = row[3]
        # circuit_ida is the id for the arrival circuit*
        circuit_ida1 = row[4]
        circuit_ida2 = row[5]

# consts in the program that are vars for ease of access
# arrival_countdown starts at the farther track circuit, platform_countdown starts at the platform
arrival_countdown = settings['arrivalCountdown']

platform_countdown = settings['platformCountdown']

# naptime is the minimum time the light must be off after cooldown < 0 or cooldown2 < 0
naptime = settings['bufferTime']


def get_train_predictions(station_code):
    base_url = 'https://api.wmata.com/StationPrediction.svc/json/GetPrediction/'
    url = base_url + station_code
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = json.loads(response.text)
        trains = data['Trains']
        return trains
    else:
        print('Error fetching data: ', response.status_code)
        return None



trains = get_train_predictions(station_code)

if trains:
    for train in trains:
        print(f"Train to {train['DestinationName']} is {train['Min']} minutes away.")
        


# In[28]:


# the imports are IMPORTant :)
import time
import requests
import json
import math
import threading
#import RPi.GPIO as GPIO


# In[5]:


# api key, kind of important
api_key = '38142ab0581f40d0ae102dfea30da93b'
headers = {'api_key': api_key}


# In[6]:


# function to get the positions of all the trains in the system
def get_train_positions():
    url = 'https://api.wmata.com/TrainPositions/TrainPositions?contentType=json'
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = json.loads(response.text)
        return data['TrainPositions']
    else:
        print('Error fetching data: ', response.status_code)
        return None


# In[7]:


# function that uses train positions (see above) to check if a train is on a specified circuit
def find_trains_on_circuit(circuit_id):
    train_positions = get_train_positions()

    if train_positions:
        trains_on_circuit = [train for train in train_positions if train['CircuitId'] == circuit_id]
        return trains_on_circuit
    else:
        return None


# In[8]:


# function that checks if a trainID matches any train in a list of trains
def is_train_gone(train_id, train_list):
    for train in train_list:
        if train['TrainId'] == train_id:
            return False
    
    return True





# In[34]:


# countdown and countdown2 mark the duration of the flashing light, countdown2 will never exceed 5 mins
countdown = 0
countdown2 = 0
# active_cd2 is a redundancy for cooldown 2 to make sure it can be reset to 5 mins
active_cd = False
# active_cd is a redundancy for cooldown so we can guarantee it stops when it reaches 0
active_cd2 = False



# light_flag is the variable that will trigger the external light (hardware)
light_flag = 0

# arr_list and brd_list are lists of trains on arrival and at the platform, respectively
arr_list = []
brd_list = []

# newtrain is a flag for when there is a new train either on arrival or at the platform 
newtrain = False



# duration of the program (might be removed later)
seconds = 600

# raspberry pi stuff
"""
#set up GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)
"""
def check_light_flag():
    global light_flag
    # essentially with multithreading, as long as countdown > 0, this will turn the light on and off
    """
    while seconds > 0:
        if light_flag == 1:
            GPIO.output(11, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(11, GPIO.LOW)
            time.sleep(0.5)
        else:
            time.sleep(1)
            """
    

# Create and start a new thread that will run the check_light_flag function
flag_thread = threading.Thread(target=check_light_flag)
flag_thread.start()

# the program will run forever so this code is in a while loop
""" should make into function later """
while seconds > 0:
    # we need to catch the timing of the program to make sure it runs every second
    start_time = time.time()
    # if the countdown is negative, we set it to 0 (shouldn't be negative) and if countdown <=0 the light is off (0)
    if countdown <= 0:
        countdown = 0
        light_flag = 0
    else:
        # if the countdown is positive, the light should be active (refer to check_light_flag thread)
        light_flag = 1
        
    #print(f'start for loop light flag: {light_flag}')
        
    # then we fetch the status of the circuits (see if they are occupied)
    # the arrivals and platform variables are lists of trains
    start_internet = time.time()
    arrivals1 = find_trains_on_circuit(circuit_ida1)
    arrivals2 = find_trains_on_circuit(circuit_ida2)
    platform1 = find_trains_on_circuit(circuit_id1)
    platform2 = find_trains_on_circuit(circuit_id2)
    end_internet = time.time()
    #print(f"internet connection speed: {end_internet - start_internet}")
    #print(arrivals1)
    #print(arrivals2)
    #print(platform1)
    #print(platform2)
    
    
    # checking if there are any new revenue trains on arrival and adding their IDs to a list
    for train in arrivals1:
        if (train['ServiceType'] == 'Normal') and not(train['TrainId'] in arr_list):
            #print(f"new train - arrivals 1, trainID: {train['TrainId']}, trainNum: {train['TrainNumber']}")
            arr_list.append(train['TrainId'])
            newtrain = True
                
                
    for train in arrivals2:
        if (train['ServiceType'] == 'Normal') and not(train['TrainId'] in arr_list):
            #print(f"new train - arrivals 2, trainID: {train['TrainId']}, trainNum: {train['TrainNumber']}")
            arr_list.append(train['TrainId'])
            newtrain = True
                
    
    # a new train on arrival means the countdown is set to 5 minutes & newtrain var is reset
    # if the countdown already went through the buffer, we set the max cooldown as well (cooldown2)
    # cooldowns then become active
    if newtrain and countdown <= 0:
        countdown = arrival_countdown
        active_cd = True
        countdown2 = arrival_countdown
        active_cd2 = True
        newtrain = False
    elif newtrain:
        countdown = arrival_countdown
        active_cd = True
        newtrain = False
        
    # checking if there are any new revenue trains *at platform* and adding their IDs to a list
    for train in platform1:
        if (train['ServiceType'] == 'Normal') and not(train['TrainId'] in brd_list):
            #print(f"new train - platform 1, trainID: {train['TrainId']}, trainNum: {train['TrainNumber']}")
            brd_list.append(train['TrainId'])
            newtrain = True
            #print(train['TrainId'])
                
    for train in platform2:
        if (train['ServiceType'] == 'Normal') and not(train['TrainId'] in brd_list):
            #print(f"new train - platform 2, trainID: {train['TrainId']}, trainNum: {train['TrainNumber']}")
            newtrain = True
            brd_list.append(train['TrainId'])
            #print(train['TrainId'])
                
    # a new train at platform means the countdown is reset to 3 minutes & newtrain var is reset
    # if the countdown already went through the buffer, we set the max cooldown as well (cooldown2)
    # cooldowns then become active
    if newtrain and countdown <= 0:
        countdown = platform_countdown
        active_cd = True
        countdown2 = arrival_countdown
        active_cd2 = True
        newtrain = False
    elif newtrain:
        #print("new train on brd")
        countdown = platform_countdown
        newtrain = False
        active_cd = True

        
    # checks if the trains have left any of the circuits - if so, removes their ID's from corresponding ID lists
    for train_id in arr_list:
        bool1 = is_train_gone(train_id, arrivals1)
        bool2 = is_train_gone(train_id, arrivals2)
        if bool1 and bool2:
            del arr_list[arr_list.index(train_id)]
            #print("train removed from arr")
    for train_id in brd_list:
        bool1 = is_train_gone(train_id, platform1)
        bool2 = is_train_gone(train_id, platform2)
        if bool1 and bool2:
            del brd_list[brd_list.index(train_id)]
            #print("train removed from brd")
     
    #print("countdown: ", countdown)
    #print("countdown2: ", countdown2)
    # decrease in countdown and (temp var) seconds, waits 1 second
    
    # gets the runtime of the program, so we advance in seconds and not partial seconds
    end_time = time.time()
    run_time = end_time - start_time
    #print(run_time)
    
    # to keep even seconds, we sleep for the runtime rounded up
    sleep = math.ceil(run_time)
    time.sleep(sleep - run_time)
    countdown = countdown - sleep
    seconds = seconds - sleep
    
    # master countdown doesn't decrease if it's already at (or below) zero
    if countdown2 < 0:
        countdown2 = 0
    else:
        countdown2 = countdown2 - sleep
 
    # the countdown will never exceed countdown2 seconds
    if countdown2 < 1 and active_cd2:
        active_cd2 = False
        active_cd = False
        countdown = 0
        countdown2 = 0
        light_flag = 0
        #print(f'max time light flag: {light_flag}')
        time.sleep(naptime)
    
    # buffer implemented after cooldown ends
    if countdown < 1 and active_cd:
        light_flag = 0
        active_cd = False
        #print(f'buffer time light flag: {light_flag}')
        countdown = 0
        countdown2 = 0
        active_cd2 = False
        time.sleep(naptime)
    
flag_thread.join()
    


# In[85]:


# old code
"""
# countdown > 0 => the light is flashing
countdown = 0
# seconds is the length of the program rn
seconds = 30

# while loop to make the program run for seconds seconds
# might want to make this into a function later
while seconds > 0:
    # if the countdown is negative, we set it to 0 (shouldn't be negative)
    if countdown < 0:
        countdown = 0
        
    # then we fetch the status of the circuits (see if they are occupied)
    # the arrivals and platform variables are lists of trains
    arrivals1 = find_trains_on_circuit(circuit_ida1)
    arrivals2 = find_trains_on_circuit(circuit_ida2)
    platform1 = find_trains_on_circuit(circuit_id1)
    platform2 = find_trains_on_circuit(circuit_id2)
    
    # if there are any trains on the arrival circuits and the countdown hasn't started, 5 min ctdwn
    if (len(arrivals1) > 0 or len(arrivals2) > 0) and countdown == 0:
        #start timer
        countdown = 300
    elif countdown < 180 and (len(platform1) > 0 or len(platform2) > 0):
        countdown = 180

    # random print statements - will be removed later - useful for testing
    if platform1:
        for train in platform1:
            print(f"Train {train['TrainNumber']} is on circuit {circuit_id1}.")
            print(f"train has been on platform for: {train['SecondsAtLocation']} seconds {circuit_id1}.")

    if platform2:
        for train in platform2:
            print(f"Train {train['TrainNumber']} is on circuit {circuit_id2}.")
            print(f"train has been on platform for: {train['SecondsAtLocation']} seconds {circuit_id2}.")
    countdown = countdown - 1
    time.sleep(1)
    seconds = seconds - 1
"""


# In[19]:


print("hello")

