"""Human and Computer Player objects

This module contains the Player objects, which represent the players of the game. The Computer player is actually very
skilled, and will probably beat you. The handle function is special, it's used to handle user input.

"""

from Gameboard import *
from random import *


def clear():
    """Clears the screen by printing blank lines"""
    print "\n" * 100

directions = ['n', 'e', 's', 'w']
"""List of directions to assist iterating through directions. Ordered such that adding 1 mod 4 rotates clockwise, and
adding two reverses."""


def handle(prompts, message, func=None, precondition=lambda *x: True, postcondition=True):
    """Handles User Input
    
    This function attempts apply a function to given input (or just test the input), and throws a message back to the
    user and forces the user to enter new input if the function throws an error. The purpose of this is as a general way
    of handling user input; as part of my philosophy that the program should not crash regardless of user input, I use
    this function to instead force the user to retry whenever they enter bad input.
    
    The code for this evolved over time and is a little messy, a decent target for refactoring.
    
    Args:
        prompts (list of strings OR str): The prompt(s) that the user receives for their input
        message (str): The message that the user receives upon bad input
        func (func): The function that will be applied to the user input
        precondition (func): A test applied to the input
        postcondition (func): A test after the function is called
    
    Returns:
        If func is not None, then a tuple containing (the list of inputs, the return value of func(*inputs)). If func
        is None, then it's just a typle containing a list of the inputs twice, which is very lazy and should probably
        be refactored.
    """
    inputs = []
    if isinstance(prompts, list):
        for prompt in prompts:
            inputs.append(raw_input(prompt))
    else:
        inputs.append(raw_input(prompts))
    try:
        assert precondition(*inputs)
        if func:
            result = func(*inputs)
        else:
            result = inputs
        assert postcondition
        return inputs, result
    except (KeyError, IndexError, AssertionError, ShipError):
        print message
        return handle(prompts, message, func, precondition, postcondition)


class Player:
    """The abstract Player superclass for both humans and computers
    
    Attributes:
        board (Board): The player's board
        ships (dict): A dictionary of the player's ships corresponding to their sizes
        opposing_player (Player): The Player's opponent
    """
    def __init__(self):
        """Inits Player with a fresh Board, the standard 5 ships, and no opposing player."""
        self.board = Board()
        self.ships = {"Carrier": 5, "Battleship": 4, "Cruiser": 3, "Submarine": 3, "Destroyer": 2}
        self.opposing_player = None

    def setup(self):
        """Puts the Player's ships on their Board; implemented by subclasses"""
        pass

    def take_turn(self):
        """Fires on the opposing player's board; implemented by subclasses"""
        pass

    def set_opponent(self, player):
        """Sets the opposing player of both this Player the passed Player to each other"""
        self.opposing_player = player
        player.opposing_player = self


class HumanPlayer(Player):
    """Human Player object"""
    def setup(self):
        """Sets up the board by taking user input with the handle() function for location and direction"""
        for ship, size in self.ships.items():
            print(self.board)
            handle(["Select the location of (one end of) your {0} ({1}):\n".format(ship, size),
                    "Selection the direction of your {}:\n".format(ship)],
                   "Please choose a valid location and (cardinal) direction.",
                   lambda x, y: self.board.put_ship(size, x, y, ship))
            clear()

    def take_turn(self):
        """Takes user input for where to fire on, and reports the result"""
        clear()
        print(self.opposing_player.board.show())
        print(self.board)
        loc = handle(["Select a location to fire on!\n"], "Please choose a valid location.",
                     lambda x: self.opposing_player.board.nodes[x].hit())[0][0]
        clear()
        print(self.opposing_player.board.show())
        if self.opposing_player.board.nodes[loc].is_ship:
            print "A hit!!!!\n"
            raw_input("Press Enter to continue\n")
        else:
            print "A miss...\n"
            raw_input("Press Enter to continue\n")
        sunken_ship = self.opposing_player.board.sink_ships()
        if sunken_ship:
            print "You sunk the " + sunken_ship[1] + "!\n"
            raw_input("Press Enter to continue\n")
        else:
            pass


class ComputerPlayer(Player):
    """AI Player object
    
    This is probably the most complex part of the project. The AI is quite good, winning in an average of around 42
    moves, which is faster than most humans. It wins most of the time, but it is possible to beat it with a bit of luck.
    
    The AI is the main target for refactoring; in addition to just cleaning up the targeting code, it's possible to
    optimize that code even further as well as optimize the AI's ship placement instead of doing it randomly.
    
    Attributes:
        mode (str): A string representing the AI's targeting mode; either 'search', 'pinpoint', or 'destroy'.
        target (str): A string representing a location where the AI believes there to be a ship; used during pinpoint
                        and destroy modes
        target_direction (str): A string representing the direction the AI believes a ship to be in
        has_flipped (bool): A bool used during destroy that describes whether the AI has already reached one end of the
                    ship that it believes it is destroying
        self.sunken_ships (list of str): a list of all of the location that contain ships that have already been sunk
    """
    def __init__(self):
        """Inits the ComputerPlayer in search mode, with no target and target_direction 'w'."""
        Player.__init__(self)
        self.mode = 'search'
        self.target = None
        self.target_direction = 'w'
        self.has_flipped = False
        self.sunken_ships = []

    def setup(self):
        """Places the ComputerPlayer's ships on the board randomly, retrying ships placed in invalid locations"""
        for ship, size in self.ships.items():
            while True:
                try:
                    numloc = randint(1, 10)
                    letterloc = ntl[randint(1, 10)]
                    loc = letterloc + str(numloc)
                    direction = choice(directions)
                    self.board.put_ship(size, loc, direction, ship)
                    break
                except ShipError:
                    pass

    def take_turn(self):
        """Determines where to fire on the opposing player's Board and fires.
        
        This is the targeting code for the AI, the bulk of its complexity. It operates in three modes: search, pinpoint,
        and destroy. Search is used when it does not know the location of any of the opposing player's ships. When the
        AI gets a hit in that mode, it switches to pinpoint mode, which is used to determine the direction of the enemy
        ship. Once the AI believes it knows the direction, it switches into destroy mode, which is used to destroy the
        enemy ship. These modes are documented individually below.
        
        This is the prime target for refactoring. The code is messy and complex, and could probably be split into 4
        separate methods. That would probably allow us to move some of the object attributes (target, target_direction,
        and has_flipped) into the parameters for the new methods, which would be very clean.
        """
        if self.mode == 'search':
            """Search Mode
            
            The first step in search mode is to figure out the most likely locations to have a ship. This is done by
            iterating through every location on the opposing player's board, and using the length of the list returned
            by the neighborhood() method to get the total number of possible ships of a specific size that could be on
            that location, and summing that for every ship that the enemy player has remaining. We use this sum as the
            'probability score' for that location; by doing this for every location, we can create a dictionary of the
            scores for every node on the opposing player's board.
            
            Then, the AI chooses randomly from locations with the maximum 'scores' and fires upon it. If it hits, then
            it moves into pinpoint mode and assigned self.target to the location that it hit.
            
            This can be optimized for speed by storing the probability score dictionary, and only updating the values
            that change when it fires, rather than recalculating every location each time.
            """
            while True:
                try:
                    node_probablities = {node: 0 for node in self.opposing_player.board.nodes.keys()}
                    for node in node_probablities.keys() :
                        if not self.opposing_player.board.nodes[node].is_hit:
                            for ship in self.opposing_player.board.ships:
                                node_probablities[node] += len(self.opposing_player.board.neighborhoods(node, len(ship)))
                    nodes = list(node_probablities.keys())
                    probs = list(node_probablities.values())
                    best_nodes = [node for node in nodes if probs[nodes.index(node)] == max(probs)]
                    loc = choice(best_nodes)
                    self.opposing_player.board.nodes[loc].hit()
                    if self.opposing_player.board.nodes[loc].is_ship:
                        self.mode = 'pinpoint'
                        self.target = loc
                    sunken_ship = self.opposing_player.board.sink_ships()
                    if sunken_ship:
                        self.sunken_ships += sunken_ship[0]
                    break
                except NodeError:
                    pass
        elif self.mode == 'pinpoint':
            """Pinpoint Mode
            
            This mode fires in a circle around a specific other location (self.target), attempting to determine the
            direction of the ship that has been hit. Once it does, it sets that to self.target_direction and goes into
            destroy mode. 
            
            This could be refactored using the adjacent() function; the code was written before that function.
            """
            while True:
                try:
                    loc = self.target
                    if self.target_direction == 'n':
                        loc = ntl[ltn[loc[0]] - 1] + loc[1:]
                    elif self.target_direction == 's':
                        loc = ntl[ltn[loc[0]] + 1] + loc[1:]
                    elif self.target_direction == 'e':
                        loc = loc[0] + str(int(loc[1:]) + 1)
                    else:
                        loc = loc[0] + str(int(loc[1:]) - 1)
                    # loc = adjacent(self.target, self.target_direction)
                    self.opposing_player.board.nodes[loc].hit()
                    if self.opposing_player.board.nodes[loc].is_ship:
                        self.mode = 'destroy'
                    else:
                        # rotate self.target_direction clockwise
                        self.target_direction = directions[(directions.index(self.target_direction) + 1) % 4]
                    sunken_ship = self.opposing_player.board.sink_ships()
                    # sunken_ship is None unless it sinks a ship that turn
                    if sunken_ship:
                        self.sunken_ships += sunken_ship[0]
                    break
                except (NodeError, KeyError, IndexError):
                    self.target_direction = directions[(directions.index(self.target_direction) + 1) % 4]
        else:
            """Destroy Mode:
            
            This mode is active only when the AI believes that it knows the location and direction of a ship. It fires
            along that direction, and reverses direction if it misses or fails. If it sinks a ship, or if it misses when
            it has already reversed direction, then it checks to see whether there are any nodes that are ships and have
            been hit but are not part of a sunken ship. If there are, it chooses one as self.target and goes into
            pinpoint mode; if not, then it goes back into search mode.
            
            This could also be refactored to make use of adjacent(), as well as cleaned up a lot in general.
            """
            while True:
                try:
                    # set loc to the adjacent location to self.target
                    loc = self.target
                    if self.target_direction == 'n':
                        loc = ntl[ltn[loc[0]] - 1] + loc[1:]
                    elif self.target_direction == 's':
                        loc = ntl[ltn[loc[0]] + 1] + loc[1:]
                    elif self.target_direction == 'e':
                        loc = loc[0] + str(int(loc[1:]) + 1)
                    else:
                        loc = loc[0] + str(int(loc[1:]) - 1)
                    if not self.opposing_player.board.nodes[loc].hide().is_hit:
                        self.opposing_player.board.nodes[loc].hit()
                        if not (self.opposing_player.board.nodes[loc].is_ship or self.has_flipped):
                            self.target_direction = directions[(directions.index(self.target_direction) + 2) % 4]
                            self.has_flipped = True
                        elif not self.opposing_player.board.nodes[loc].is_ship and self.has_flipped:
                            self.target_direction = directions[(directions.index(self.target_direction) + 1) % 4]
                            self.has_flipped = False
                        sunken_ship = self.opposing_player.board.sink_ships()
                        if sunken_ship:
                            self.has_flipped = False
                            self.sunken_ships += sunken_ship[0]
                            targets = filter(lambda x: x not in self.sunken_ships and self.opposing_player.board.nodes[
                                x].hide().is_ship,
                                             self.opposing_player.board.nodes.keys())
                            if targets:
                                self.target = choice(targets)
                            else:
                                self.mode = 'search'
                        break
                    elif self.opposing_player.board.nodes[loc].hide().is_ship:
                        self.target = loc
                    else:
                        raise KeyError
                        # print self.opposing_player.board
                except (KeyError, IndexError):
                    if self.has_flipped:
                        targets = filter(
                            lambda x: x not in self.sunken_ships and self.opposing_player.board.nodes[x].hide().is_ship,
                            self.opposing_player.board.nodes.keys())
                        self.has_flipped = False
                        if targets:
                            self.target = choice(targets)
                            self.mode = "pinpoint"
                            self.take_turn()
                            break
                        else:
                            self.mode = 'search'
                            self.take_turn()
                            break
                    else:
                        # flips direction
                        self.target_direction = directions[(directions.index(self.target_direction) + 2) % 4]
                        self.has_flipped = True


# d = []
# for i in range(50):
#     a = ComputerPlayer()
#     b = ComputerPlayer()
#     a.set_opponent(b)
#     a.setup()
#     b.setup()
#     c = 0
#     try:
#         for j in range(99):
#             a.take_turn()
#             c += 1
#             assert b.board.ships
#         print b.board.ships
#         print b.board
#     except AssertionError:
#         d.append(c)
# print d
# print sum(d) / float(len(d))
