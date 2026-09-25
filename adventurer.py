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
    if gold >= 5:
        gold -= 5
        mana += 10
    else:
        sys.stderr.write("Not enough gold to buy the potion\n")

def usr2_handler(sig, frame):
    global health, mana, pos_r, pos_c, gold
    if mana >= 5:
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

def cont_handler(sig, frame):
    global petrified
    if petrified:
      petrified = False
      sys.stderr.write("Adventurer {} is no longer petrified\n".format(adv_id))

def int_handler(sig, frame):
    global health
    if health >= 10:
     health -= 10

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
    # Wire up the other signal handlers
    signal.signal(signal.SIGUSR1, usr1_handler)
    signal.signal(signal.SIGUSR2, usr2_handler)
    signal.signal(signal.SIGQUIT, quit_handler) 
    signal.signal(signal.SIGTSTP, stop_handler)
    signal.signal(signal.SIGCONT, cont_handler)
    signal.signal(signal.SIGINT, int_handler)
    
    # Main command loop
    while True:
        try:
            # 1. Capture the input and make it lowercase
            choice = input("Enter your choice: ")
            choice = choice.lower()
            
            # 2. Split the string into a list of parts
            parts = choice.split()
            
            # 3. Check if the list is empty (in case the user just pressed Enter)
            if (len(parts) == 0):
                continue 
                
            # 4. Extract the main command (the first word)
            command = parts[0]

            # Check if the adventurer is petrified
            if petrified:
                sys.stderr.write(f"{adv_name} is petrified\n")
                continue
            
            # 5. Route the command using if/elif blocks
            if command == "exit":
                print(f"{adv_name}: Position: {pos_r} {pos_c} Health: {health} Mana: {mana} Gold: {gold}")
                sys.exit(0)
                
            elif command == "health":
                print(f"Health: {health}")
                
            elif command == "pos":
                print(f"Position: {pos_r} {pos_c}")
                
            elif command == "unbox":
                if mana < 2:
                    print(f"{adv_name}: I cannot cast spells")
                    continue
                mana -= 2
                cell_content = sensor.what_is_here(pos_r,pos_c)
                if cell_content == 'B':
                    box_type = sensor.type_of_box(pos_r,pos_c)
                    print(f"Type: {box_type}")
                    if box_type == 'MP':
                        mana += 20
                    elif box_type =='MD':
                        mana -= 10
                    elif box_type == 'HP':
                        health +=20
                    elif box_type =='HD':
                        health -=10
                    elif box_type == 'G':
                        gold +=10
                    print(f"Health: {health} Mana: {mana} Gold: {gold}")
                else:
                    print(f"No box at position {pos_r}, {pos_c}")

                print("Unboxing logic goes here...")
                
            elif command == "mv":
                if len(parts) == 2:
                    direction = parts[1]
                    
                # Check if they actually provided a second word (the direction)
                    if health <= 0 or mana < 2:
                        print(f"{adv_name}: I cannot move {direction}")
                        print(f"KO")
                        continue
                    new_r = pos_r
                    new_c = pos_c
                    if direction == 'up':
                        new_r -= 1
                    elif direction == 'down':
                        new_r += 1
                    elif direction == 'left':
                        new_c -= 1
                    elif direction == 'right':
                        new_c += 1
                    mana -= 2
                    target = sensor.what_is_here(new_r, new_c)
                    if target is not None and target != '#':
                        pos_r = new_r
                        pos_c = new_c
                        print(f"OK")
                    else:
                        print(f"{adv_name}: I cannot move {direction}")
                        print(f"KO")
                else:
                    print("Invalid move command. Did you forget the direction?")
                    
            else:
                print("Invalid command")
                
        except EOFError:
            break
        except InterruptedError:
            continue
