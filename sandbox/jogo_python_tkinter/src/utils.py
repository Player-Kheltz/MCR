import tkinter as tk
from tkinter import messagebox

class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Game")
        self.canvas_width = 800
        self.canvas_height = 600
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()
        
        self.player = None
        self.obstacles = []
        self.score = 0
        
        self.create_menu()

    def create_menu(self):
        self.menu_frame = tk.Frame(self.root)
        self.menu_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        title_label = tk.Label(self.menu_frame, text="Simple Game", font=("Helvetica", 24))
        title_label.pack(pady=10)
        
        instructions_label = tk.Label(self.menu_frame, text="Use arrow keys to move the player.\nAvoid obstacles to score points.", font=("Helvetica", 12))
        instructions_label.pack(pady=5)
        
        start_button = tk.Button(self.menu_frame, text="Start Game", command=self.start_game)
        start_button.pack(pady=10)

    def start_game(self):
        self.menu_frame.destroy()
        self.initialize_game()

    def initialize_game(self):
        self.player = self.canvas.create_oval(395, 295, 405, 305, fill="blue")
        self.obstacles = []
        self.score = 0
        self.update_score()
        
        self.root.bind("<KeyPress>", self.move_player)
        self.create_obstacle()
        self.game_loop()

    def move_player(self, event):
        if event.keysym == "Left":
            self.canvas.move(self.player, -10, 0)
        elif event.keysym == "Right":
            self.canvas.move(self.player, 10, 0)
        elif event.keysym == "Up":
            self.canvas.move(self.player, 0, -10)
        elif event.keysym == "Down":
            self.canvas.move(self.player, 0, 10)

    def create_obstacle(self):
        x = 5 + (self.canvas_width - 10) * (2 * random.random())
        y = 5 + (self.canvas_height - 10) * (2 * random.random())
        obstacle = self.canvas.create_rectangle(x, y, x+10, y+10, fill="red")
        self.obstacles.append(obstacle)

    def game_loop(self):
        player_coords = self.canvas.coords(self.player)
        for obstacle in self.obstacles:
            if self.check_collision(player_coords, self.canvas.coords(obstacle)):
                messagebox.showinfo("Game Over", f"Your score: {self.score}")
                self.root.quit()
        
        self.create_obstacle()
        self.score += 1
        self.update_score()
        self.root.after(500, self.game_loop)

    def check_collision(self, player_coords, obstacle_coords):
        px1, py1, px2, py2 = player_coords
        ox1, oy1, ox2, oy2 = obstacle_coords
        return not (px2 < ox1 or px1 > ox2 or py2 < oy1 or py1 > oy2)

    def update_score(self):
        self.canvas.delete("score")
        score_label = self.canvas.create_text(50, 20, text=f"Score: {self.score}", font=("Helvetica", 16), tags="score")

if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()