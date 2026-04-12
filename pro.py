import pygame
import random
import heapq
import time

# -------------------- SETTINGS --------------------
WIDTH, HEIGHT = 1000, 720
ROWS, COLS = 12, 16
CELL_SIZE = 40
MAZE_X = 50
MAZE_Y = 80

PANEL_X = 760
FPS = 60

BG = (15, 18, 35)
GRID_BG = (25, 30, 55)
WALL = (220, 220, 255)
PLAYER_COLOR = (0, 255, 180)
EXIT_COLOR = (255, 90, 90)
COIN_COLOR = (255, 215, 0)
TEXT = (240, 240, 255)
BTN = (80, 140, 255)
BTN_HOVER = (110, 170, 255)
PATH_COLOR = (120, 100, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Runner Pro - Kruskal + Dijkstra")
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 24)
small_font = pygame.font.SysFont("arial", 18)
big_font = pygame.font.SysFont("arial", 34, bold=True)


# -------------------- DISJOINT SET (KRUSKAL) --------------------
class DisjointSet:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return False

        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1
        return True


# -------------------- CELL --------------------
class Cell:
    def __init__(self, r, c):
        self.r = r
        self.c = c
        self.walls = {"top": True, "right": True, "bottom": True, "left": True}
        self.coin = False

    def draw(self, surface, show_path=False, is_path=False):
        x = MAZE_X + self.c * CELL_SIZE
        y = MAZE_Y + self.r * CELL_SIZE

        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, GRID_BG, rect)

        if show_path and is_path:
            pygame.draw.rect(surface, PATH_COLOR, rect.inflate(-10, -10), border_radius=8)

        if self.coin:
            pygame.draw.circle(surface, COIN_COLOR, (x + CELL_SIZE // 2, y + CELL_SIZE // 2), 7)

        if self.walls["top"]:
            pygame.draw.line(surface, WALL, (x, y), (x + CELL_SIZE, y), 3)
        if self.walls["right"]:
            pygame.draw.line(surface, WALL, (x + CELL_SIZE, y), (x + CELL_SIZE, y + CELL_SIZE), 3)
        if self.walls["bottom"]:
            pygame.draw.line(surface, WALL, (x, y + CELL_SIZE), (x + CELL_SIZE, y + CELL_SIZE), 3)
        if self.walls["left"]:
            pygame.draw.line(surface, WALL, (x, y), (x, y + CELL_SIZE), 3)


# -------------------- MAZE GAME --------------------
class MazeGame:
    def __init__(self):
        self.level = 1
        self.score = 0
        self.lives = 3
        self.show_hint = False
        self.message = ""
        self.reset_level()

    def reset_level(self):
        self.grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
        self.generate_maze_kruskal()
        self.place_coins(10)
        self.player = [0, 0]
        self.exit = [ROWS - 1, COLS - 1]
        self.start_time = time.time()
        self.level_complete = False
        self.shortest_path = self.dijkstra_path((0, 0), (ROWS - 1, COLS - 1))

    def place_coins(self, count):
        placed = 0
        while placed < count:
            r = random.randint(0, ROWS - 1)
            c = random.randint(0, COLS - 1)
            if (r, c) not in [(0, 0), (ROWS - 1, COLS - 1)] and not self.grid[r][c].coin:
                self.grid[r][c].coin = True
                placed += 1

    def cell_id(self, r, c):
        return r * COLS + c

    def generate_maze_kruskal(self):
        edges = []

        for r in range(ROWS):
            for c in range(COLS):
                if r < ROWS - 1:
                    edges.append(((r, c), (r + 1, c)))
                if c < COLS - 1:
                    edges.append(((r, c), (r, c + 1)))

        random.shuffle(edges)
        ds = DisjointSet(ROWS * COLS)

        for (r1, c1), (r2, c2) in edges:
            id1 = self.cell_id(r1, c1)
            id2 = self.cell_id(r2, c2)

            if ds.union(id1, id2):
                self.remove_wall((r1, c1), (r2, c2))

    def remove_wall(self, a, b):
        r1, c1 = a
        r2, c2 = b

        if r1 == r2:
            if c1 < c2:
                self.grid[r1][c1].walls["right"] = False
                self.grid[r2][c2].walls["left"] = False
            else:
                self.grid[r1][c1].walls["left"] = False
                self.grid[r2][c2].walls["right"] = False
        elif c1 == c2:
            if r1 < r2:
                self.grid[r1][c1].walls["bottom"] = False
                self.grid[r2][c2].walls["top"] = False
            else:
                self.grid[r1][c1].walls["top"] = False
                self.grid[r2][c2].walls["bottom"] = False

    def get_neighbors(self, r, c):
        neighbors = []
        cell = self.grid[r][c]

        if not cell.walls["top"] and r > 0:
            neighbors.append((r - 1, c))
        if not cell.walls["right"] and c < COLS - 1:
            neighbors.append((r, c + 1))
        if not cell.walls["bottom"] and r < ROWS - 1:
            neighbors.append((r + 1, c))
        if not cell.walls["left"] and c > 0:
            neighbors.append((r, c - 1))

        return neighbors

    # -------------------- DIJKSTRA --------------------
    def dijkstra_path(self, start, goal):
        dist = {start: 0}
        parent = {}
        pq = [(0, start)]
        visited = set()

        while pq:
            d, node = heapq.heappop(pq)
            if node in visited:
                continue
            visited.add(node)

            if node == goal:
                break

            for nbr in self.get_neighbors(node[0], node[1]):
                nd = d + 1
                if nbr not in dist or nd < dist[nbr]:
                    dist[nbr] = nd
                    parent[nbr] = node
                    heapq.heappush(pq, (nd, nbr))

        path = []
        cur = goal
        if cur not in parent and cur != start:
            return []

        while cur != start:
            path.append(cur)
            cur = parent[cur]
        path.append(start)
        path.reverse()
        return path

    def move_player(self, direction):
        r, c = self.player
        cell = self.grid[r][c]

        if direction == "UP" and not cell.walls["top"]:
            r -= 1
        elif direction == "RIGHT" and not cell.walls["right"]:
            c += 1
        elif direction == "DOWN" and not cell.walls["bottom"]:
            r += 1
        elif direction == "LEFT" and not cell.walls["left"]:
            c -= 1

        self.player = [r, c]
        self.check_coin()
        self.check_exit()

    def check_coin(self):
        r, c = self.player
        if self.grid[r][c].coin:
            self.grid[r][c].coin = False
            self.score += 10
            self.message = "Coin collected! +10"

    def check_exit(self):
        if self.player == self.exit:
            time_bonus = max(0, 100 - int(time.time() - self.start_time))
            self.score += 50 + time_bonus
            self.level_complete = True
            self.message = f"Level {self.level} completed!"

    def next_level(self):
        self.level += 1
        self.show_hint = False
        self.reset_level()

    def draw(self):
        screen.fill(BG)

        title = big_font.render("Maze Runner Pro", True, TEXT)
        screen.blit(title, (40, 20))

        sub = small_font.render("", True, (180, 200, 255))
        screen.blit(sub, (42, 58))

        path_set = set(self.shortest_path) if self.show_hint else set()

        for r in range(ROWS):
            for c in range(COLS):
                self.grid[r][c].draw(screen, self.show_hint, (r, c) in path_set)

        # exit
        ex = MAZE_X + self.exit[1] * CELL_SIZE + 8
        ey = MAZE_Y + self.exit[0] * CELL_SIZE + 8
        pygame.draw.rect(screen, EXIT_COLOR, (ex, ey, CELL_SIZE - 16, CELL_SIZE - 16), border_radius=8)

        # player
        px = MAZE_X + self.player[1] * CELL_SIZE + CELL_SIZE // 2
        py = MAZE_Y + self.player[0] * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, PLAYER_COLOR, (px, py), 12)

        # side panel
        panel = pygame.Rect(PANEL_X, 90, 210, 500)
        pygame.draw.rect(screen, (28, 34, 62), panel, border_radius=18)
        pygame.draw.rect(screen, (95, 110, 190), panel, 2, border_radius=18)

        stats = [
            f"Level: {self.level}",
            f"Score: {self.score}",
            f"Lives: {self.lives}",
            f"Time: {int(time.time() - self.start_time)} sec",
            f"Coins Left: {self.count_coins()}",
        ]

        y = 120
        for item in stats:
            txt = font.render(item, True, TEXT)
            screen.blit(txt, (785, y))
            y += 40

        controls = [
            "Controls:",
            "Arrow Keys / WASD",
            "H = Hint Path",
            "R = Restart Level",
            "N = Next Level",
            "ESC = Quit"
        ]

        y += 20
        for i, item in enumerate(controls):
            color = (255, 220, 120) if i == 0 else (220, 220, 245)
            txt = small_font.render(item, True, color)
            screen.blit(txt, (785, y))
            y += 28

        if self.message:
            msg = small_font.render(self.message, True, (255, 215, 120))
            screen.blit(msg, (785, 510))

        if self.level_complete:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))

            box = pygame.Rect(280, 220, 430, 170)
            pygame.draw.rect(screen, (30, 40, 80), box, border_radius=20)
            pygame.draw.rect(screen, (130, 180, 255), box, 3, border_radius=20)

            t1 = big_font.render("Level Complete!", True, (255, 255, 255))
            t2 = font.render("Press N for next level", True, (220, 220, 255))
            t3 = font.render(f"Current Score: {self.score}", True, (255, 215, 100))

            screen.blit(t1, (370, 250))
            screen.blit(t3, (400, 300))
            screen.blit(t2, (380, 340))

    def count_coins(self):
        count = 0
        for row in self.grid:
            for cell in row:
                if cell.coin:
                    count += 1
        return count


# -------------------- MAIN LOOP --------------------
def main():
    game = MazeGame()
    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key in (pygame.K_UP, pygame.K_w):
                    if not game.level_complete:
                        game.move_player("UP")

                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if not game.level_complete:
                        game.move_player("RIGHT")

                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if not game.level_complete:
                        game.move_player("DOWN")

                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if not game.level_complete:
                        game.move_player("LEFT")

                elif event.key == pygame.K_h:
                    game.show_hint = not game.show_hint
                    game.message = "Hint toggled using Dijkstra path"

                elif event.key == pygame.K_r:
                    game.message = "Level restarted"
                    game.reset_level()

                elif event.key == pygame.K_n:
                    if game.level_complete:
                        game.next_level()

        game.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()