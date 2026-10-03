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
    