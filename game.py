import heapq
import tkinter as tk
from tkinter import messagebox


CELL_SIZE = 34
GRID_ROWS = 15
GRID_COLS = 20

PLAYER = "P"
EXIT = "E"
WALL = "#"
ROAD = "."
MUD = "M"
WATER = "W"

TERRAIN_COSTS = {
    ROAD: 1,
    MUD: 3,
    WATER: 5,
    PLAYER: 1,
    EXIT: 1,
}

TILE_COLORS = {
    ROAD: "#f7f3e8",
    WALL: "#1f2937",
    MUD: "#a16207",
    WATER: "#38bdf8",
    EXIT: "#22c55e",
}

LEVELS = [
    {
        "name": "Campus Courtyard",
        "description": "A balanced first rescue route with a few costly shortcuts.",
        "rows": [
            "P...#.....M....#....",
            ".##.#.###.M.##.#.##.",
            "...M#...#...#..#....",
            "##.###.#.###.#.####.",
            "...#...#.....#....M.",
            ".#.#.#####.#####.##.",
            ".#...M...#.....#....",
            ".#####.#.###.#.####.",
            "...W...#...#.#....#.",
            "##.#####.#.#.####.#.",
            "...#.....#.#....#...",
            ".#.#.#####.####.###.",
            ".#...#...M....#...W.",
            ".###.#.#########.#..",
            ".....#..........#..E",
        ],
    },
    {
        "name": "Flooded Library",
        "description": "Water-heavy level where the shortest-looking path is not cheapest.",
        "rows": [
            "P..W....#.....M.....",
            "##.####.#.###.#####.",
            "...#....#...#.....#.",
            ".#.#.######.#####.#.",
            ".#...W....#.....#...",
            ".#####.##.#####.###.",
            ".....#..#.....#...#.",
            "####.##.#####.###.#.",
            "...#....W...#.....#.",
            ".#.########.#####.#.",
            ".#......#...#...#...",
            ".######.#.###.#.###.",
            "...M....#.....#...W.",
            ".###############.##.",
            "..................E",
        ],
    },
    {
        "name": "Night Market",
        "description": "Dense barriers reward careful planning and algorithmic hints.",
        "rows": [
            "P....#....M....#....",
            ".##.#.#.#####.#.##..",
            "...#.#.....#..#...#.",
            "##.#.#####.#.###.#..",
            "...#.....#.#.....#..",
            ".#######.#.#####.##.",
            ".#.....#.#.....#....",
            ".#.###.#.###.#.####.",
            ".#...#.#.....#....#.",
            ".###.#.#####.####.#.",
            "...#.#.....#....#...",
            "##.#.###.#.####.###.",
            "...#.....M......#...",
            ".##########..####.#.",
            ".....W..........#.E.",
        ],
    },
]


def normalize_level_rows(rows):
    width = max(len(row) for row in rows)
    return [row.ljust(width, ROAD) for row in rows]


def parse_level(rows):
    grid = [list(row) for row in normalize_level_rows(rows)]
    start = None
    goal = None

    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value == PLAYER:
                start = (row_index, col_index)
                grid[row_index][col_index] = ROAD
            elif value == EXIT:
                goal = (row_index, col_index)
                grid[row_index][col_index] = EXIT

    if start is None or goal is None:
        raise ValueError("Every level must contain one player start and one exit.")

    return grid, start, goal


def dijkstra(grid, start, goal):
    distances = {start: 0}
    previous = {}
    visited_order = []
    priority_queue = [(0, start)]

    while priority_queue:
        current_cost, current = heapq.heappop(priority_queue)
        if current_cost != distances[current]:
            continue

        visited_order.append(current)
        if current == goal:
            break

        for neighbor in get_neighbors(grid, current):
            terrain = grid[neighbor[0]][neighbor[1]]
            new_cost = current_cost + TERRAIN_COSTS[terrain]
            if new_cost < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_cost
                previous[neighbor] = current
                heapq.heappush(priority_queue, (new_cost, neighbor))

    if goal not in distances:
        return [], float("inf"), visited_order

    path = []
    current = goal
    while current != start:
        path.append(current)
        current = previous[current]
    path.append(start)
    path.reverse()
    return path, distances[goal], visited_order


def get_neighbors(grid, position):
    row, col = position
    candidates = [
        (row - 1, col),
        (row + 1, col),
        (row, col - 1),
        (row, col + 1),
    ]

    for next_row, next_col in candidates:
        inside_grid = 0 <= next_row < len(grid) and 0 <= next_col < len(grid[0])
        if inside_grid and grid[next_row][next_col] != WALL:
            yield next_row, next_col


class RescueRouteGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Rescue Route: Dijkstra Pathfinder")
        self.root.resizable(False, False)

        self.level_index = 0
        self.grid = []
        self.start = (0, 0)
        self.goal = (0, 0)
        self.player = (0, 0)
        self.moves = 0
        self.energy = 0
        self.total_moves = 0
        self.total_energy = 0
        self.best_path = []
        self.best_cost = 0
        self.total_best_cost = 0
        self.showing_hint = False
        self.auto_running = False
        self.visited_animation = []
        self.path_animation = []

        self.build_interface()
        self.bind_controls()
        self.load_level(0)

    def build_interface(self):
        self.root.configure(bg="#111827")

        header = tk.Frame(self.root, bg="#111827", padx=14, pady=12)
        header.pack(fill="x")

        title_area = tk.Frame(header, bg="#111827")
        title_area.pack(side="left", fill="x", expand=True)

        self.title_label = tk.Label(
            title_area,
            text="Rescue Route",
            font=("Segoe UI", 18, "bold"),
            fg="#f9fafb",
            bg="#111827",
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = tk.Label(
            title_area,
            text="",
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#111827",
        )
        self.subtitle_label.pack(anchor="w")

        self.stats_label = tk.Label(
            header,
            text="",
            font=("Consolas", 11, "bold"),
            fg="#facc15",
            bg="#111827",
            justify="right",
        )
        self.stats_label.pack(side="right")

        self.canvas = tk.Canvas(
            self.root,
            width=GRID_COLS * CELL_SIZE,
            height=GRID_ROWS * CELL_SIZE,
            bg="#0f172a",
            highlightthickness=0,
        )
        self.canvas.pack(padx=14, pady=(0, 10))

        controls = tk.Frame(self.root, bg="#111827", padx=14, pady=0)
        controls.pack(fill="x", pady=(0, 14))

        self.hint_button = tk.Button(
            controls,
            text="Show Dijkstra Hint",
            command=self.toggle_hint,
            width=18,
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        self.hint_button.pack(side="left", padx=(0, 8))

        self.solve_button = tk.Button(
            controls,
            text="Auto Rescue",
            command=self.auto_rescue,
            width=13,
            bg="#16a34a",
            fg="white",
            activebackground="#15803d",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        self.solve_button.pack(side="left", padx=(0, 8))

        self.restart_button = tk.Button(
            controls,
            text="Restart",
            command=lambda: self.load_level(self.level_index),
            width=10,
            bg="#475569",
            fg="white",
            activebackground="#334155",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        self.restart_button.pack(side="left", padx=(0, 8))

        self.next_button = tk.Button(
            controls,
            text="Next Level",
            command=self.next_level,
            width=11,
            bg="#7c3aed",
            fg="white",
            activebackground="#6d28d9",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        self.next_button.pack(side="left")

        legend = tk.Label(
            controls,
            text="Arrows/WASD move | Yellow = optimal path | Purple = explored nodes",
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#111827",
        )
        legend.pack(side="right")

    def bind_controls(self):
        controls = {
            "<Up>": (-1, 0),
            "<Down>": (1, 0),
            "<Left>": (0, -1),
            "<Right>": (0, 1),
            "w": (-1, 0),
            "s": (1, 0),
            "a": (0, -1),
            "d": (0, 1),
            "W": (-1, 0),
            "S": (1, 0),
            "A": (0, -1),
            "D": (0, 1),
        }
        for key, delta in controls.items():
            self.root.bind(key, lambda event, move=delta: self.move_player(move))

    def load_level(self, level_index):
        self.level_index = level_index % len(LEVELS)
        level = LEVELS[self.level_index]
        self.grid, self.start, self.goal = parse_level(level["rows"])
        self.player = self.start
        self.moves = 0
        self.energy = 0
        self.showing_hint = False
        self.auto_running = False
        self.visited_animation = []
        self.path_animation = []
        self.best_path, self.best_cost, _ = dijkstra(self.grid, self.start, self.goal)

        self.title_label.config(text=f"Rescue Route: {level['name']}")
        self.subtitle_label.config(text=level["description"])
        self.hint_button.config(text="Show Dijkstra Hint")
        self.draw()

    def next_level(self):
        if self.level_index + 1 >= len(LEVELS):
            self.finish_game()
        else:
            self.load_level(self.level_index + 1)

    def toggle_hint(self):
        if self.auto_running:
            return

        self.showing_hint = not self.showing_hint
        self.hint_button.config(text="Hide Hint" if self.showing_hint else "Show Dijkstra Hint")
        if self.showing_hint:
            self.animate_dijkstra()
        else:
            self.visited_animation = []
            self.path_animation = []
            self.draw()

    def animate_dijkstra(self):
        _, _, visited = dijkstra(self.grid, self.player, self.goal)
        self.visited_animation = []
        self.path_animation = []
        self.animate_visited(visited[:90], 0)

    def animate_visited(self, visited, index):
        if not self.showing_hint or index >= len(visited):
            path, _, _ = dijkstra(self.grid, self.player, self.goal)
            self.path_animation = path
            self.draw()
            return

        self.visited_animation.append(visited[index])
        self.draw()
        self.root.after(10, lambda: self.animate_visited(visited, index + 1))

    def auto_rescue(self):
        if self.auto_running:
            return

        path, _, _ = dijkstra(self.grid, self.player, self.goal)
        if not path:
            messagebox.showwarning("No route", "Dijkstra could not find a route to the exit.")
            return

        self.auto_running = True
        self.showing_hint = True
        self.hint_button.config(text="Hide Hint")
        self.path_animation = path
        self.follow_path(path[1:], 0)

    def follow_path(self, path, index):
        if index >= len(path):
            self.auto_running = False
            return

        next_position = path[index]
        self.step_to(next_position)
        self.root.after(120, lambda: self.follow_path(path, index + 1))

    def move_player(self, delta):
        if self.auto_running:
            return

        row_delta, col_delta = delta
        next_position = (self.player[0] + row_delta, self.player[1] + col_delta)
        if not self.is_walkable(next_position):
            self.flash_wall(next_position)
            return

        self.step_to(next_position)

    def is_walkable(self, position):
        row, col = position
        if row < 0 or row >= len(self.grid) or col < 0 or col >= len(self.grid[0]):
            return False
        return self.grid[row][col] != WALL

    def step_to(self, position):
        self.player = position
        self.moves += 1
        terrain = self.grid[position[0]][position[1]]
        self.energy += TERRAIN_COSTS[terrain]

        if self.showing_hint:
            self.path_animation, _, _ = dijkstra(self.grid, self.player, self.goal)
            self.visited_animation = []

        self.draw()

        if self.player == self.goal:
            self.finish_level()

    def finish_level(self):
        self.total_moves += self.moves
        self.total_energy += self.energy
        self.total_best_cost += self.best_cost

        rating = "Perfect" if self.energy == self.best_cost else "Rescued"
        messagebox.showinfo(
            "Level Complete",
            f"{rating}!\n\n"
            f"Your energy cost: {self.energy}\n"
            f"Dijkstra optimal cost: {self.best_cost}\n"
            f"Moves used: {self.moves}",
        )
        self.next_level()

    def finish_game(self):
        efficiency = self.total_best_cost / self.total_energy if self.total_energy else 0
        messagebox.showinfo(
            "Mission Complete",
            "You completed all rescue missions!\n\n"
            f"Total energy used: {self.total_energy}\n"
            f"Total Dijkstra optimal energy: {self.total_best_cost}\n"
            f"Total moves: {self.total_moves}\n"
            f"Efficiency score: {efficiency:.1%}",
        )
        self.root.destroy()

    def flash_wall(self, position):
        row, col = position
        if 0 <= row < len(self.grid) and 0 <= col < len(self.grid[0]):
            x1 = col * CELL_SIZE + 3
            y1 = row * CELL_SIZE + 3
            x2 = x1 + CELL_SIZE - 6
            y2 = y1 + CELL_SIZE - 6
            marker = self.canvas.create_rectangle(x1, y1, x2, y2, outline="#ef4444", width=3)
            self.root.after(120, lambda: self.canvas.delete(marker))

    def draw(self):
        self.canvas.delete("all")

        path_set = set(self.path_animation if self.showing_hint else [])
        visited_set = set(self.visited_animation if self.showing_hint else [])

        for row in range(len(self.grid)):
            for col in range(len(self.grid[0])):
                position = (row, col)
                tile = self.grid[row][col]
                color = TILE_COLORS[tile]

                if position in visited_set and position not in (self.player, self.goal):
                    color = "#a78bfa"
                if position in path_set and position not in (self.player, self.goal):
                    color = "#facc15"

                x1 = col * CELL_SIZE
                y1 = row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#111827")

                if tile == MUD:
                    self.canvas.create_text(x1 + 17, y1 + 17, text="3", fill="#fef3c7", font=("Segoe UI", 10, "bold"))
                elif tile == WATER:
                    self.canvas.create_text(x1 + 17, y1 + 17, text="5", fill="#082f49", font=("Segoe UI", 10, "bold"))
                elif tile == EXIT:
                    self.canvas.create_text(x1 + 17, y1 + 17, text="E", fill="white", font=("Segoe UI", 12, "bold"))

        self.draw_player()
        self.draw_stats()

    def draw_player(self):
        row, col = self.player
        center_x = col * CELL_SIZE + CELL_SIZE // 2
        center_y = row * CELL_SIZE + CELL_SIZE // 2

        self.canvas.create_oval(
            center_x - 12,
            center_y - 12,
            center_x + 12,
            center_y + 12,
            fill="#ef4444",
            outline="#fecaca",
            width=2,
        )
        self.canvas.create_text(center_x, center_y, text="+", fill="white", font=("Segoe UI", 13, "bold"))

    def draw_stats(self):
        current_path, current_best, _ = dijkstra(self.grid, self.player, self.goal)
        remaining = current_best if current_path else float("inf")
        total_possible = self.energy + remaining if remaining != float("inf") else "No route"
        self.stats_label.config(
            text=(
                f"Moves: {self.moves}\n"
                f"Energy: {self.energy}\n"
                f"Optimal: {self.best_cost}\n"
                f"Best from here: {total_possible}"
            )
        )


def main():
    root = tk.Tk()
    RescueRouteGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
