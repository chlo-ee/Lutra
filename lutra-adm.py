#! /usr/bin/env python
import configparser
import random
import string

from LutraDB.database import LutraDB
from LutraDB.objects.position import Position
from LutraDB.objects.tracker import Tracker
from LutraDB.objects.user import User
from LutraDB.objects.user_tracker import UserTracker

config = configparser.ConfigParser()
config.read('config.ini')
db_file = config['DB']['sqlite_file']
db = LutraDB(db_file)


def adduser():
    username = input("Username: ")
    if User.get_by_username(db, username) is not None:
        print("Username is already in use!")
        return
    user = User(db)
    user.set_name(username)
    password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
    user.hash_and_set_password(password)
    user.save_record()
    print(f'Created new user with password {password}')


def addtracker():
    ttn_identifier = input('TTN identifier: ')
    if Tracker.get_by_ttn_identifier(db, ttn_identifier) is not None:
        print("TTN identifier is already in use!")
        return
    tracker = Tracker(db)
    tracker.set_ttn_identifier(ttn_identifier)
    tracker.set_name(input("Name: "))
    tracker.set_deviation(int(input("Deviation: ")))
    tracker.save_record()
    print("Tracker created.")


def deluser():
    username = input("Username: ")
    user = User.get_by_username(db, username)
    if user is None:
        print("Username does not exist!")
        return
    for user_tracker in UserTracker.get_user_trackers_by_user(db, user):
        user_tracker.delete_record()
    user.delete_record()


def deltracker():
    ttn_id = input("TTN ID: ")
    tracker = Tracker.get_by_ttn_identifier(db, ttn_id)
    if tracker is None:
        print("Tracker does not exist!")
        return
    for user_tracker in UserTracker.get_user_trackers_by_tracker(db, tracker):
        user_tracker.delete_record()
    for position in Position.get_all_for_tracker(db, tracker):
        position.delete_record()
    tracker.delete_record()


def assigntracker():
    ttn_id = input("TTN ID: ")
    tracker = Tracker.get_by_ttn_identifier(db, ttn_id)
    if tracker is None:
        print("Tracker does not exist!")
        return
    username = input("Username: ")
    user = User.get_by_username(db, username)
    if user is None:
        print("Username does not exist!")
        return
    for ut in UserTracker.get_user_trackers_by_tracker(db, tracker):
        if ut.get_user().get_id() == user.get_id():
            print("Tracker is already assigned to this user.")
            return
    user_tracker = UserTracker(db)
    user_tracker.set_tracker(tracker)
    user_tracker.set_user(user)
    user_tracker.save_record()


def unassigntracker():
    ttn_id = input("TTN ID: ")
    tracker = Tracker.get_by_ttn_identifier(db, ttn_id)
    if tracker is None:
        print("Tracker does not exist!")
        return
    username = input("Username: ")
    user = User.get_by_username(db, username)
    if user is None:
        print("Username does not exist!")
        return
    for ut in UserTracker.get_user_trackers_by_tracker(tracker):
        if ut.get_user().get_id() == user.get_id():
            ut.delete_record()


def main():
    run = True
    while(run):
        command = input('''
Lutra Admin Console
___________________
    
Commands:
    adduser:            Adds a user
    addtracker:         Adds a tracker
    deluser:            Deletes a user
    deltracker:         Deletes a tracker
    assigntracker:      Assigns a tracker to a user
    unassigntracker:    Unassigns a tracker from a user
    exit:               Exits this tool
>''')
        if command == 'adduser':
            adduser()
        elif command == 'addtracker':
            addtracker()
        elif command == 'deluser':
            deluser()
        elif command == 'deltracker':
            deltracker()
        elif command == 'assigntracker':
            assigntracker()
        elif command == 'unassigntracker':
            unassigntracker()
        elif command == 'exit':
            run = False


if __name__ == '__main__':
    main()
