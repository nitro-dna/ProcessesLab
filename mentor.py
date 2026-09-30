import os
import sys
import signal
import goggles # Allowed only during the setup phase[cite: 4]

# Global variables for the Mentor
mentor_name = "Gandalf"
dungeon_file = ""
party_file = ""
dungeon_dims = (0, 0)
dungeon_map = []      # Matrix to track Fog of War ('?' for unvisited cells)
adventurers = []      # List of dictionaries/objects containing initial adventurer data
opened_boxes = set()  # Set of (r, c) tuples storing positions of opened boxes
total_gold = 0        # Cumulative gold collected by the party

#  1: ARGUMENT PARSING AND PARTY VALIDATION
def parse_arguments():
    global mentor_name, dungeon_file, party_file
    i = 1 # Start from index 1 to skip the script name
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '-dungeon':
            dungeon_file = sys.argv[i+1]
            i += 2
        elif arg == '-party':
            party_file = sys.argv[i+1]
            i += 2
        else:
            # If it has no flag, it is the mentor name
            mentor_name = arg
            i += 1
    pass

def load_party_and_validate():
    global dungeon_file, party_file, dungeon_dims, dungeon_map, adventurers
    current_id = 1  
    try:
        with open(party_file, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                # "(2,2) 100 100 70 Princess Donut" -> "2 2 100 100 70 Princess Donut"
                clean_line = line.replace('(', '').replace(')', '').replace(',', ' ')
                
                parts = clean_line.split()

                pos_r = int(parts[0])
                pos_c = int(parts[1])
                health = int(parts[2])
                mana = int(parts[3])
                gold = int(parts[4])
                name = " ".join(parts[5:])

                adv_data = {
                    "id": current_id,
                    "name": name,
                    "pos_r": pos_r,
                    "pos_c": pos_c,
                    "health": health,
                    "mana": mana,
                    "gold": gold
                }
                
                adventurers.append(adv_data)
                current_id += 1

        return adventurers

    except OSError as e:
        sys.stderr.write(f"Error al abrir el archivo {party_file}: {e}\n")
        sys.exit(1)

    sensor = goggles.GogglesSpell(dungeon_file)
    dungeon_dims = sensor.dimensions()

    for adv in adventurers:
        pos_r = adv["pos_r"]
        pos_c = adv["pos_c"]

        if not (0 <= pos_r < dungeon_dims[0] and 0 <= pos_c < dungeon_dims[1]):
            sys.stderr.write(f"Error: Adventurer {adv['id']} position ({pos_r}, {pos_c}) is out of bounds.\n")
            sys.exit(1)

        if sensor.is_obstacle(pos_r, pos_c):
            sys.stderr.write(f"Error: Adventurer {adv['id']} position ({pos_r}, {pos_c}) overlaps with an obstacle.\n")
            sys.exit(1)

        for other_adv in adventurers:
            if other_adv["id"] != adv["id"] and other_adv["pos_r"] == pos_r and other_adv["pos_c"] == pos_c:
                sys.stderr.write(f"Error: Adventurer {adv['id']} position ({pos_r}, {pos_c}) overlaps with adventurer {other_adv['id']}.\n")
                sys.exit(1)

    pass

def main():
    parse_arguments()
    load_party_and_validate()
    channels = {}
    for adv in adventurers:
        try:
            adv_id = adv["id"]
            adv_to_mentor_r, adv_to_mentor_w = os.pipe() # Create a pipe for communication with the adventurer
            mentor_to_adv_r, mentor_to_adv_w = os.pipe() # Create a pipe for communication with the mentor
            channels[adv_id] = {
            "cmd_in": mentor_to_adv_r,      
            "cmd_out": mentor_to_adv_w,     
            "resp_in": adv_to_mentor_r,    
            "resp_out": adv_to_mentor_w,   
            "pid": None
           }
             
            pid_adv = os.fork()  # Fork a new process for each adventurer
        except OSError as e:
            sys.exit(f"Fork failed: {e}") 
        if pid_adv == 0:  # Child process (adventurer)
            os.dup2(adv_to_mentor_r, sys.stdin.fileno())  # Redirect stdin to read from the mentor
            os.dup2(adv_to_mentor_w, sys.stdout.fileno())  # Redirect stdout to write to the mentor
            os.close(adv_to_mentor_w)  # Close the read end in the child
            os.close(adv_to_mentor_r)  # Close the write end in the child
            try:
              os.execl(
               sys.executable,                               # Path to the Python interpreter
               "python3",                                    # arg0
               "-u",                                         # unbuffered exit
               "adventurer.py",                              # script name
               str(adv["id"]),                               # adventurer Id
               "-f", dungeon_file,                           # maze file
               "-pos", str(adv["pos_r"]), str(adv["pos_c"]), # Initial position
               "-h", str(adv["health"]),                     # Health
               "-m", str(adv["mana"]),                       # Mana
               "-g", str(adv["gold"]),                       # Gold
               "-n", adv["name"]                             # Name
               )
            except OSError as e:
              sys.stderr.write(f"Error al mutar el proceso: {e}\n")[cite: 1]
              sys.exit(1)

        else:  # Parent process (mentor)
       

# =====================================================================
# 3: FORK AND CHILD MUTATION (EXEC)
# =====================================================================
# 1. Loop over each validated adventurer and call os.fork()[cite: 4].
# 2. Child branch (pid == 0):
#    - Redirect stdin: os.dup2(command_pipe_read, sys.stdin.fileno())[cite: 2]
#    - Redirect stdout: os.dup2(response_pipe_write, sys.stdout.fileno())[cite: 2]
#    - Close all unused pipe descriptors[cite: 2].
#    - Replace child process image using os.execl() to execute 'adventurer.py'[cite: 4].
#      Arguments: ID, -f dungeon_file, -pos r c, -h health, -m mana, -g gold, -n name[cite: 4]
# 3. Parent branch (pid > 0):
#    - Save the child PID and active pipe descriptors.
#    - Close the pipe ends that the mentor will not use[cite: 2].

# =====================================================================
# 4: MENTOR SIGNAL HANDLERS
# =====================================================================
# Configure signals using signal.signal():
# - SIGINT: Finish program, print current party info, wait for children, and exit[cite: 4].
# - SIGTSTP: Send signal to decrease health of all adventurers by 10[cite: 4].
# - SIGUSR1: Send signal to all adventurers to buy mana potion; update party gold[cite: 4].
# - SIGUSR2: Send signal to all adventurers to cast healing spell[cite: 4].
# - SIGQUIT: Query and print current position, health, mana, and gold for all adventurers[cite: 4].

# =====================================================================
# 5: MENTOR INTERACTIVE COMMAND LOOP
# =====================================================================
while True:
    try:
     choice = input("Enter command: ")
     choice = choice.lower()
     parts = choice.split()

     if (len(parts) == 0):
         continue 
     command = parts[0]
     if command == "exit":
         for adv in adventurers:
             pid = channels[adv["id"]]["pid"]
             os.kill(pid, signal.SIGTERM)  # Send SIGTERM to each adventurer
         for adv in adventurers:
             pid = channels[adv["id"]]["pid"]
             os.waitpid(pid, 0)  # Wait for each adventurer to terminate
         print("All adventurers have exited. Mentor exiting.")
         sys.exit(0)
     elif command == "print":
        # Display the discovered map with Fog of War ('?'), showing adventurers as 'A'
        

# Implement the command-line interface loop (while True):
# - mv <id/all> <direction>:
#     Check for collisions against walls or other adventurers before sending command[cite: 4].
#     Forward 'mv <dir>' via command pipe, read response, update 'dungeon_map' and position[cite: 4].
# - print:
#     Display the discovered map with Fog of War ('?'), showing adventurers as 'A'[cite: 4].
# - pos <id/all>:
#     Print cached adventurer positions[cite: 4].
# - health <id/all>:
#     Query health from adventurer via pipe and print result[cite: 4].
# - unbox <id/all>:
#     Check 'opened_boxes'; prevent opening if already opened, else forward 'unbox'[cite: 4].
# - petrify <id/all> / depetrify <id/all>:
#     Send SIGTSTP / SIGCONT directly to the designated adventurer PID(s)[cite: 4].
# - exit:
#     Send 'exit' command to all children, wait for their termination using os.waitpid(),
#     print exit statuses, and display summary stats[cite: 4].


if __name__ == "__main__":
    main()