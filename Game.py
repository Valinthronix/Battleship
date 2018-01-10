"""Game Running code

This module contains the main loop that runs the game, handling the turn taking system and choosing to play against
a computer or another human. The clear() method prints 100 blank lines, used to clear the screen.
"""

from Player import *


human = ["human", "person", "yes", "0"]
computer = ["computer", "ai", "cpu", "bot", "no", "1"]
yes = ["y", "yes", "1"]
no = ["n", "no", "0"]
player1 = HumanPlayer()
while True:
    start = handle(["Welcome to Battleship! Do you want to play against a human or a computer?"],
                   "Please choose human or computer.",
                   precondition=lambda x: True if x.lower() in human or x.lower() in computer else False)[1][0].lower()
    winner = None
    if start in human:
        player2 = HumanPlayer()
        player1.set_opponent(player2)
        clear()
        raw_input("It is Player 1's turn to place ships. Press Enter to continue.")
        player1.setup()
        clear()
        raw_input("It is Player 2's turn to place ships. Press Enter to continue")
        player2.setup()
        while True:
            clear()
            raw_input("It is Player 1's turn. Press Enter to continue")
            player1.take_turn()
            if not player2.board.ships:
                winner = "Player 1"
                break
            raw_input("Enemy Remaining Ships: " + ", ".join([ship[1] for ship in player2.board.ships]))
            clear()
            raw_input("It is Player 2's turn. Press Enter to continue")
            player2.take_turn()
            raw_input("Enemy Remaining Ships: " + ", ".join([ship[1] for ship in player1.board.ships]))
            if not player1.board.ships:
                winner = "Player 2"
                break
    else:
        clear()
        player2 = ComputerPlayer()
        player1.set_opponent(player2)
        player2.setup()
        raw_input("It is your turn to place ships. Press Enter to continue")
        player1.setup()
        while True:
            clear()
            raw_input("It is your turn. Press Enter to continue")
            player1.take_turn()
            if not player2.board.ships:
                winner = "You"
                break
            raw_input("Enemy Remaining Ships: " + ", ".join([ship[1] for ship in player2.board.ships]))
            player2.take_turn()
            if not player1.board.ships:
                winner = "The computer"
                break
    if winner == 'You':
        print "You win!"
    else:
        print(winner + " wins!")
    again = handle(["Do you want to play again?"], "Say yes or no.",
                   precondition=lambda x: True if x.lower() in yes else False)[1][0].lower()
    if again:
        player1 = HumanPlayer()
    else:
        break
    
