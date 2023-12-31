#!/usr/bin/env python
# coding: utf-8
import os.path
import csv
import datetime
import time
import requests
import json
import math
import threading
import RPi.GPIO as GPIO

#Does config file exist?
if not os.path.exists("config.json"):
    print("No config file found. Starting out of box experience...")
    print("Goodbye!")
    os.system("python -m flask run --host=0.0.0.0 --port=4000")
    exit()
#No -> Launch UI to decide location
#Set station code and track circuit IDs. Buffer time (naptime). Arrival countdown & Platform Countdown.
#Yes -> Proceed Headless

#Different time periods per day
def is_allowed_time():
    # Get the current date and time
    now = datetime.datetime.now()

    # Get the day of the week (0 = Monday, 6 = Sunday)
    day_of_week = now.weekday()

    # Get the current hour (24-hour format)
    current_hour = now.hour

    # Define allowed hours for weekdays and weekends


    if day_of_week < 5:  # Weekdays (0 to 4)
        return weekdays_allowed_hours[0] <= current_hour < weekdays_allowed_hours[1] or weekdays_allowed_hours[2] <= current_hour < weekdays_allowed_hours[3]
    else:  # Weekends (5 and 6)
        return weekends_allowed_hours[0] <= current_hour < weekends_allowed_hours[1] or weekends_allowed_hours[2] <= current_hour < weekends_allowed_hours[3]


api_key = '38142ab0581f40d0ae102dfea30da93b'  # Replace with your actual API key
headers = {'api_key': api_key}


#Set the variables to that of the config file.
with open('config.json') as file:
    settings = json.loads(file.read())

station_code = settings['station']

for row in csv.reader(open("Track Circuits.csv")):
    if row[0] == station_code:
        # circuit_id is the id for the track circuit at the platform
        circuit_id1 = int(row[2])
        circuit_id2 = int(row[3])
        # circuit_ida is the id for the arrival circuit*
        circuit_ida1 = int(row[4])
        circuit_ida2 = int(row[5])
        #start/end times for program to run
        print(circuit_id1)
        print(circuit_id2)
        print(circuit_ida1)
        print(circuit_ida2)
        time.sleep(10)
        

# consts in the program that are vars for ease of access
# arrival_countdown starts at the farther track circuit, platform_countdown starts at the platform
arrival_countdown = int(settings['arrivalCountdown'])

platform_countdown = int(settings['platformCountdown'])


# naptime is the minimum time the light must be off after cooldown < 0 or cooldown2 < 0
naptime = int(settings['bufferTime'])
start_time_weekday_1 =int( settings['weekdaystart1'])
end_time_weekday_1 = int(settings['weekdayend1'])
start_time_weekday_2 = int(settings['weekdaystart2'])
end_time_weekday_2 = int(settings['weekdayend2'])
start_time_weekend_1 = int(settings['weekendstart1'])
end_time_weekend_1 = int(settings['weekendend1'])
start_time_weekend_2 = int(settings['weekendstart2'])
end_time_weekend_2 = int(settings['weekendend2'])

def is_allowed_time():
    # Get the current date and time
    now = datetime.datetime.now()

    # Get the day of the week (0 = Monday, 6 = Sunday)
    day_of_week = now.weekday()

    # Get the current hour (24-hour format)
    current_hour = now.hour

    # Define allowed hours for weekdays and weekends


    if day_of_week < 5:  # Weekdays (0 to 4)
        return start_time_weekday_1 <= current_hour < end_time_weekday_1 or start_time_weekday_2 <= current_hour < end_time_weekday_2
    else:  # Weekends (5 and 6)
        return start_time_weekend_1 <= current_hour < end_time_weekend_1 or start_time_weekend_2 <= current_hour < end_time_weekend_2

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
# In[28]:



# api key, kind of important
api_key = '38142ab0581f40d0ae102dfea30da93b'
headers = {'api_key': api_key}

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
    
# function that uses train positions (see above) to check if a train is on a specified circuit
def find_trains_on_circuit(circuit_id):
    train_positions = get_train_positions()

    if train_positions:
        trains_on_circuit = [train for train in train_positions if train['CircuitId'] == circuit_id]
        return trains_on_circuit
    else:
        return None


# function that checks if a trainID matches any train in a list of trains
def is_train_gone(train_id, train_list):
    for train in train_list:
        if train['TrainId'] == train_id:
            return False
    
    return True

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

#set up GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)

def check_light_flag():
    global light_flag
    # essentially with multithreading, as long as countdown > 0, this will turn the light on and off
    
    while seconds > 0:
        if light_flag == 1:
            GPIO.output(11, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(11, GPIO.LOW)
            time.sleep(0.5)
        else:
            time.sleep(1)
            
    

# Create and start a new thread that will run the check_light_flag function
flag_thread = threading.Thread(target=check_light_flag)
flag_thread.start()

print(is_allowed_time())
# the program will run forever so this code is in a while loop
""" should make into function later """
while True: 

    while is_allowed_time(): #runs if the time of day is right 
        # we need to catch the timing of the program to make sure it runs every second
        start_time = time.time()
        # if the countdown is negative, we set it to 0 (shouldn't be negative)
        if countdown <= 0:
            countdown = 0
            light_flag = 0
        else:
            light_flag = 1
            
        print(f'start for loop light flag: {light_flag}')
            
            # then we fetch the status of the circuits (see if they are occupied)
        # the arrivals and platform variables are lists of trains
        start_internet = time.time()
        arrivals1 = find_trains_on_circuit(circuit_ida1)
        arrivals2 = find_trains_on_circuit(circuit_ida2)
        platform1 = find_trains_on_circuit(circuit_id1)
        platform2 = find_trains_on_circuit(circuit_id2)
        end_internet = time.time()
        print(f"internet connection speed: {end_internet - start_internet}")
        print(arrivals1)
        print(arrivals2)
        print(platform1)
        print(platform2)
        
        # checking if there are any new revenue trains and adding their IDs to a list
        for train in arrivals1:
            if not(train['TrainId'] in arr_list):
                print(f"new train - arrivals 1, trainID: {train['TrainId']}, trainNum: {train['TrainNumber']}")
                if train['ServiceType'] == 'Normal':
                    newtrain = True
                    arr_list.append(train['TrainId'])
                    
        for train in arrivals2:
            if not(train['TrainId'] in arr_list):
                print(f"new train - arrivals 2, trainID: {train['TrainId']}, trainNum: {train['TrainNumber']}")
                if train['ServiceType'] == 'Normal':
                    newtrain = True
                    arr_list.append(train['TrainId'])
        
        # a new train on arrival means the countdown is set to 5 minutes
        if newtrain and countdown <= 0:
            countdown = arrival_countdown
            countdown2 = arrival_countdown
            active_cd2 = True
            newtrain = False
        elif newtrain:
            countdown = arrival_countdown
            newtrain = False
            
        # checking if there are any new revenue trains *at platform* and adding their IDs to a list
        for train in platform1:
            if not(train['TrainId'] in brd_list):
                print(f"new train - platform 1, trainID: {train['TrainId']}, trainNum: {train['TrainNumber']}")
                if train['ServiceType'] == 'Normal':
                    newtrain = True
                    brd_list.append(train['TrainId'])
                    print(train['TrainId'])
                    
        for train in platform2:
            if not(train['TrainId'] in brd_list):
                print(f"new train - platform 2, trainID: {train['TrainId']}, trainNum: {train['TrainNumber']}")
                if train['ServiceType'] == 'Normal':
                    newtrain = True
                    brd_list.append(train['TrainId'])
                    print(train['TrainId'])
                    
        # a new train at platform means the countdown is reset to 3 minutes
        if newtrain and countdown <= 0:
            countdown2 = arrival_countdown
            countdown = platform_countdown
            active_cd2 = True
            newtrain = False
        elif newtrain:
            print("new train on brd")
            countdown = platform_countdown
            newtrain = False

            
        # checks if the trains have left any of the circuits - if so, removes their ID's from corresponding ID lists
        for train_id in arr_list:
            bool1 = is_train_gone(train_id, arrivals1)
            bool2 = is_train_gone(train_id, arrivals2)
            if bool1 and bool2:
                del arr_list[arr_list.index(train_id)]
                print("train removed from arr")
        for train_id in brd_list:
            bool1 = is_train_gone(train_id, platform1)
            bool2 = is_train_gone(train_id, platform2)
            if bool1 and bool2:
                del brd_list[brd_list.index(train_id)]
                print("train removed from brd")
         
        print("countdown: ", countdown)
        print("countdown2: ", countdown2)
        
        # decrease in countdown and (temp var) seconds, waits 1 second
        
        end_time = time.time()
        run_time = end_time - start_time
        print(run_time)
        
        sleep = math.ceil(run_time)
        
        time.sleep(sleep - run_time)
        
        countdown = countdown - sleep
        if countdown2 < 0:
            countdown2 = 0
        else:
            countdown2 = countdown2 - sleep
        seconds = seconds - sleep
    # Catch-all case that ensures light doesn't flash for longer than 5 minutes
        if countdown2 < 1 and active_cd2:
            active_cd2 = False
            countdown = 0
            countdown2 = 0
            light_flag = 0
            print(f'max time light flag: {light_flag}')
            time.sleep(60)
    # Ensure light does not re-activate within 60 seconds of turning off to allow bus operators time to notice the light has turned off
        if countdown < 4 and countdown > 1:
            light_flag = 0
            print(f'buffer time light flag: {light_flag}')
            countdown = 0
            countdown2 = 0
            active_cd2 = False
            time.sleep(60)
flag_thread.join()
    

