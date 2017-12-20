from Gameboard import *
from random import *


def clear():
    print "\n" * 100


directions = ['n', 'e', 's', 'w']


def handle(prompts, message, func=None, precondition=lambda *x: True, postcondition=True):
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
    def __init__(self):
        self.board = Board()
        self.ships = {"Carrier": 5, "Battleship": 4, "Cruiser": 3, "Submarine": 3, "Destroyer": 2}
        self.opposing_player = None

    def setup(self):
        pass

    def take_turn(self):
        pass

    def set_opponent(self, player):
        self.opposing_player = player
        player.opposing_player = self


class HumanPlayer(Player):
    def setup(self):
        for ship, size in self.ships.items():
            print(self.board)
            handle(["Select the location of (one end of) your {0} ({1}):\n".format(ship, size),
                    "Selection the direction of your {}:\n".format(ship)],
                   "Please choose a valid location and (cardinal) direction.",
                   lambda x, y: self.board.put_ship(size, x, y, ship))
            clear()

    def take_turn(self):
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
    def __init__(self):
        Player.__init__(self)
        self.mode = 'search'
        self.target = None
        self.target_direction = 'w'
        self.has_flipped = False
        self.sunken_ships = []

    def setup(self):
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
        if self.mode == 'search':
            while True:
                try:
                    # length = max(len(i[0]) for i in self.opposing_player.board.ships)
                    # loc = ntl[randint(1, 10)] + str(randint(1, 10))
                    # possible = any(filter(lambda x: all(map(lambda y: not self.board.nodes[y].is_hit, x)),
                    #                       self.opposing_player.board.neighborhoods(loc, length)))
                    node_probablities = {node: 0 for node in self.opposing_player.board.nodes.keys()}
                    for node in node_probablities.keys() :
                        if not self.opposing_player.board.nodes[node].is_hit:
                            for ship in self.opposing_player.board.ships:
                                node_probablities[node] += len(self.opposing_player.board.neighborhoods(node, len(ship)))
                    nodes = list(node_probablities.keys())
                    probs = list(node_probablities.values())
                    best_nodes = [node for node in nodes if probs[nodes.index(node)] == max(probs)]
                    # raw_input(str(best_nodes))
                    # print best_nodes
                    loc = choice(best_nodes)
                    # raw_input('wait')
                    # if not possible:
                    #     raise NodeError
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
                        self.target_direction = directions[(directions.index(self.target_direction) + 1) % 4]
                    sunken_ship = self.opposing_player.board.sink_ships()
                    if sunken_ship:
                        self.sunken_ships += sunken_ship[0]
                    break
                except (NodeError, KeyError, IndexError):
                    self.target_direction = directions[(directions.index(self.target_direction) + 1) % 4]
        else:
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
