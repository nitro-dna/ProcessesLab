import sys
import os
import signal
import goggles

# Global variables so signal handlers can access and modify them
adv_name = "Princess Donut" # Default name
adv_id = 0
pos_r = 0
pos_c = 0
health = 100  # Default health
mana = 50     # Default mana
gold = 25     # Default gold
filename = ""
petrified = False
sensor = None

def parse_arguments():
    global adv_id, filename, pos_r, pos_c, health, mana, gold, adv_name
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '-f':
            filename = sys.argv[i+1]
            i += 2
        elif arg == '-pos':
            pos_r = int(sys.argv[i+1])
            pos_c = int(sys.argv[i+2])
            i += 3
        elif arg == '-h':
            health = int(sys.argv[i+1])
            i += 2
        elif arg == '-m':
            mana = int(sys.argv[i+1])
            i += 2
        elif arg == '-g':
            gold = int(sys.argv[i+1])
            i += 2
        elif arg == '-n':
            adv_name = sys.argv[i+1]
            i += 2
        else:
            # If it has no flag, it is the adventurer ID
            adv_id = int(arg)
            i += 1
            
    if not filename:
        sys.stderr.write("Error: -f <filename> is required\n")
        sys.exit(1)

def handle_alarm(sig, frame):
    global health, petrified
    # Decrease health by 1 every 2 seconds if not petrified[cite: 1]
    if not petrified:
        health -= 1
    signal.alarm(2)

def usr1_handler(sig, frame):
    global gold, mana
    if gold > 5:
        gold -= 5
        mana += 10
    else:
        sys.stderr.write("Not enough gold to buy the potion\n")

def usr2_handler(sig, frame):
    global health, mana, pos_r, pos_c, gold
    if mana > 5:
        mana -= 5
        health += 10
    else: 
        sys.stderr.write("Not enough mana to cast the spell\n")

def quit_handler(sig, frame):
    sys.stderr.write("Position: ({}, {}), Health: {}, Mana: {}, Gold: {}\n".format(pos_r, pos_c, health, mana, gold))

def stop_handler(sig, frame):
    global petrified, adv_id, pos_r, pos_c, health
    petrified = True
    sys.stderr.write("Adventurer {} is petrified at position ({}, {}) with health {}\n".format(adv_id, pos_r, pos_c, health))

def main():
    global adv_name, adv_id, pos_r, pos_c, health, mana, gold, sensor, petrified
    
    # 1. Parse arguments manually
    parse_arguments()
    
    my_pid = os.getpid()
    sys.stderr.write(f"My name is {adv_name}, my PID is {my_pid} and my id is {adv_id}\n")
    
    # 2. Initialize the GogglesSpell class
    sensor = goggles.GogglesSpell(filename)
    initial_cell = sensor.what_is_here(pos_r, pos_c)
    if initial_cell == '#':
        sys.stderr.write(f"({pos_r}, {pos_c}) Invalid initial position\n")
        sys.exit(1)
        
    # Wire up the health drain timer[cite: 1]
    signal.signal(signal.SIGALRM, handle_alarm)
    signal.alarm(2)
    
    # Main command loop
    while True:
        try: