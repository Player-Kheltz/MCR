import tkinter as tk
from entidades import Jogo, Fase

class MenuInicial:
    def __init__(self, root):
        self.root = root
        self.root.title("Jogo com Tkinter")
        
        self.label = tk.Label(root, text="Bem-vindo ao Jogo!", font=("Helvetica", 18))
        self.label.pack(pady=20)
        
        self.instrucoes_button = tk.Button(root, text="Instruções", command=self.exibir_instrucoes)
        self.instrucoes_button.pack(pady=10)
        
        self.jogar_button = tk.Button(root, text="Jogar", command=self.iniciar_jogo)
        self.jogar_button.pack(pady=10)
    
    def exibir_instruções(self):
        instrucoes_window = tk.Toplevel(self.root)
        instrucoes_window.title("Instruções")
        
        instrucoes_text = (
            "Instruções do Jogo:\n"
            "- Use as setas do teclado para mover o personagem.\n"
            "- Evite os obstáculos e colete pontos.\n"
            "- Complete todas as fases para vencer."
        )
        
        label = tk.Label(instrucoes_window, text=instruções_text, font=("Helvetica", 14))
        label.pack(pady=20)
    
    def iniciar_jogo(self):
        self.root.destroy()
        jogo = Jogo()

class Fase:
    def __init__(self, canvas, jogador, nivel):
        self.canvas = canvas
        self.jogador = jogador
        self.nivel = nivel
        self.obstaculos = []
        self.pontos = 0
        
        self.iniciar_fase()
    
    def iniciar_fase(self):
        # Posiciona o jogador no centro da tela
        self.canvas.coords(self.jogador, 250, 400)
        
        # Cria obstáculos com dificuldade crescente
        for i in range(10 + self.nivel * 3):
            x = 50 + (i % 10) * 50
            y = 50 + (i // 10) * 50
            obstaculo = self.canvas.create_rectangle(x, y, x + 20, y + 20, fill="red")
            self.obstaculos.append(obstaculo)
    
    def verificar_colisoes(self):
        for obstaculo in self.obstaculos:
            if self.canvas.bbox(self.jogador).intersects(self.canvas.bbox(obstaculo)):
                return True
        return False

class Jogo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Jogo")
        
        self.canvas = tk.Canvas(self.root, width=500, height=500)
        self.canvas.pack()
        
        self.jogador = self.canvas.create_rectangle(250, 400, 270, 420, fill="blue")
        
        self.fase_atual = 1
        self.iniciar_fase()
        
        self.root.bind("<KeyPress>", self.mover_jogador)
        self.root.mainloop()
    
    def iniciar_fase(self):
        self.fase = Fase(self.canvas, self.jogador, self.fase_atual)
    
    def mover_jogador(self, event):
        x, y = 0, 0
        if event.keysym == "Left":
            x -= 10
        elif event.keysym == "Right":
            x += 10
        elif event.keysym == "Up":
            y -= 10
        elif event.keysym == "Down":
            y += 10
        
        self.canvas.move(self.jogador, x, y)
        
        if self.fase.verificar_colisoes():
            print(f"Fim de jogo! Você completou {self.fase_atual - 1} fases.")
            self.root.destroy()
        else:
            self.pontos += 1
            print(f"Pontuação: {self.pontos}")
            
            if self.canvas.coords(self.jogador)[0] < 0 or self.canvas.coords(self.jogador)[2] > 500 or \
               self.canvas.coords(self.jogador)[1] < 0 or self.canvas.coords(self.jogador)[3] > 500:
                print("Você saiu da tela! Fim de jogo.")
                self.root.destroy()
            
            if self.pontos % 10 == 0 and self.fase_atual < 4:
                self.fase_atual += 1
                self.iniciar_fase()

if __name__ == "__main__":
    root = tk.Tk()
    menu_inicial = MenuInicial(root)
    root.mainloop()