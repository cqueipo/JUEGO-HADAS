from multiprocessing.connection import Listener
from multiprocessing import Process, Manager, Value, Lock
import traceback
import sys
import random

jugador_1 = 0
jugador_2 = 1
turno = ["primero", "segundo"]
turno1 = ["primero", "segundo"]
SIZE = (728, 410) #tamaño de la imagen de fondo
X=0
Y=1
DELTA = 10
venenonum = 3

class Player():
    def __init__(self, numero):
        self.numero = numero
        if numero == jugador_1:
            self.pos = [30, SIZE[Y]-45]
            self.face  = 'Right'
        else:
            self.pos = [SIZE[X] - 30, SIZE[Y]-45]
            self.face  = 'Left'
        
    def get_pos(self):
        return self.pos
    
    def get_face(self):
        return self.face
    
    def get_numero(self):
        return self.numero
    
    def moveRight(self):
        self.pos[X] += DELTA
        if self.pos[X] > SIZE[X]:
            self.pos[X] = SIZE[X]

    def moveLeft(self):
        self.pos[X] -= DELTA
        if self.pos[X] < 0:
            self.pos[X] = 0

    def __str__(self):
        return f"P<{turno1[self.numero]}, {self.pos}>"


class veneno():
    def __init__(self, number,velocity):
        self.pos=[ random.randint(0,700) , 0 ]
        self.velocity = velocity
        self.number = number

    def get_pos(self):
        return self.pos

    def get_number(self):
        return self.number

    def update(self):
        self.pos[X] += self.velocity[X]
        self.pos[Y] += self.velocity[Y]

    def edge(self, AXIS):
        self.velocity[AXIS] = -self.velocity[AXIS]

    def collide_player(self, numero):        
        self.pos[X] = random.randint(0,2)
        self.pos[Y] = 0

    def __str__(self):
        return f"B<{self.pos, self.velocity}>"

class flor():
    def __init__(self,velocity):
        self.pos=[ random.randint(0,700) , 0 ]
        self.velocity = velocity

    def get_pos(self):
        return self.pos

    def update(self):
        self.pos[X] += self.velocity[X]
        self.pos[Y] += self.velocity[Y]

    def edge(self, AXIS):
        self.velocity[AXIS] = -self.velocity[AXIS]

    def collide_player(self, numero):        
        self.pos[X] = random.randint(0,2)
        self.pos[Y] = 0

    def __str__(self):
        return f"B<{self.pos, self.velocity}>"


class Game():
    def __init__(self, manager):
        self.players = manager.list( [Player(jugador_1), Player(jugador_2)] )
        self.vidas = manager.list( [5,5] )
        self.veneno = manager.list([veneno(i,[random.randint(-3,3),random.randint(5,7)]) for i in range(venenonum)])
        self.flor = flor([random.randint(-3,3),random.randint(5,7)])
        self.veneno_pos = manager.list([self.veneno[i].get_pos() for i in range(venenonum)])
        self.flor_pos = self.flor.get_pos() 
        self.running = Value('i', 1)
        self.lock = Lock()

    def get_player(self, numero):
        return self.players[numero]
    
    def get_vidas(self):
        return list(self.vidas)

    def get_veneno(self,i):
        return self.veneno[i]
    
    def get_flor(self):
        return self.flor
    
    def is_running(self):
        return self.running.value == 1

    def stop(self):
        self.running.value = 0
    
    def faceLeft(self, player):
        self.lock.acquire()
        p = self.players[player]
        p.face = 'Left'
        self.players[player] = p
        self.lock.release()
    
    def faceRight(self, player):
        self.lock.acquire()
        p = self.players[player]
        p.face = 'Right'
        self.players[player] = p
        self.lock.release()
    
    def moveLeft(self, player):
        self.lock.acquire()
        p = self.players[player]
        p.moveLeft()
        self.players[player] = p
        self.lock.release()
    
    def moveRight(self, player):
        self.lock.acquire()
        p = self.players[player]
        p.moveRight()
        self.players[player] = p
        self.lock.release()

    def move_veneno(self,i):
        self.lock.acquire()
        veneno = self.veneno[i]
        veneno.update()
        pos = veneno.get_pos()
        if pos[Y]<0 or pos[Y]>SIZE[Y]:
            pos[Y] = 0        
            pos[X] = random.randint(10,700)
        self.veneno[i]=veneno
        self.veneno_pos[i] = [pos[X],pos[Y]]
        self.lock.release()
        
    def move_flor(self):
        self.lock.acquire()
        flor = self.flor
        flor.update()
        pos = flor.get_pos()
        if pos[Y]<0 or pos[Y]>SIZE[Y]:
            pos[Y] = 0        
            pos[X] = random.randint(10,700)
        self.flor=flor
        self.flor_pos = [pos[X],pos[Y]]
        self.lock.release()

    def veneno_collide(self,i, playernumero):
        self.lock.acquire()
        veneno = self.veneno[i]
        veneno.collide_player(playernumero)    
        self.veneno[i] = veneno
        self.lock.release()
      
    def flor_collide(self, playernumero):
        self.lock.acquire()
        flor = self.flor
        flor.collide_player(playernumero)    
        self.flor = flor
        self.lock.release()
          
    
    def get_info(self):
        info = {
            'pos_jugador_1': self.players[jugador_1].get_pos(),
            'pos_jugador_2': self.players[jugador_2].get_pos(),
            'face_jugador_1': self.players[jugador_1].get_face(),
            'face_jugador_2': self.players[jugador_2].get_face(),
            'vidas' : list(self.vidas),
            'is_running': self.running.value == 1,
            'pos_veneno_list': list(self.veneno_pos),
            'pos_flor': self.flor_pos
        }
        return info

    def __str__(self):
        return f"G<{self.players[jugador_2]}:{self.players[jugador_1]}:{self.running.value}>"

def player(numero, conn, game):
    try:
        print(f"starting player {turno[numero]}:{game.get_info()}")
        conn.send( (numero, game.get_info()) )
        while game.is_running():
            command = ""
            while command != "next":
                command = conn.recv()
        
                if command == "right":
                    game.moveRight(numero)
                    game.faceRight(numero)
                elif command == "left":
                    game.moveLeft(numero)
                    game.faceLeft(numero)
                elif "collideveneno" in command:
                    i = int(command[16]) 
                    game.veneno_collide(i,numero)
                    game.vidas[numero] -=1   
                elif "collideflor" in command: 
                    game.flor_collide(numero)
                    if game.vidas[numero] < 5:
                        game.vidas[numero] += 1
                elif command == "quit":
                    game.stop()
                elif "death" in command:
                    game.stop()
                    print('El jugador ' + f'{numero + 1}' + ' murió')
                    if numero == 0 :
                        print('El jugador ' + f'{2}' + ' ha ganado')
                    else: 
                        print('El jugador ' + f'{1}' + ' ha ganado')
                elif "victory" in command:
                    game.stop()
                    print('El jugador ' + f'{numero + 1}' + ' ha ganado')
            if numero == 1:
                for i in range(venenonum):
                    game.move_veneno(i)
            game.move_flor()  
            conn.send(game.get_info())
    except:
        traceback.print_exc()
        conn.close()
    finally:
        print(f"Game ended {game}")


def main(ip_address):
    manager = Manager()
    try:
        with Listener((ip_address, 6000),
                      authkey=b'secret password') as listener:
            n_player = 0
            players = [None, None]
            game = Game(manager)
            while True:
                print(f"accepting connection {n_player}")
                conn = listener.accept()
                players[n_player] = Process(target=player, args=(n_player, conn, game))
                n_player += 1
                if n_player == 2:
                    players[0].start()
                    players[1].start()
                    n_player = 0
                    players = [None, None]
                    game = Game(manager)

    except Exception as e:
        traceback.print_exc()

if __name__=='__main__':
    ip_address = "127.0.0.1"
    if len(sys.argv)>1:
        ip_address = sys.argv[1]

    main(ip_address)
