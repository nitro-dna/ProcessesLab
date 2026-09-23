# Test the GogglesSpell class
# This program uses the GogglesSpell class to read the dungeon information from a file and print the dungeon.
# The program reads the filename from the command line and creates an instance of the GogglesSpell class with the filename.
# The program calls the _read_dungeon() method to read the dungeon information from the file.
# The program calls the print_dungeon() method to print the dungeon.
# The program should be executed from the command line as follows:
# python test.py level_one.txt
# or
# python test.py level_two.txt

import sys
import goggles

def main():
    if len(sys.argv) != 2:
        print(f'Usage: python {sys.argv[0]} filename')
        sys.exit(1)
    filename = sys.argv[1]
    magic_goggles = goggles.GogglesSpell(filename)

    # this method cannot be invoked by the master or the robot
    # it is only "for us"
    magic_goggles.print_dungeon()
    
    #methods that can be used only by the master
    print(f'dimensions of the dungeon: {magic_goggles.dimensions()}')
    print(f'exit position: {magic_goggles.where_is_the_exit()}')

    # checking a position: this methods are only meant for the robots
    # the master can use them only at the beginning to check if the
    # initial position of a robot contains an obstacle or a treasure
    my_row=2
    my_col=3

    # Calling this function cost to the adventurer 2 mana points, and it is only available if the adventurer has at least 2 mana points.
    what_is_at_my_position  = magic_goggles.what_is_here(my_row, my_col)

    print(f'what is here at ({my_row}, {my_col}): {what_is_at_my_position}')

    # The type of surprise box is different each time this function is called, and it is randomly generated.
    # The adventurer can call this function each time he/she finds a surprise box, and it has no cost for the adventurer.
    # but only once per each time he/she reaches a surprise box. The adventurer cannot call this function if he/she is not at a position with a surprise box.

    if what_is_at_my_position == 'B':
        print(f'type of box at ({my_row}, {my_col}): {magic_goggles.type_of_box(my_row, my_col)}')



if __name__ == '__main__':
    main()
