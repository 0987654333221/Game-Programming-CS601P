import os
import time
import keyboard
try:
    from colorama import init
    init(autoreset=True)
except:
    pass

T_FLOOR  = '🟩'
T_WALL   = '🧱'
T_OBS    = '🌲'
T_BLOCK  = '📦'
T_LOCKED = '✅'
T_SPOT   = '❎'
T_EXIT   = '🚪'
T_P1     = '🐱'
T_P2     = '🐶'


class GameState:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.p1_x = 2
        self.p1_y = 2
        self.p2_x = width - 3
        self.p2_y = height - 3
        self.p1_hold_active = False
        self.p2_hold_active = False
        self.objects = {}
        self.puzzle_spots = {}
        self.obstacles = {}
        self.exit_pos = None
        self.time_remaining = 0
        self.level_complete = False
        self.time_up = False
        self.message = ""

    def _get_hold_axis(self, player):
        """
        Returns 'h' (horizontal) or 'v' (vertical) depending on which side
        of an adjacent *unlocked* block the player is standing on.
        Returns None if not adjacent to any moveable block.
        """
        px, py = (self.p1_x, self.p1_y) if player == 1 else (self.p2_x, self.p2_y)
        for obj in self.objects.values():
            if obj.get('locked'):
                continue
            ox, oy = obj['x'], obj['y']
            if oy == py and abs(ox - px) == 1:
                return 'h'
            if ox == px and abs(oy - py) == 1:
                return 'v'
        return None

    def can_move(self, player, direction):
        hold_active = self.p1_hold_active if player == 1 else self.p2_hold_active
        if not hold_active:
            return True 

        px, py = (self.p1_x, self.p1_y) if player == 1 else (self.p2_x, self.p2_y)
        if self.exit_pos:
            ex, ey = self.exit_pos
            dx, dy = {'up': (0,-1), 'down': (0,1),
                      'left': (-1,0), 'right': (1,0)}[direction]
            if px + dx == ex and py + dy == ey:
                return True

        axis = self._get_hold_axis(player)
        if axis is None:
            return True 
        if axis == 'h' and direction in ('left', 'right'):
            return True
        if axis == 'v' and direction in ('up', 'down'):
            return True
        return False


class Map:
    def __init__(self, width, height, extra_walls=None):
        self.width = width
        self.height = height
        self.walls = self._create_border()
        if extra_walls:
            self.walls.update(extra_walls)

    def _create_border(self):
        walls = set()
        for x in range(self.width):
            walls.add((x, 0))
            walls.add((x, self.height - 1))
        for y in range(self.height):
            walls.add((0, y))
            walls.add((self.width - 1, y))
        return walls

    def is_passable(self, x, y):
        return (0 <= x < self.width and 0 <= y < self.height
                and (x, y) not in self.walls)


class Level:
    def __init__(self, level_num):
        self.level_num = level_num
        dispatch = {1: self._setup_tutorial,
                    2: self._setup_main,
                    3: self._setup_hard,
                    4: self._setup_expert}
        dispatch.get(level_num, self._setup_expert)()

    # ── Level 1 ─────────────────────────────────────────────────────
    def _setup_tutorial(self):
        self.width, self.height = 12, 8
        self.time_limit = 60
        self.description = "Tutorial: Push the box to the marked spot"
        self.game_map = Map(self.width, self.height)
        s = GameState(self.width, self.height)
        s.time_remaining = self.time_limit
        s.exit_pos = (self.width - 2, self.height - 2)
        s.objects = {'block1': {'x': 6, 'y': 4, 'solid': True, 'locked': False}}
        s.puzzle_spots = {'spot1': {'x': 9, 'y': 4, 'required': 'block1', 'filled': False}}
        s.obstacles = {}
        self.state = s

    # ── Level 2 ─────────────────────────────────────────────────────
    def _setup_main(self):
        self.width, self.height = 16, 10
        self.time_limit = 90
        self.description = "Navigate obstacles and place all boxes"
        self.game_map = Map(self.width, self.height)
        s = GameState(self.width, self.height)
        s.time_remaining = self.time_limit
        s.exit_pos = (self.width - 2, self.height - 2)
        s.objects = {
            'block1': {'x': 7, 'y': 3, 'solid': True, 'locked': False},
            'block2': {'x': 10, 'y': 3, 'solid': True, 'locked': False},
            'block3': {'x': 8, 'y': 6, 'solid': True, 'locked': False},
        }
        s.puzzle_spots = {
            'spot1': {'x': 13, 'y': 2, 'required': 'block1', 'filled': False},
            'spot2': {'x': 13, 'y': 4, 'required': 'block2', 'filled': False},
            'spot3': {'x': 13, 'y': 6, 'required': 'block3', 'filled': False},
        }
        s.obstacles = {
            'wall1':   {'x': 5, 'y': 2, 'width': 1, 'height': 5},
            'narrow1': {'x': 8, 'y': 2, 'width': 3, 'height': 1},
        }
        self.state = s

    # ── Level 3 ─────────────────────────────────────────────────────
    def _setup_hard(self):
        self.width, self.height = 18, 12
        self.time_limit = 150
        self.description = "Hard"
        self.game_map = Map(self.width, self.height)
        s = GameState(self.width, self.height)
        s.p1_x, s.p1_y = 2, 2
        s.p2_x, s.p2_y = 2, 9
        s.time_remaining = self.time_limit
        s.exit_pos = (self.width - 2, self.height - 2)
        s.objects = {
            'block1': {'x': 4,  'y': 4,  'solid': True, 'locked': False},
            'block2': {'x': 7,  'y': 2,  'solid': True, 'locked': False},
            'block3': {'x': 11, 'y': 5,  'solid': True, 'locked': False},
            'block4': {'x': 9,  'y': 9,  'solid': True, 'locked': False},
            'block5': {'x': 5,  'y': 9,  'solid': True, 'locked': False},
        }
        s.puzzle_spots = {
            'spot1': {'x': 15, 'y': 2,  'required': 'block1', 'filled': False},
            'spot2': {'x': 15, 'y': 4,  'required': 'block2', 'filled': False},
            'spot3': {'x': 15, 'y': 6,  'required': 'block3', 'filled': False},
            'spot4': {'x': 15, 'y': 8,  'required': 'block4', 'filled': False},
            'spot5': {'x': 15, 'y': 10, 'required': 'block5', 'filled': False},
        }
        s.obstacles = {
            'wall1':   {'x': 6,  'y': 1, 'width': 1, 'height': 6},
            'wall2':   {'x': 10, 'y': 4, 'width': 2, 'height': 4},
            'narrow1': {'x': 9,  'y': 8, 'width': 2, 'height': 1},
            'narrow2': {'x': 13, 'y': 10,'width': 1, 'height': 2},
        }
        self.state = s

    # ── Level 4 (NEW) ────────────────────────────────────────────────
    def _setup_expert(self):
        self.width, self.height = 22, 14
        self.time_limit = 200
        self.description = "Expert"
        self.game_map = Map(self.width, self.height)
        s = GameState(self.width, self.height)
        s.p1_x, s.p1_y = 2, 2
        s.p2_x, s.p2_y = 2, 11
        s.time_remaining = self.time_limit
        s.exit_pos = (self.width - 2, self.height - 2)
        s.objects = {
            'block1': {'x': 5,  'y': 3,  'solid': True, 'locked': False},
            'block2': {'x': 8,  'y': 2,  'solid': True, 'locked': False},
            'block3': {'x': 11, 'y': 5,  'solid': True, 'locked': False},
            'block4': {'x': 14, 'y': 3,  'solid': True, 'locked': False},
            'block5': {'x': 7,  'y': 10, 'solid': True, 'locked': False},
            'block6': {'x': 11, 'y': 10, 'solid': True, 'locked': False},
            'block7': {'x': 15, 'y': 9,  'solid': True, 'locked': False},
        }
        s.puzzle_spots = {
            'spot1': {'x': 19, 'y': 2,  'required': 'block1', 'filled': False},
            'spot2': {'x': 19, 'y': 4,  'required': 'block2', 'filled': False},
            'spot3': {'x': 19, 'y': 6,  'required': 'block3', 'filled': False},
            'spot4': {'x': 19, 'y': 8,  'required': 'block4', 'filled': False},
            'spot5': {'x': 19, 'y': 10, 'required': 'block5', 'filled': False},
            'spot6': {'x': 19, 'y': 12, 'required': 'block6', 'filled': False},
            'spot7': {'x': 17, 'y': 12, 'required': 'block7', 'filled': False},
        }
        s.obstacles = {
            'col1':    {'x': 7,  'y': 1,  'width': 1, 'height': 5},
            'col2':    {'x': 13, 'y': 1,  'width': 1, 'height': 4},
            'col3':    {'x': 10, 'y': 7,  'width': 1, 'height': 5},
            'row1':    {'x': 4,  'y': 7,  'width': 5, 'height': 1},
            'narrow1': {'x': 16, 'y': 5,  'width': 2, 'height': 1},
            'narrow2': {'x': 8,  'y': 11, 'width': 3, 'height': 1},
        }
        self.state = s

    def check_puzzle(self):
        """
        Mark spots filled and LOCK the block in place when it lands on its spot.
        Returns True when every spot is filled.
        """
        all_filled = True
        for spot in self.state.puzzle_spots.values():
            blk = self.state.objects.get(spot['required'])
            if blk and blk['x'] == spot['x'] and blk['y'] == spot['y']:
                spot['filled'] = True
                blk['locked'] = True      
            else:
                all_filled = False
        return all_filled

    def check_exit(self):
        puzzle_done = self.check_puzzle()
        if puzzle_done:
            ex, ey = self.state.exit_pos
            p1_at = (self.state.p1_x == ex and self.state.p1_y == ey)
            p2_at = (self.state.p2_x == ex and self.state.p2_y == ey)
            if p1_at and p2_at:
                self.state.level_complete = True


class Display:
    def __init__(self, level):
        self.level = level

    def render(self):
        s = self.level.state
        output = '\033[2J\033[H'
        output += "━" * 44 + "\n"
        output += f"  LEVEL {self.level.level_num}  {self.level.description}\n"
        output += "━" * 44 + "\n\n"
        output += self._build_grid() + "\n\n"
        output += "🐱 WASD + SPACE(hold)   🐶 ARROWS + X(hold)\n"
        output += "Hold next to a box → axis-locked push/pull\n"
        output += "Boxes lock in place once placed correctly!\n\n"

        spots_done = sum(1 for sp in s.puzzle_spots.values() if sp['filled'])
        spots_total = len(s.puzzle_spots)
        bar = '🟦' * spots_done + '⬜' * (spots_total - spots_done)
        output += f"Progress: {bar}  {spots_done}/{spots_total}\n"

        t = max(0, s.time_remaining)
        p1h = "🔒ON" if s.p1_hold_active else "  off"
        p2h = "🔒ON" if s.p2_hold_active else "  off"
        output += f"⏱ {t:>3}s  |  🐱 Hold:{p1h}  |  🐶 Hold:{p2h}\n"

        if s.message:
            output += f"\n  ▶ {s.message}\n"

        print(output, end='', flush=True)

    def _build_grid(self):
        W, H = self.level.width, self.level.height
        s = self.level.state
        grid = [[T_FLOOR] * W for _ in range(H)]

        for (x, y) in self.level.game_map.walls:
            grid[y][x] = T_WALL

        for obs in s.obstacles.values():
            ox, oy = obs['x'], obs['y']
            for dy in range(obs.get('height', 1)):
                for dx in range(obs.get('width', 1)):
                    ny, nx = oy + dy, ox + dx
                    if 0 <= ny < H and 0 <= nx < W:
                        grid[ny][nx] = T_OBS

        for spot in s.puzzle_spots.values():
            grid[spot['y']][spot['x']] = T_SPOT

        for obj in s.objects.values():
            grid[obj['y']][obj['x']] = T_LOCKED if obj.get('locked') else T_BLOCK

        ex, ey = s.exit_pos
        grid[ey][ex] = T_EXIT

        grid[s.p1_y][s.p1_x] = T_P1
        grid[s.p2_y][s.p2_x] = T_P2

        return '\n'.join(''.join(row) for row in grid)


class Game:
    def __init__(self, level_num):
        self.level = Level(level_num)
        self.display = Display(self.level)
        self.running = True
        self.move_delay = 0.12
        self.p1_hold_pressed = False
        self.p2_hold_pressed = False

    def _obstacle_at(self, x, y):
        for obs in self.level.state.obstacles.values():
            ox, oy = obs['x'], obs['y']
            if ox <= x < ox + obs.get('width', 1) and oy <= y < oy + obs.get('height', 1):
                return True
        return False

    def _block_at(self, x, y, exclude=None):
        for name, obj in self.level.state.objects.items():
            if name == exclude:
                continue
            if obj['x'] == x and obj['y'] == y:
                return name
        return None

    def _cell_free(self, x, y, exclude_block=None):
        """True if x,y is inside bounds, not a wall, not an obstacle, not another block."""
        if not self.level.game_map.is_passable(x, y):
            return False
        if self._obstacle_at(x, y):
            return False
        if self._block_at(x, y, exclude=exclude_block) is not None:
            return False
        return True

    def move_character(self, player, direction):
        state = self.level.state
        x, y = (state.p1_x, state.p1_y) if player == 1 else (state.p2_x, state.p2_y)
        hold  = state.p1_hold_active if player == 1 else state.p2_hold_active

        dx, dy = {'up': (0,-1), 'down': (0,1),
                  'left': (-1,0), 'right': (1,0)}[direction]
        nx, ny = x + dx, y + dy

        if not self.level.game_map.is_passable(nx, ny):
            return
        if self._obstacle_at(nx, ny):
            return

        other_x = state.p2_x if player == 1 else state.p1_x
        other_y = state.p2_y if player == 1 else state.p1_y
        ex, ey = state.exit_pos
        if nx == other_x and ny == other_y and not (nx == ex and ny == ey):
            return  

        hit = self._block_at(nx, ny)
        if hit:
            obj = state.objects[hit]
            if not hold:
                return    
            if obj.get('locked'):
                return    

            px2, py2 = nx + dx, ny + dy
            if (self._cell_free(px2, py2, exclude_block=hit)
                    and not (px2 == other_x and py2 == other_y)):
                obj['x'], obj['y'] = px2, py2
            else:
                return

        else:
            if hold:
                bx, by = x - dx, y - dy
                pull_name = self._block_at(bx, by)
                if pull_name:
                    pobj = state.objects[pull_name]
                    if not pobj.get('locked'):
                        if (self.level.game_map.is_passable(x, y)
                                and not self._obstacle_at(x, y)):
                            pobj['x'], pobj['y'] = x, y

        if player == 1:
            state.p1_x, state.p1_y = nx, ny
        else:
            state.p2_x, state.p2_y = nx, ny

    def get_input(self):
        p1_dir = p2_dir = None

        if keyboard.is_pressed('w'):      p1_dir = 'up'
        elif keyboard.is_pressed('s'):    p1_dir = 'down'
        elif keyboard.is_pressed('a'):    p1_dir = 'left'
        elif keyboard.is_pressed('d'):    p1_dir = 'right'

        if keyboard.is_pressed('up'):     p2_dir = 'up'
        elif keyboard.is_pressed('down'): p2_dir = 'down'
        elif keyboard.is_pressed('left'): p2_dir = 'left'
        elif keyboard.is_pressed('right'):p2_dir = 'right'

        p1h_now = keyboard.is_pressed('space')
        if p1h_now and not self.p1_hold_pressed:
            self.level.state.p1_hold_active = not self.level.state.p1_hold_active
        self.p1_hold_pressed = p1h_now

        p2h_now = keyboard.is_pressed('x')
        if p2h_now and not self.p2_hold_pressed:
            self.level.state.p2_hold_active = not self.level.state.p2_hold_active
        self.p2_hold_pressed = p2h_now

        return p1_dir, p2_dir

    def run(self):
        print("Starting… Ctrl+C to quit")
        time.sleep(2)
        start = time.time()
        try:
            while self.running and not self.level.state.level_complete:
                self.display.render()
                p1_dir, p2_dir = self.get_input()

                if p1_dir and self.level.state.can_move(1, p1_dir):
                    self.move_character(1, p1_dir)
                if p2_dir and self.level.state.can_move(2, p2_dir):
                    self.move_character(2, p2_dir)

                self.level.check_exit()

                self.level.state.time_remaining = (
                    self.level.time_limit - int(time.time() - start))
                if self.level.state.time_remaining <= 0:
                    self.level.state.time_up = True
                    self.running = False

                time.sleep(self.move_delay)

            self.display.render()
            if self.level.state.level_complete:
                print("🎉 LEVEL COMPLETE!")
                return True
            elif self.level.state.time_up:
                print("💀 TIME UP!  Mission failed.")
                return False

        except KeyboardInterrupt:
            print("\nGame quit.")
            return None


if __name__ == "__main__":
    print("=" * 50)
    print("  🐱🐶  CAT & DOG PUZZLE GAME  🐶🐱")
    print("=" * 50)
    print()
    print("Install deps if needed:")
    print("  pip install keyboard colorama")
    print()
    print("CONTROLS")
    print("  🐱  Cat (P1) : WASD to move, SPACE to toggle Hold")
    print("  🐶  Dog (P2) : Arrow keys,   X     to toggle Hold")
    print()
    print("RULES")
    print("  📦  Boxes can only be pushed/pulled with Hold ON")
    print("  🔒  Stand left/right → horizontal only")
    print("      Stand above/below → vertical only")
    print("  ✅  A box placed on its spot is locked forever")
    print("  🚪  Both reach the exit once all spots are filled")
    print("  🚫  Players cannot walk through each other")
    print()

    for level_num in [1, 2, 3, 4]:
        level_complete = False
        result = None
        while not level_complete:
            print(f"\n▶  Starting Level {level_num}…")
            time.sleep(2)
            game = Game(level_num)
            result = game.run()

            if result is None:
                break
            elif result is True:
                level_complete = True
                time.sleep(1)
            else:
                time.sleep(1)
                retry = input("\nRetry? (y/n): ").strip().lower()
                if retry != 'y':
                    level_complete = True
                    result = True   
                print()

        if result is None:
            break

    print("\nThanks for playing! 🐾")