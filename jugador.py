from multiprocessing.connection import Client
import traceback
import pygame
import sys, os
from multiprocessing import Value

X = 0
Y = 1
SIZE = (728, 410)

jugador_1 = 0
jugador_2 = 1
FPS = 30

turno = ["first", "second"]
nveneno = 3

class Player():
    def __init__(self, numero):
        self.numero = numero
        self.pos = [None, None]
        self.face = None
    def get_pos(self):
        return self.pos

    def get_numero(self):
        return self.numero

    def set_pos(self, pos):
        self.pos = pos
        
    def set_face(self, face):
        self.face = face
    
    def get_face(self):
        return self.face
        
    def __str__(self):
        return f"P<{turno[self.numero], self.pos}>"


class veneno():
    def __init__(self,number):
        self.pos = [None,None]
        self.number = number
    
    def get_pos(self):
        return self.pos

    def set_pos(self,pos):
        self.pos = pos

    def __str__(self):
        return f"B<{self.pos}>"

class flor():
    def __init__(self):
        self.pos = [None,None]
    
    def get_pos(self):
        return self.pos

    def set_pos(self,pos):
        self.pos = pos

    def __str__(self):
        return f"B<{self.pos}>"

class Game():
    def __init__(self):
        self.players = [Player(i) for i in range(2)]
        self.veneno = [veneno(i) for i in range(nveneno)]      
        self.flor = flor()
        self.vidas = [5,5]
        self.running = True

    def get_player(self, numero):
        return self.players[numero]

    def get_veneno(self,i):
        return self.veneno[i]
    
    def get_flor(self):
        return self.flor
    
    def get_vidas(self):
        return self.vidas

    def set_pos_player(self, numero, pos):
        self.players[numero].set_pos(pos)
        
    def set_face_player(self, numero, face):
        self.players[numero].set_face(face)
        
    def set_veneno_pos(self, i, pos):
        self.veneno[i].pos = pos
        
    def set_flor_pos(self, pos):
        self.flor.pos = pos
        
    def set_vidas(self,vidas):
        self.vidas = vidas

    def update(self, gameinfo):
        self.set_pos_player(jugador_1, gameinfo['pos_jugador_1'])
        self.set_pos_player(jugador_2, gameinfo['pos_jugador_2'])
        self.set_face_player(jugador_1, gameinfo['face_jugador_1'])
        self.set_face_player(jugador_2, gameinfo['face_jugador_2'])
        for i in range(nveneno):
            self.set_veneno_pos(i, gameinfo['pos_veneno_list'][i]) 
        self.set_flor_pos(gameinfo['pos_flor']) 
        self.set_vidas(gameinfo['vidas'])
        self.running = gameinfo['is_running']

    def is_running(self):
        return self.running

    def stop(self):
        self.running = False

    def __str__(self):
        return f"G<{self.players[jugador_2]}:{self.players[jugador_1]}>"

lista =['hada1r.png', 'hada2l.png']
right = ['hada1r.png', 'hada2r.png']
left = ['hada1l.png', 'hada2l.png']

class Hada(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.player = player
        imagen = lista[self.player.get_numero()]
        self.image = pygame.image.load(imagen)
        self.rect = self.image.get_rect()
        self.update()

    def update(self):
        pos = self.player.get_pos()  
        if self.player.get_face() == 'Left':
            imagen = left[self.player.get_numero()]
            self.image = pygame.image.load(imagen)
        elif self.player.get_face() == 'Right':
            imagen = right[self.player.get_numero()]
            self.image = pygame.image.load(imagen)
        self.rect.centerx, self.rect.centery = pos

    def __str__(self):
        return f"S<{self.player}>"


class venenoSprite(pygame.sprite.Sprite):
    def __init__(self, veneno):
        super().__init__()
        self.veneno = veneno
        self.image = pygame.image.load('venenomalo.png')
        self.rect = self.image.get_rect()
        self.update()

    def update(self):
        pos = self.veneno.get_pos()
        self.rect.centerx, self.rect.centery = pos

class florSprite(pygame.sprite.Sprite):
    def __init__(self, flor):
        super().__init__()
        self.flor= flor
        self.image = pygame.image.load('flor.png')
        self.rect = self.image.get_rect()
        self.update()

    def update(self):
        pos = self.flor.get_pos()
        self.rect.centerx, self.rect.centery = pos
        
def draw_lives(surf, x, y, lives, img):
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = x + 40 * i
        img_rect.y = y
        surf.blit(img, img_rect)

listavidas = ['corazon1.png','corazon2.png']
img1 = pygame.image.load(listavidas[0])
miniimg1 = pygame.transform.scale(img1, (50, 38))
img2 = pygame.image.load(listavidas[1])
miniimg2 = pygame.transform.scale(img2, (50, 38))

class Display():
    def __init__(self, game, face):    
        self.game = game
        self.hadas = [Hada(self.game.get_player(i)) for i in range(2)]
        self.veneno = [venenoSprite(self.game.get_veneno(i)) for i in range(nveneno)]  
        self.flor = florSprite(self.game.get_flor())
        self.all_sprites = pygame.sprite.Group()
        self.hada_group = pygame.sprite.Group()
        for hada in self.hadas:
            self.all_sprites.add(hada)
            self.hada_group.add(hada)  
        for bul in self.veneno:
            self.all_sprites.add(bul)      
        self.all_sprites.add(self.flor)
        self.screen = pygame.display.set_mode(SIZE) 
        self.clock =  pygame.time.Clock() 
        self.background = pygame.image.load('nubes.jpg')
        pygame.init()
        self.sound = pygame.mixer.music.load('musica.mp3')
        self.sound = pygame.mixer.music.set_volume(0.4)
        pygame.mixer.init()
        pygame.mixer.music.play(loops=-1)


    def analyze_events(self, numero):
        events = []    
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    events.append("quit")
            elif event.type == pygame.QUIT:
                events.append("quit")
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
           events.append("left")
           self.game.set_face_player(numero, 'Left') 
        elif keys[pygame.K_RIGHT]:
           events.append("right") 
           self.game.set_face_player(numero, 'Right') 
        for i in range(nveneno):
            if pygame.sprite.collide_rect(self.veneno[i], self.hadas[numero]):
                events.append("collideveneno"+f"{i}")
        
        if pygame.sprite.collide_rect(self.flor, self.hadas[numero]):
            events.append("collideflor")
        if self.game.vidas[numero] == 0:
            events.append("death"+f"{numero}")      
        return events

    def refresh(self):
        vidas = self.game.get_vidas()
        self.screen.blit(self.background, (0, 0)) 
        self.all_sprites.draw(self.screen)
        draw_lives(self.screen, 20, 5, vidas[jugador_1], miniimg1)
        draw_lives(self.screen, 500, 5, vidas[jugador_2], miniimg2)
        pygame.display.flip()
        self.all_sprites.update()
 
        

    def tick(self):
        self.clock.tick(FPS)
    @staticmethod
    def quit():
        pygame.quit()


def main(ip_address):
    try:
        with Client((ip_address, 6000), authkey=b'secret password') as conn:
            game = Game()
            face = None
            numero,gameinfo = conn.recv()
            print(f"You are playing {turno[numero]}. Good luck!")
            game.update(gameinfo)
            display = Display(game,face)
            while game.is_running():
                events = display.analyze_events(numero)
                for ev in events:
                    conn.send(ev)
                    if ev == 'quit':
                        game.stop()
                conn.send("next")
                gameinfo = conn.recv()
                game.update(gameinfo)
                display.refresh()
                display.tick()
    except:
        traceback.print_exc()
    finally:
        pygame.quit()


if __name__=="__main__":
    ip_address = "127.0.0.1"
    if len(sys.argv)>1:
        ip_address = sys.argv[1]
    main(ip_address)
    