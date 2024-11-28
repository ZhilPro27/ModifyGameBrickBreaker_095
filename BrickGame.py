import tkinter as tk
import random
import pygame

# Inisialisasi pygame untuk mixer audio
pygame.mixer.init()

class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)

class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        # increase the below value to increase the speed of ball
        self.speed = 5
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()

class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        # set the shape and position of paddle
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        self.color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=self.color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.create_particles()
            self.delete()
        else:
            self.color = Brick.COLORS[self.hits]
            self.canvas.itemconfig(self.item, fill=self.color)
    
    def create_particles(self):
        # Mendapatkan posisi brick
        coords = self.get_position()
        x = (coords[0] + coords[2]) / 2
        y = (coords[1] + coords[3]) / 2
        for _ in range(20):  # 20 partikel untuk setiap brick
            particle = Particle(self.canvas, x, y, self.color)
            # Tambahkan partikel ke daftar global
            self.canvas.master.particles.append(particle)


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#D6D1F5',
                                width=self.width,
                                height=self.height,)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width/2, 326)
        self.items[self.paddle.item] = self.paddle
        # adding brick with different hit capacities - 3,2 and 1
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>',
                         lambda _: self.paddle.move(-10))
        self.canvas.bind('<Right>',
                         lambda _: self.paddle.move(10))
        self.particles = []


    def setup_game(self):
           self.add_ball()
           self.update_lives_text()
           self.text = self.draw_text(300, 200,
                                      'Press Space to start')
           self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.ball.speed = None
            self.draw_text(300, 200, 'You win! You the Breaker of Bricks.')
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.draw_text(300, 200, 'You Lose! Game Over!')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.update_particles()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)
    
    def update_particles(self):
        # Update and remove expired particles
        self.particles = [p for p in self.particles if p.update()]

class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = 5
        self.tail_particles = []  # Menyimpan partikel ekor
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        # Membalik arah jika bola menyentuh dinding
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        
        # Menggerakkan bola
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

        # Membuat efek ekor
        self.create_tail_particles(coords[0] + self.radius, coords[1] + self.radius, x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()  # Menghancurkan brick dan memutar suara
    
    def create_tail_particles(self, ball_x, ball_y, speed_x, speed_y):
        # Membuat partikel ekor yang bergerak mengikuti bola
        for _ in range(2):  # Membuat 2 partikel ekor per frame
            particle = TailParticle(self.canvas, ball_x, ball_y, speed_x, speed_y)
            self.canvas.master.particles.append(particle)  # Menambahkan ke daftar global partikel

class TailParticle:
    def __init__(self, canvas, x, y, speed_x, speed_y):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.size = 5  # Ukuran awal partikel ekor
        self.lifetime = 10  # Lama hidup partikel ekor
        self.speed_x = speed_x * 0.5  # Kecepatan ekor sedikit lebih lambat dari bola
        self.speed_y = speed_y * 0.5  # Kecepatan ekor sedikit lebih lambat dari bola
        self.item = canvas.create_oval(x - self.size, y - self.size,
                                       x + self.size, y + self.size,
                                       fill='white', outline="")
    
    def update(self):
        # Kurangi lifetime partikel
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.canvas.delete(self.item)
            return False
        
        # Gerakkan partikel ekor mengikuti bola
        self.canvas.move(self.item, self.speed_x, self.speed_y)
        
        # Kurangi ukuran partikel ekor agar semakin meredup
        self.size -= 0.5
        coords = self.canvas.coords(self.item)
        new_coords = [coords[0] + 0.25, coords[1] + 0.25,
                      coords[2] - 0.25, coords[3] - 0.25]
        self.canvas.coords(self.item, *new_coords)
        
        return True


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        self.color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=self.color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.create_particles()
            self.delete()
        else:
            self.color = Brick.COLORS[self.hits]
            self.canvas.itemconfig(self.item, fill=self.color)

        # Memutar suara saat brick kena
        self.play_hit_sound()
    
    def play_hit_sound(self):
        # Memutar suara saat brick terkena bola
        hit_sound = pygame.mixer.Sound('hit_sound.mp3')  # Ganti dengan file suara Anda
        hit_sound.set_volume(1.5)  # Menetapkan volume suara (opsional)
        hit_sound.play()
    
    def create_particles(self):
        # Mendapatkan posisi brick
        coords = self.get_position()
        x = (coords[0] + coords[2]) / 2
        y = (coords[1] + coords[3]) / 2
        for _ in range(20):  # 20 partikel untuk setiap brick
            particle = Particle(self.canvas, x, y, self.color)
            self.canvas.master.particles.append(particle)  # Tambahkan ke daftar partikel

class Particle:
    def __init__(self, canvas, x, y, color):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.size = 10  # Ukuran awal partikel lebih besar
        self.lifetime = 20  # Jumlah update sebelum partikel menghilang
        self.speed_x = (random.random() - 0.5) * 6  # Kecepatan horizontal
        self.speed_y = (random.random() - 0.5) * 6  # Kecepatan vertikal
        self.color = color  # Simpan warna asli
        self.item = canvas.create_oval(x - self.size, y - self.size,
                                       x + self.size, y + self.size,
                                       fill=self.color, outline="")

    def update(self):
        # Kurangi lifetime
        self.lifetime -= 0.5
        if self.lifetime <= 0:
            self.canvas.delete(self.item)
            return False

        # Hitung faktor redup berdasarkan sisa lifetime
        factor = self.lifetime / 20  # Faktor redup berdasarkan lifetime maksimum


        # Kurangi ukuran partikel
        self.size -= 150
        coords = self.canvas.coords(self.item)
        new_coords = [coords[0] + 0.25, coords[1] + 0.25,
                      coords[2] - 0.25, coords[3] - 0.25]
        self.canvas.coords(self.item, *new_coords)

        # Gerakkan partikel
        self.canvas.move(self.item, self.speed_x, self.speed_y)
        return True
        

class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#D6D1F5',
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width/2, 326)
        self.items[self.paddle.item] = self.paddle
        self.particles = []  # Tambahkan daftar partikel global
        # Menambahkan bricks
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>',
                         lambda _: self.paddle.move(-10))
        self.canvas.bind('<Right>',
                         lambda _: self.paddle.move(10))

        self.music_playing = False  # Flag untuk cek apakah musik sudah diputar

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200,
                                    'Press Space to start')
        self.canvas.bind('<space>', lambda _: self.start_game())
        

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

        # Mulai memutar soundtrack jika belum diputar
        if not self.music_playing:
            self.play_soundtrack()
            self.music_playing = True
    
    def play_soundtrack(self):
        # Muat dan putar musik (gunakan file audio yang ada di direktori game)
        pygame.mixer.music.load('soundtrack.mp3')  # Ganti dengan path file musik Anda
        pygame.mixer.music.set_volume(0.75)  # Menetapkan volume musik (opsional)
        pygame.mixer.music.play(-1, 0.0)  # Pemutaran looping tak terbatas, mulai dari 0 detik

    def play_win_soundtrack(self):
        # Hentikan musik yang sedang diputar
        pygame.mixer.music.stop()

        # Putar musik kemenangan
        pygame.mixer.music.load('win_soundtrack.wav')  # Ganti dengan path file musik kemenangan Anda
        pygame.mixer.music.set_volume(1)  # Menetapkan volume musik (opsional)
        pygame.mixer.music.play(0, 0.0)  # Musik hanya diputar sekali

        # Tampilkan pesan kemenangan
        self.canvas.create_text(self.width // 2, self.height // 2,
                                text="YOU WIN!", font=('Arial', 30), fill='green')

    def game_over(self):
        # Hentikan musik yang sedang diputar
        pygame.mixer.music.stop()

        # Putar musik Game Over
        pygame.mixer.music.load('game_over.mp3')  # Ganti dengan path file musik game over
        pygame.mixer.music.set_volume(1)  # Menetapkan volume musik (opsional)
        pygame.mixer.music.play(0, 0.0)  # Musik hanya diputar sekali

        # Tampilkan pesan game over
        self.canvas.create_text(self.width // 2, self.height // 2,
                                text="GAME OVER", font=('Arial', 30), fill='red')

    def game_loop(self):
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.ball.speed = None
            self.play_win_soundtrack()  # Panggil musik kemenangan jika semua brick dihancurkan
        elif self.ball.get_position()[3] >= self.height:  # Bola jatuh
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.game_over()  # Pemanggilan game over jika hidup habis
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.update_particles()  # Perbarui partikel
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)
    
    def update_particles(self):
        active_particles = []
        for particle in self.particles:
            if particle.update():  # Hanya simpan partikel yang masih aktif
                active_particles.append(particle)
        self.particles = active_particles



if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root)
    game.mainloop()