import os, sys, goggles

# Global variables for the Mentor
dungeon_file = ""
monsters_file = ""
monsters = []
FIFO_M2DM = "mentor_to_dm.fifo"
FIFO_DM2M = "dm_to_mentor.fifo"

def parse_arguments():
    global dungeon_file, monsters_file
    i = 1
    while i< len(sys.argv):
        arg = sys.argv[i]
        if arg == '-dungeon':
            dungeon_file = sys.argv[i+1]
            i +=2
        elif arg == '-monsters':
            monsters_file = sys.argv[i+1]
            i += 2
    if not dungeon_file or not monsters_file:
        sys.stderr.write("Error: -dungeon und -monsters must be given.\n")
        sys.exit(1)

def load_monster():
    global dungeon_file, monsters_file, monsters
    current_id = 1
    try:
        with open(monsters_file, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                clean_line = line.replace('(', ''). replace(')', '').replace(',',' ') 
                parts = clean_line.split()
                # transform data
                pos_r = int(parts[0])
                pos_c = int(parts[1])
                health = int(parts[2])
                name = " ".join(parts[3:])

                monster_data = {
                    "id": current_id,
                    "name": name,
                    "pos_r": pos_r,
                    "pos_c": pos_c,
                    "health": health
                }
                monsters.append(monster_data)
                current_id += 1
    except OSError as e:
        sys.stderr.write(f"Error while opening the monsters file: {e}\n")
        sys.exit(1)
    # validate with the sensor 
    sensor = goggles.GogglesSpell(dungeon_file)

    for m in monsters:
        pos_r = m["pos_r"]
        pos_c = m["pos_c"]

        if sensor.what_is_here(pos_r, pos_c) == '#':
            sys.stderr.write(f"Error: monster{m['name']} just spawned in a Wall at position:({pos_r}, {pos_c}).\n")
            sys.exit(1)


def setup_fifos():
    global monsters
    
    # 1. Turn off Linux security filter to apply true 0o666 permissions
    original_umask = os.umask(0)
    
    # Initial cleanup in case the program crashed in a previous run
    if os.path.exists(FIFO_M2DM):
        os.unlink(FIFO_M2DM)
    if os.path.exists(FIFO_DM2M):
        os.unlink(FIFO_DM2M)
    
    # Create FIFOs with universal permissions
    os.mkfifo(FIFO_M2DM, 0o666)
    os.mkfifo(FIFO_DM2M, 0o666)
    
    # Restore the security filter as a good practice
    os.umask(original_umask)

    try:
        print("DM: Waiting for Mentor connection...")
        
        # 2. BLOCKING OPEN (Careful with the opening order in the Mentor)
        # The Mentor MUST execute: fifo_out = open(FIFO_M2DM, 'w') BEFORE opening the other pipe.
        fifo_in = open(FIFO_M2DM, 'r')
        fifo_out = open(FIFO_DM2M, 'w')
        
        print("DM: Mentor connected. Starting game.")

        while True:
            line = fifo_in.readline()
            if not line:
                break
                
            parts = line.strip().split()
            if not parts:
                continue
                
            command = parts[0]
            
            if command == "EXIT":
                print("DM: Exit command received. Closing dungeon...")
                break
                
            elif command == "MOVE":
                if len(parts) < 4:
                    continue # Protection against malformed commands
                    
                adv_id = parts[1]
                pos_r = int(parts[2])
                pos_c = int(parts[3])
                
                monster_found = False
                
                # loop to search for the monster
                for m in monsters:
                    if m["pos_r"] == pos_r and m["pos_c"] == pos_c:
                        m["health"] -= 10
                        if m["health"] <= 0:
                            fifo_out.write(f"KILLED {adv_id}\n")
                            fifo_out.flush()
                            monsters.remove(m)
                        else:
                            fifo_out.write(f"HIT {adv_id}\n")
                            fifo_out.flush()
                        
                        monster_found = True
                        break # Found, stop searching
                        
                if not monster_found:
                    fifo_out.write(f"CLEAR {adv_id}\n")
                    fifo_out.flush()
                    
    finally:
        # 3. ABSOLUTE CLEANUP
        # This block ALWAYS executes, even if the program crashes due to an error
        print("DM: Cleaning pipes from disk...")
        try:
            fifo_in.close()
            fifo_out.close()
        except:
            pass
            
        if os.path.exists(FIFO_M2DM):
            os.unlink(FIFO_M2DM)
        if os.path.exists(FIFO_DM2M):
            os.unlink(FIFO_DM2M)      

def main():
    parse_arguments()
    load_monster()
    setup_fifos()

if __name__ == "__main__":
    main()