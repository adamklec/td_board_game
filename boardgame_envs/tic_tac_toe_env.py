import numpy as np
from .board_game_env_base import BoardGameEnvBase, BoardBase
from agents.random_agent import RandomAgent
from collections import Counter
from copy import deepcopy
from random import choice, random


class TicTacToeEnv(BoardGameEnvBase):
    def __init__(self, random_position=False):
        self.board = TicTacToeBoard()
        self.random_position = random_position

    def reset(self, board=None):
        if board is None:
            self.board = TicTacToeBoard()
            if self.random_position:
                if random() < .5:
                    for _ in range(2):
                        legal_moves = self.get_legal_moves()
                        move = choice(legal_moves)
                        self.make_move(move)
        else:
            self.board = board

    def get_board(self):
        return self.board

    def get_null_move(self):
        return None

    def get_move_stack(self):
        return self.board.move_stack

    def get_reward(self, board=None):
        if board is None:
            board = self.board
        return board.result()

    def make_move(self, move):
        assert move in self.get_legal_moves()
        self.board.push(move)

    def get_legal_moves(self, board=None):
        if board is None:
            board = self.board
        return board.legal_moves

    def make_feature_vector(self, board=None):
        if board is None:
            board = self.board
        fv = np.zeros((1, 28))
        fv[0, :9] = board.xs.reshape(9)
        fv[0, 9:18] = board.os.reshape(9)
        fv[0, 18:27] = ((board.xs + board.os).reshape(9) == 0).astype(float)
        fv[0, -1] = float(board.turn)
        return fv

    def _print(self, board=None):
        if board is None:
            board = self.board
        s = ''
        for i in range(3):
            s += ' '
            for j in range(3):
                if board.xs[i, j] == 1:
                    s += 'X'
                elif board.os[i, j] == 1:
                    s += 'O'
                else:
                    s += ' '
                if j < 2:
                    s += '|'
            s += '\n'
            if i < 2:
                s += '-------\n'
        print(s)

    def play(self, players, verbose=False):
        while self.get_reward() is None:
            if verbose:
                self._print()
            player = players[int(self.board.turn)]
            move = player.get_move(self)
            self.make_move(move)

        reward = self.get_reward()
        if verbose:
            self._print()
            if reward == 1:
                print("X won!")
            elif reward == -1:
                print("O won!")
            else:
                print("draw")
        return self.get_reward()

    def play_random(self, get_move_function, side):
        self.reset()
        random_agent = RandomAgent()
        if side:
            move_functions = [random_agent.get_move, get_move_function]  # True == 1 == 'X'
        else:
            move_functions = [get_move_function, random_agent.get_move]

        while self.get_reward() is None:
            move_function = move_functions[int(self.board.turn)]
            move = move_function(self)
            self.make_move(move)

        reward = self.get_reward()

        return reward

    def play_self(self, get_move_function):
        self.reset()
        while self.get_reward() is None:
            move = get_move_function(self)
            self.make_move(move)

        reward = self.get_reward()

        return reward

    def test(self, get_move_function, test_idx):
        x_counter = Counter()
        for _ in range(100):
            self.reset()
            reward = self.play_random(get_move_function, True)
            x_counter.update([reward])

        o_counter = Counter()
        for _ in range(100):
            self.reset()
            reward = self.play_random(get_move_function, False)
            o_counter.update([reward])

        return [x_counter[1], x_counter[0], x_counter[-1], o_counter[1], o_counter[0], o_counter[-1]]

    def get_feature_vector_size(self):
        return self.make_feature_vector().shape[1]

    def get_simple_value_weights(self):
        fv_size = self.get_feature_vector_size()
        return np.zeros((fv_size, 1))

    @staticmethod
    def is_quiet(board):
        return True

    @staticmethod
    def move_order_key(board, ttable):
        return 0


class TicTacToeBoard(BoardBase):
    def __init__(self, fen=None):
        super().__init__()

        self.xs = np.zeros((3, 3))
        self.os = np.zeros((3, 3))
        self._legal_moves = np.arange(9)
        self._turn = True
        self.move_stack = []

        if fen is not None:
            assert len(fen) == 9
            for i, char in enumerate(fen):
                row = int(i / 3)
                col = i % 3
                if char == 'X':
                    self.xs[row, col] = 1
                elif char == 'O':
                    self.xs[row, col] = 1
                else:
                    assert char == '-'
            self._turn = bool((self.xs.sum() + self.os.sum()) % 2)

    @property
    def turn(self):
        return self._turn

    @property
    def legal_moves(self):
        return self._legal_moves

    def fen(self):
        fen = ''
        for pair in zip(self.xs.reshape(9), self.os.reshape(9)):
            assert not (pair[0] and pair[1])
            if pair[0]:
                fen += 'X'
            elif pair[1]:
                fen += 'O'
            else:
                fen += '-'
        return fen

    def push(self, move):
        row = int(move / 3)
        col = move % 3

        assert self.xs[row, col] == 0
        assert self.os[row, col] == 0
        if self.turn:
            self.xs[row, col] = 1
        else:
            self.os[row, col] = 1
        self.move_stack.append(3 * row + col)
        self._turn = not self._turn
        self._legal_moves = np.where((self.xs + self.os).reshape(9) == 0)[0]

    def pop(self):
        move = self.move_stack[-1]
        self.move_stack = self.move_stack[:-1]

        row = int(move / 3)
        col = move % 3

        self.xs[row, col] = 0
        self.os[row, col] = 0

        return move

    def is_game_over(self):
        return self.result() is not None

    def result(self):
        if any(self.xs.sum(axis=0) == 3) or any(self.xs.sum(axis=1) == 3) or self.xs[np.eye(3) == 1].sum() == 3 or self.xs[np.rot90(np.eye(3)) == 1].sum() == 3:
            return 1.0
        elif any(self.os.sum(axis=0) == 3) or any(self.os.sum(axis=1) == 3) or self.os[np.eye(3) == 1].sum() == 3 or self.os[np.rot90(np.eye(3)) == 1].sum() == 3:
            return -1.0
        elif (self.xs + self.os).sum() == 9:
            return 0.0
        else:
            return None

    def zobrist_hash(self):
        return self.fen()

    def copy(self):
        return deepcopy(self)
