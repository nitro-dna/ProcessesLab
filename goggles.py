# Implementation of a class named GogglesSpell that receives the following arguments:
# filename - the name of the file that contains the dungeon information.
# The dungeon is a grid of squares.
# Within the file, the first line contains the dimensions of the dungeon (number of rows and columns).
# The second line the position of the exit stairwell
# The second line contains the number of obstacles and their positions.
# The third line contains the number of surprise boxes and their positions
# Example:
# 3 4 
# (0,3)
# 2 (1,1) (2,2) 
# 1 (0, 1)
# The dungeon has 3 rows and 4 columns and the exit stairwell is in position (0,3)
# There are 2 obstacles in positions (1,1) and (2,2)
# There is 1 surprise box in position (0,1)
#
# The class GogglesSpell exposes the following methods:
# print_dungeon() - prints the room
# dimensions() - returns the dimensions of the dungeon as a tuple (rows, columns)
# where_is_the_exit() - returns the position of the exit stairwell as a tuple (row, column)
# what_is_here(row, column) - returns the type of cell in the given position. The possible values are:
# '-' - empty cell
# 'E' - exit stairwell
# '#' - obstacle
# 'B' - surprise box
# type_of_box(row, column) - returns the type of the box in the given position. 
# The possible values are::
# 'MP' - mana potion. Augments the mana of the adventurer by 20 points
# 'MD' - mana drain. Reduces the mana of the adventurer by 10 points
# 'HP' - health potion. Augments the health of the adventurer by 20 points
# 'HD' - health drain. Reduces the health of the adventurer by 10 points
# 'G' - gold. Augments the gold of the adventurer by 10 coins

class GogglesSpell:
    def __init__(self, filename):
        self._filename = filename
        self._dungeon = []
        self._exit = None
        self._rows = -1
        self._columns = -1
        self._num_obstacles = -1
        self._obstacles = []
        self._num_boxes = -1
        self._boxes = []
        self._read_dungeon()

    # This method is internal of the class and called by the constructor
    # It should not be called within your code.
    def _read_dungeon(self):
        with open(self._filename, 'r') as file:
            lines = file.readlines()
            dimensions = lines[0].split()
            self._rows = int(dimensions[0])
            self._columns = int(dimensions[1])
            salida = lines[1].strip().replace('(', '').replace(')', '').split(',')
            self._exit = (int(salida[0]), int(salida[1]))
            
            obstacles = lines[2].split()
            self._num_obstacles = int(obstacles[0])
            boxes = lines[3].split()
            self._num_boxes = int(boxes[0])

            self._dungeon = []
            for i in range(self._rows):
                self._dungeon.append([])
                for j in range(self._columns):
                    self._dungeon[i].append('-')
                    if (i, j) == self._exit:
                        self._dungeon[i][j] = 'E'
            for i in range(1, len(obstacles)):
                obstacle = obstacles[i].replace('(', '').replace(')', '').split(',')
                row = int(obstacle[0])
                column = int(obstacle[1])
                self._dungeon[row][column] = '#'
                self._obstacles.append((row, column))
                
            for i in range(1, len(boxes)):
                box = boxes[i].replace('(', '').replace(')', '').split(',')
                row = int(box[0])
                column = int(box[1])
                self._dungeon[row][column] = 'B'
                self._boxes.append((row, column))
                
    # For testing purposes, you can use this method to print the dungeon. It is not part of the assignment and should not be used in your code.
    def print_dungeon(self):
        for row in self._dungeon:
            for cell in row:
                print(cell, end=' ')
            print()

    # Only to be used by the mentor
    def dimensions(self):
        return (self._rows, self._columns)

    # Only to be used by the mentor
    def where_is_the_exit(self):
        return self._exit

    # To be used by the adventurers at any time, but by the mentor only at the initialization of the room to check the position of the adventurers.
    # Calling this function cost to the adventurer 2 mana points, and it is only available if the adventurer has at least 2 mana points.
    def what_is_here(self, row, column):
        if row < 0 or row >= self._rows:
            return None
        if column < 0 or column >= self._columns:
            return None
        return self._dungeon[row][column]

    # The content of the surprise boxes are different each time this function is called, and it is randomly generated.
    # Calling this function has no cost for the adventurer.
    def type_of_box(self, row, column):
        if self._dungeon[row][column] != 'B':
            return None
        import random
        box_types = ['MP', 'MD', 'HP', 'HD', 'G']
        return random.choice(box_types)
