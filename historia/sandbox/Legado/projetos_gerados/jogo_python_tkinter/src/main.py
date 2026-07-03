import tkinter as tk

class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Jogo Simples com Tkinter")
        
        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()
        
        self.current_phase = 1
        self.score = 0
        
        self.init_menu()
    
    def init_menu(self):
        self.canvas.delete("all")
        
        title_label = self.canvas.create_text(400, 200, text="Jogo Simples", font=("Arial", 36), fill="black")
        instructions_label = self.canvas.create_text(400, 300, text="Use as setas do teclado para mover o jogador.", font=("Arial", 18), fill="black")
        
        start_button = tk.Button(self.root, text="Iniciar Jogo", command=self.start_game)
        start_button.pack(pady=20)
    
    def start_game(self):
        self.canvas.delete("all")
        self.score = 0
        self.current_phase = 1
        self.create_player()
        self.update_score()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.game_loop()
    
    def create_player(self):
        self.player = self.canvas.create_rectangle(400, 500, 420, 520, fill="blue")
    
    def update_score(self):
        score_label = self.canvas.create_text(700, 30, text=f"Pontuação: {self.score}", font=("Arial", 18), fill="black")
    
    def on_key_press(self, event):
        if event.keysym == "Left":
            self.move_player(-10, 0)
        elif event.keysym == "Right":
            self.move_player(10, 0)
        elif event.keysym == "Up":
            self.move_player(0, -10)
        elif event.keysym == "Down":
            self.move_player(0, 10)
    
    def move_player(self, dx, dy):
        self.canvas.move(self.player, dx, dy)
    
    def game_loop(self):
        if self.current_phase <= 3:
            self.update_score()
            self.root.after(50, self.game_loop)
        else:
            self.end_game()
    
    def end_game(self):
        self.canvas.delete("all")
        
        final_score_label = self.canvas.create_text(400, 200, text=f"Fim de Jogo! Pontuação Final: {self.score}", font=("Arial", 36), fill="black")
        
        restart_button = tk.Button(self.root, text="Reiniciar Jogo", command=self.start_game)
        restart_button.pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()