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
channels = {}
opened_boxes = set()  # Set of (r, c) tuples storing positions of opened boxes
total_gold = 0        # Cumulative gold collected by the party
opened_boxes = set()  # Set of (r, c) tuples storing positions of opened boxes

#  1: ARGUMENT PARSING AND PARTY VALIDATION
def parse_arguments():
    global mentor_name, dungeon_file, party_file, channels
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

        ##return adventurers

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

def handle_usr1(sig, frame):
    for adv_id, data in channels.items():
        child_pid = data["pid"]

        if child_pid is not None:
            os.kill(child_pid, signal.SIGUSR1)

def handle_usr2(sig, frame):
    for adv_id, data in channels.items():
        child_pid = data["pid"]

        if child_pid is not None:
            os.kill(child_pid, signal.SIGUSR2)
def handle_mentor_quit(sig, frame):
    for adv_id, data in channels.items():
        child_pid = data["pid"]

        if child_pid is not None:
            os.kill(child_pid, signal.SIGQUIT)

def handle_mentor_tstp(sig, frame):
    for adv_id, data in channels.items():
        child_pid = data["pid"]

        if child_pid is not None:
            os.kill(child_pid, signal.SIGINT)
def handle_mentor(sig, frame):
    sys.stderr.write("\nMentor shutting down party...\n")
    for adv in adventurers:
        sys.stderr.write(f"{adv['name']} is at {adv['pos_r']}, {adv['pos_c']}\n") # 1. Print positions

    for adv_id, data in channels.items():  # 2. Kill children and wait
        child_pid = data["pid"]

        if child_pid is not None:
            os.kill(child_pid, signal.SIGINT)
            os.waitpid(child_pid, 0)
        
    sys.exit(0)
def main():
    parse_arguments()
    load_party_and_validate()
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
            ##os.dup2(adv_to_mentor_r, sys.stdin.fileno())  # Redirect stdin to read from the mentor
            ##os.dup2(adv_to_mentor_w, sys.stdout.fileno())  # Redirect stdout to write to the mentor
            os.dup2(mentor_to_adv_r,0) # Read from the Mentor (Command In)
            os.dup2(adv_to_mentor_w,1) # Write to the Mentor (Response Out)

            os.close(adv_to_mentor_w)  # Close the read end in the child
            os.close(adv_to_mentor_r)  # Close the write end in the child
            os.close(mentor_to_adv_w)
            os.close(mentor_to_adv_r)

            os.execl(sys.executable,"python3", "-u", "adventurer.py")
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
            # Save the child's PID into the global dictionary
            channels[adv_id]["pid"] = pid_adv
            os.close(adv_to_mentor_w)  # Close the read end in the child
            os.close(mentor_to_adv_r)  # Close the write end in the child
    signal.signal(signal.SIGUSR1, handle_usr1)
    signal.signal(signal.SIGUSR2, handle_usr2)
    signal.signal(signal.SIGQUIT, handle_mentor_quit)
    signal.signal(signal.SIGTSTP, handle_mentor_tstp)
    signal.signal(signal.SIGINT, handle_mentor)
    fifo_out_dm = open("mentor_to_dm.fifo", "w")
    fifo_in_dm = open("dm_to_mentor.fifo", "r")




    while True:
        try:
            choice = input("Enter command: ").strip()
            if not choice:
                continue
                
            choice = choice.lower()
            parts = choice.split()
            command = parts[0]

            # ---------------------------------------------------------
            # COMMAND: EXIT
            # ---------------------------------------------------------
            if command == "exit":
                fifo_out_dm.write("EXIT\n")
                fifo_out_dm.flush()
                # Send 'exit' command to all children
                for adv in adventurers:
                    fd_out = channels[adv["id"]]["cmd_out"]
                    os.write(fd_out, b"exit\n")
                
                # Wait for each adventurer to terminate and get exit status
                for adv in adventurers:
                    pid = channels[adv["id"]]["pid"]
                    _, status = os.waitpid(pid, 0)
                    exit_code = status >> 8
                    print(f"Adventurer {adv['id']} exited with status {exit_code}")
                    
                print("All adventurers have exited. Mentor exiting.")
                sys.exit(0)

            # ---------------------------------------------------------
            # COMMAND: PRINT (C-STYLE)
            # ---------------------------------------------------------
            elif command == "print":
                # Iterate through rows and columns explicitly
                for r in range(dungeon_dims[0]):
                    row_str = ""
                    for c in range(dungeon_dims[1]):
                        # Check if there is any adventurer at these coordinates
                        adv_here = False
                        for adv in adventurers:
                            if adv["pos_r"] == r and adv["pos_c"] == c:
                                adv_here = True
                                break # C-optimization: stop searching if found
                        
                        if adv_here:
                            row_str += "A"
                        else:
                            row_str += dungeon_map[r][c]
                    print(row_str)
                continue

            # =========================================================
            # TARGET PROCESSING (<id> or 'all') (C-STYLE)
            # =========================================================
            if len(parts) < 2:
                print("Error: Missing target (need 'all' or id).")
                continue
                
            target_str = parts[1]
            target_ids = []
            
            if target_str == "all":
                # Add all IDs one by one
                for adv in adventurers:
                    target_ids.append(adv["id"])
            else:
                try:
                    tid = int(target_str)
                    # Existence validation with a boolean flag
                    id_exists = False
                    for adv in adventurers:
                        if adv["id"] == tid:
                            id_exists = True
                            break
                    
                    if id_exists:
                        target_ids.append(tid)
                    else:
                        print("Error: Adventurer ID not found.")
                        continue
                except ValueError:
                    print("Error: Invalid ID format.")
                    continue

            # ---------------------------------------------------------
            # COMMAND EXECUTION BY TARGET
            # ---------------------------------------------------------
            for tid in target_ids:
                # 1. Retrieve the complete dictionary of the current adventurer
                current_adv = None
                for adv in adventurers:
                    if adv["id"] == tid:
                        current_adv = adv
                        break
                
                if command == "pos":
                    print(f"Adventurer {tid} position: ({current_adv['pos_r']}, {current_adv['pos_c']})")

                elif command == "health":
                    os.write(channels[tid]["cmd_out"], b"health\n")
                    resp = os.read(channels[tid]["resp_in"], 1024).decode('utf-8').strip()
                    print(f"Adventurer {tid} health: {resp}")

                elif command in ["petrify", "depetrify"]:
                    signum = signal.SIGTSTP if command == "petrify" else signal.SIGCONT
                    os.kill(channels[tid]["pid"], signum)
                    print(f"Sent {command.upper()} signal to Adventurer {tid}.")

                elif command == "unbox":
                    pos_tuple = (current_adv["pos_r"], current_adv["pos_c"])
                    if pos_tuple in opened_boxes:
                        print(f"Box at {pos_tuple} is already opened.")
                    else:
                        os.write(channels[tid]["cmd_out"], b"unbox\n")
                        resp = os.read(channels[tid]["resp_in"], 1024).decode('utf-8').strip()
                        print(f"Adventurer {tid} unbox result: {resp}")
                        if "OK" in resp:
                            opened_boxes.add(pos_tuple)

                elif command == "mv":
                    if len(parts) < 3:
                        print("Error: Missing direction for mv.")
                        continue
                    
                    direction = parts[2]
                    nr = current_adv["pos_r"]
                    nc = current_adv["pos_c"]
                    
                    # Calculate new theoretical position
                    if direction == "up": nr -= 1
                    elif direction == "down": nr += 1
                    elif direction == "left": nc -= 1
                    elif direction == "right": nc += 1
                    else:
                        print(f"Invalid direction: {direction}")
                        continue

                    # Boundary collision check
                    if not (0 <= nr < dungeon_dims[0] and 0 <= nc < dungeon_dims[1]):
                        print(f"Move failed for {tid}: Out of bounds.")
                        continue

                    # Wall collision check
                    if dungeon_map[nr][nc] == '#':
                        print(f"Move failed for {tid}: Wall collision.")
                        continue

                    # 2. Collision control with other adventurers
                    collision = False
                    for other in adventurers:
                        if other["pos_r"] == nr and other["pos_c"] == nc:
                            collision = True
                            break
                    
                    if collision:
                        print(f"Move failed for {tid}: Cell occupied by another adventurer.")
                        continue

                    # Send move command
                    cmd_str = f"mv {direction}\n"
                    os.write(channels[tid]["cmd_out"], cmd_str.encode('utf-8'))
                    
                    # Read response
                    resp = os.read(channels[tid]["resp_in"], 1024).decode('utf-8').strip()
                    
                    if resp.startswith("OK"):
                        current_adv["pos_r"] = nr
                        current_adv["pos_c"] = nc
                        # telling the DM the movement 
                        fifo_out_dm.write(f"MOVE {tid} {nr} {nc}\n")
                        fifo_out_dm.flush()
                        #wait for the repsonse from DM
                        dm_response = fifo_in_dm.readline().strip().split()
                        if not dm_response:
                            continue
                        dm_status = dm_response[0]
                        # 3. the DM response review
                        if dm_status == "HIT":
                            print(f"Monster attacked Adventurer {tid}!")
                            # deduct 10 health from ADV (with SIGINT)
                            os.kill(channels[tid]["pid"], signal.SIGINT)
                        elif dm_status == "KILLED":
                            print(f"Adventurer {tid} killed a monster!")
                        elif dm_status == "CLEAR":
                            print(f"Adventurer {tid} moved safely.")

                        # Update fog of war if there's discovered terrain
                        resp_parts = resp.split()
                        if len(resp_parts) > 1:
                            dungeon_map[nr][nc] = resp_parts[1]
                        print(f"Adventurer {tid} moved successfully.")
                    else:
                        print(f"Adventurer {tid} failed to move: {resp}")
                        dungeon_map[nr][nc] = '#'

                else:
                    print(f"Unknown command: {command}")
                    break 

        except (EOFError, KeyboardInterrupt):
            # Capture Ctrl+D or Ctrl+C to exit gracefully
            print("\nEmergency exit triggered.")
            break
        except Exception as e:
            # Prevents a typo or silly mistake from crashing the mentor
            print(f"Unexpected error processing command: {e}")

if __name__ == "__main__":
    main()