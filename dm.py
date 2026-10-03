import os, sys, goggles

# Global variables for the Mentor
dungeon_file = ""
monsters_file = ""
monsters = []
FIFO_MENTOR_TO_DM = "fifo_m2dm"
FIFO_DM_TO_MENTOR = "fifo_dm2m"

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
    global dungeon_file, monsters_file
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
    sensor = goggles.GogglesSpell(monsters_file)

    for m in monsters:
        pos_r = m["pos_r"]
        pos_c = m["pos_c"]

        if sensor.what_is_here(pos_r, pos_c) == '#':
            sys.stderr.write(f"Error: monster{m['name']} just spawned in a Wall at position:({pos_r}, {pos_c}).\n")
            sys.exit(1)


