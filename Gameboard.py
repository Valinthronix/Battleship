# coding=utf-8
"""Gameboard objects

This file contains all of the battleship game mechanics code
It includes the board objects, node objects, and a helper method to determine the adjacent node in a given direction

A good possibility for refactoring is to add a Ship class; I have a couple inconsistent ways of representing them
throughout my code, and it would be an improvement to streamline that.

"""


class Node:
    """Gameboard Node object
    
    Attributes:
        is_ship (bool): Whether the node contains a part of a ship
        is_hit (bool): Whether the node has been fired upon
    """
    def __init__(self, ship=False, hit=False):
        """Inits Node with default False for both is_ship and is_hit"""
        self.is_ship = ship
        self.is_hit = hit

    def hit(self):
        """Node firing method
        
        Attempts to fire on the node, setting self.is_hit to True
        
        Returns:
            True if not already hit, else raises a NodeError
        """
        if not self.is_hit:
            self.is_hit = True
            return True
        else:
            raise NodeError

    def __str__(self):
        """Very dependent on certain Unicode character widths, which can be different in different environments"""
        if self.is_ship:
            if self.is_hit:
                return u'☒'.encode('utf-8')
            else:
                return u'☐'.encode('utf-8')
        else:
            if self.is_hit:
                return u'○'.encode('utf-8')
            else:
                return u' 🞄 '.encode('utf-8')

    def hide(self):
        """Node hiding function
        
        Used to hide unrevealed Nodes for the opposing player.
        
        Returns:
            self if self.is_hit, else a blank Node()
        """
        if self.is_hit:
            return self
        else:
            return Node()


class ShipError(Exception):
    pass

class NodeError(ShipError):
    pass
"""My own errors; used to simplify some try-except control flow but largely unnecessary.
Should probably refactor and remove."""


ltn = {'a': 1,
       'b': 2,
       'c': 3,
       'd': 4,
       'e': 5,
       'f': 6,
       'g': 7,
       'h': 8,
       'i': 9,
       'j': 10}

ntl = ' abcdefghij'
""" Helper objects for translating numbers to letters and back, used specifcally in the adjacent function below"""


def adjacent(location, direction):
    """Adjacent Node function
    
    Args:
        location (str): The given location, as a string
        direction (str): The given direction, as a string of a single lowercase character as a cardinal direction
    
    Returns:
        A string representing the location adjacent to the given location in the given direction.
    """
    longi = int(location[1:])
    lati = ltn[location[0]]
    if direction == 'n':
        lati = lati - 1
        if lati < 1:
            raise NodeError
    elif direction == 's':
        lati = lati + 1
        if lati > 10:
            raise NodeError
    elif direction == 'e':
        longi = longi + 1
        if longi > 10:
            raise NodeError
    else:
        longi = longi - 1
        if longi < 1:
            raise NodeError
    return ntl[lati] + str(longi)

class Board:
    """Game Board object
    
    Attributes:
        nodes (dict): A dictionary containing every location on the board as keys which correspond to a Node value
        ships (list): A list of the ships contained on the board, represented
            as a 2-tuple ([list of locations of ship], "string name of ship")
    """
    def __init__(self):
        """Inits Board with blank Nodes for the standard a-j and 1-10 battleship gameboard and no ships on the board."""
        nodes = []
        for letter in "abcdefghij":
            for number in range(10):
                nodes.append(letter + str(number + 1))
        for index, item in enumerate(nodes):
            nodes[index] = (item, Node())
        self.nodes = dict(nodes)
        self.ships = []

    def __str__(self):
        """Used to display the gameboard
        
        Ridiculously sensitive to Unicode character widths; there's actually two different kinds of spaces used
        in that initial boardstring to make everything line up. One is extremely narrow.
        """
        boardstring = u'   1   2   3   4   5   6   7   8   9   10'.encode('utf-8')
        for letter in "abcdefghij":
            line = "\n" + letter
            for i in range(10):
                line += " " + str(self.nodes[letter + str(i + 1)])
            boardstring += line
        return boardstring

    def neighborhoods(self, location, size):
        """Collects all of the valid neighborhoods of a specific size around a given location.
        
        A neighborhood is defined as a list of location strings that are in either a vertical or horizontal row (meaning
        that they all have either the same number or letter) and include a specific given location.
        This is used in the AI player code, but lives within the Board class because its return value is determined
        exclusively by Board attributes, namely, what Nodes have already been hit. This information could be exposed to 
        the player, too, in the future. It's important for the AI to determine the most likely location on the board to
        have a ship.
        
        Args:
            location (str): The location to collect neighborhoods of
            size (int): The size of neighborhoods to collect
            
        Returns:
            A list containing all of the valid neighborhoods of the given location at the given size
        """
        neighbors = {'n': [], 'e': [], 's': [], 'w': []}
        for direction in ['n', 'e', 's', 'w']:
            for i in range(size):
                candidate = location
                skip = False
                for j in range(i):
                    skip = False
                    try:
                        candidate = adjacent(candidate, direction)
                        assert not self.nodes[candidate].is_hit
                    except (NodeError, AssertionError):
                        skip = True
                if not skip:
                    neighbors[direction].append(candidate)
        vert = neighbors['n'][:0:-1] + neighbors['s']
        hori = neighbors['w'][:0:-1] + neighbors['e']
        lists = []
        for i in range(len(vert) - size + 1):
            lists.append(vert[i:i + size])
        for i in range(len(hori) - size + 1):
            lists.append(hori[i:i + size])
        return lists

    def put_ship(self, size, location, direction, name):
        """Places a ship on the Board
        
        If attempting to place an invalid ship (that goes off the board or overlaps another ship), raises ShipError
        
        Args:
            size (int): Size of ship to place
            location (str): String representing location of one end of the ship being placed
            direction (str): String representing direction of ship to place
            name (str): Name of ship being placed
        """
        # These directions should probably be outside of this method; used to handle various ways of writing directions
        east = ["E", "EAST", "RIGHT", "R"]
        west = ["W", "WEST", "LEFT", "L"]
        north = ["N", "NORTH", "UP", "U"]
        south = ["S", "SOUTH", "DOWN", "D"]
        ship = []
        location = location.lower()
        try:
            # This is very messy, an extremely good target for refactoring using the adjacent function
            #       (the adjacent function was written after this code)
            # The basic idea is that we iterate location by location, along the direction given at the place given
            # Testing whether each location is a valid place to put a ship
            # If we ever run into an exception, then the ship placement is invalid, so we raise ShipError
            # If we don't, then we iterate through again, placing the ship this time.
            if direction.upper() in east:
                assert (self.nodes[location[0] + str(int(location[1:]) + size - 1)])
                for i in range(int(location[1:]), int(location[1:]) + size):
                    assert (self.nodes[location[0] + str(i)].is_ship is False)
                for i in range(int(location[1:]), int(location[1:]) + size):
                    self.nodes[location[0] + str(i)].is_ship = True
                    ship.append(location[0] + str(i))
            elif direction.upper() in west:
                assert (self.nodes[location[0] + str(int(location[1:]) - size + 1)])
                for i in range(int(location[1:]) - size + 1, int(location[1:]) + 1):
                    assert (self.nodes[location[0] + str(i)].is_ship is False)
                for i in range(int(location[1:]) - size + 1, int(location[1:]) + 1):
                    self.nodes[location[0] + str(i)].is_ship = True
                    ship.append(location[0] + str(i))
            elif direction.upper() in north:
                length = ntl[ltn[location[0]] - size + 1]
                assert (ltn[location[0]] - size + 1 > 0)
                assert (self.nodes[length + location[1:]])
                for i in range(size):
                    assert (self.nodes[ntl[ltn[location[0]] - i] + location[1:]].is_ship is False)
                for i in range(size):
                    self.nodes[ntl[ltn[location[0]] - i] + location[1:]].is_ship = True
                    ship.append(ntl[ltn[location[0]] - i] + location[1:])
            elif direction.upper() in south:
                length = ntl[ltn[location[0]] + size - 1]
                assert (ltn[location[0]] + size - 1 < 11)
                assert (self.nodes[length + location[1:]])
                for i in range(size):
                    assert (self.nodes[ntl[ltn[location[0]] + i] + location[1:]].is_ship is False)
                for i in range(size):
                    self.nodes[ntl[ltn[location[0]] + i] + location[1:]].is_ship = True
                    ship.append(ntl[ltn[location[0]] + i] + location[1:])
            else:
                assert False
            self.ships.append((ship, name))
        except (AssertionError, KeyError, IndexError):
            # We raise a KeyError going off the board in one direction, and an IndexError the other, due to the ntl and
            # ltn objects being a string and a dictionary.
            # The AssertionError arrises from a location that already contains a ship.
            raise ShipError

    def fire(self, node):
        self.nodes[node].hit()

    def sink_ships(self):
        """Removes and returns a ship from the Board if every part has been sunk"""
        for ship in self.ships:
            if filter(lambda node: self.nodes[node].is_hit, ship[0]) == ship[0]:
                self.ships.remove(ship)
                return ship
        return None

    def show(self):
        """Displays the game Board, with unrevealed nodes hidden for the opposing player"""
        boardstring = u'   1   2   3   4   5   6   7   8   9   10'.encode('utf-8')
        for letter in "abcdefghij":
            line = "\n" + letter
            for i in range(10):
                line += " " + str(self.nodes[letter + str(i + 1)].hide())
            boardstring += line
        return boardstring


# Code used to test this module

# a = Board()
# a.put_ship(4, "b9", 'S', "Carrier")
# a.fire("d2")
# print a
# print a.sink_ships()
# print a.ships
