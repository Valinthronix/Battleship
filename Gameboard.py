# coding=utf-8


def adjacent(location, direction):
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




class Node:
    def __init__(self, ship=False, hit=False):
        self.is_ship = ship
        self.is_hit = hit

    def hit(self):
        if not self.is_hit:
            self.is_hit = True
            return True
        else:
            raise NodeError

    def __str__(self):
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
        if self.is_hit:
            return self
        else:
            return Node()


class ShipError(Exception):
    pass


class NodeError(ShipError):
    pass


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





class Board:
    def __init__(self):
        nodes = []
        for letter in "abcdefghij":
            for number in range(10):
                nodes.append(letter + str(number + 1))
        for index, item in enumerate(nodes):
            nodes[index] = (item, Node())
        self.nodes = dict(nodes)
        self.ships = []

    def __str__(self):
        boardstring = u'   1   2   3   4   5   6   7   8   9   10'.encode('utf-8')
        for letter in "abcdefghij":
            line = "\n" + letter
            for i in range(10):
                line += " " + str(self.nodes[letter + str(i + 1)])
            boardstring += line
        return boardstring

    def put_carrier(self, location, direction):
        self.put_ship(5, location, direction)

    def neighborhoods(self, location, size):
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
        east = ["E", "EAST", "RIGHT", "R"]
        west = ["W", "WEST", "LEFT", "L"]
        north = ["N", "NORTH", "UP", "U"]
        south = ["S", "SOUTH", "DOWN", "D"]
        ship = []
        location = location.lower()
        try:
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
            raise ShipError

    def fire(self, node):
        self.nodes[node].hit()

    def sink_ships(self):
        for ship in self.ships:
            if filter(lambda node: self.nodes[node].is_hit, ship[0]) == ship[0]:
                self.ships.remove(ship)
                return ship
        return None

    def show(self):
        boardstring = u'   1   2   3   4   5   6   7   8   9   10'.encode('utf-8')
        for letter in "abcdefghij":
            line = "\n" + letter
            for i in range(10):
                line += " " + str(self.nodes[letter + str(i + 1)].hide())
            boardstring += line
        return boardstring

# a = Board()
# a.put_ship(4, "b9", 'S', "Carrier")
# a.fire("d2")
# print a
# print a.sink_ships()
# print a.ships
