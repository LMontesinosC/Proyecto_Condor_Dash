import pygame
import random
import socket
import threading
import time
import pickle
import sys

# Inicialización de Pygame
pygame.init()

# Variables generales
ANCHO, ALTURA = 1200, 600
ALTURA_BASE = 0
FPS = 60
VELOCIDAD_CAIDA = 0.25
VELOCIDAD_SUBIDA = -0.275
INTERVALO_ESCENARIOS = 2400
VELOCIDAD_ESCENARIOS = 1
ANCHO_ESCENARIOS = 2400
INTERVALO_OBSTACULOS = 30
VELOCIDAD_OBSTACULOS = 5

# Variables multijugador
PUERTO_UDP = 5000  # Para broadcast
PUERTO_TCP = 5001  # Para juego

# Colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
AZUL = (50, 150, 255)
AZUL_CLARO = (115, 183, 255)
ROJO = (229, 32, 32)
VERDE = (32, 229, 32)
AMARILLO = (255, 235, 0)
NARANJA = (255, 127, 39)
GRIS = (170, 170, 170)
GRIS_CLARO = (210, 210, 210)
GRIS_OSCURO = (120, 120, 120)
GRIS_NEGRO = (90, 90, 90)

# Pantalla
screen = pygame.display.set_mode((ANCHO, ALTURA))  # Tamaño de la ventana
pygame.display.set_caption("Condor Dash")  # Nombre de la ventana

# Fuentes
font = pygame.font.SysFont("ArialBlack", 32)
font_titulo = pygame.font.Font('Proyecto\Prototipos\Fonts\Titulo\ka1.ttf', 75)
font_boton = pygame.font.Font('Proyecto\Prototipos\Fonts\Texto\Righteous-Regular.ttf', 35)
font_texto = pygame.font.Font('Proyecto\Prototipos\Fonts\Texto\Righteous-Regular.ttf', 20)
font_texto_pequeño = pygame.font.Font('Proyecto\Prototipos\Fonts\Texto\Righteous-Regular.ttf', 15)
#font_titulo = pygame.font.SysFont("ArialBlack", 70)

# Extras
posiciones_ocupadas = set()     # Conjunto global para evitar superposiciones

### Cargar imágenes
condor_img = pygame.image.load('Proyecto\Prototipos\w_condor_v1.png')  # Carga de imagen
condor_img = pygame.transform.scale(condor_img, (60, 20))  # Escalado de imagen

menu_img = pygame.image.load('Proyecto\Prototipos\menu.png')

valle_img = pygame.image.load('Proyecto\Prototipos\w_valle_v1.png')
valle_img = pygame.transform.scale(valle_img, (2400, 600))

ciudad_img = pygame.image.load('Proyecto\Prototipos\w_ciudad_v1.png')
ciudad_img = pygame.transform.scale(ciudad_img, (2400, 600))

industria_img = pygame.image.load('Proyecto\Prototipos\w_industria_v1.png')
industria_img = pygame.transform.scale(industria_img, (2400, 600))

mina_img = pygame.image.load('Proyecto\Prototipos\w_mina_v1.png')
mina_img = pygame.transform.scale(mina_img, (2400, 600))

paloma_img = pygame.image.load('Proyecto\Prototipos\w_paloma_v1.png')
paloma_img = pygame.transform.scale(paloma_img, (65, 20))  

cfc_img = pygame.image.load('Proyecto\Prototipos\w_cfc_v1.png')
cfc_img = pygame.transform.scale(cfc_img, (150, 70))

texturas = {
    "recto": pygame.image.load("Proyecto\Prototipos\w_recto.png"),
    "esquina": pygame.image.load("Proyecto\Prototipos\w_esquina.png"),
    "bifurcacion": pygame.image.load("Proyecto\Prototipos\w_bifurcacion.png"),
    "cruce": pygame.image.load("Proyecto\Prototipos\w_cruce.png"),
    "extremo": pygame.image.load("Proyecto\Prototipos\w_extremo.png")
}

# Condor
class Condor:
    def __init__(self):
        self.posicionX = 150
        self.posicionY = ALTURA / 2
        self.velocidad_caida = VELOCIDAD_CAIDA
        self.velocidad_subida = VELOCIDAD_SUBIDA
        self.velocidad = 0
        self.altura = 20
        self.ancho = 60

    def ciclo(self, teclas, mouse):
        # Subida
        if teclas[pygame.K_SPACE] or mouse:
            self.velocidad += self.velocidad_subida
            self.posicionY += self.velocidad
        # Caida
        elif not (teclas[pygame.K_SPACE] or mouse):
            self.velocidad += self.velocidad_caida
            self.posicionY += self.velocidad

        # Limites entre techo y piso [0, 600]
        if self.posicionY < 0:  # Limite techo
            self.posicionY = 0      # Cte.
            self.velocidad = 0      # Reinicio de velocidad
        elif self.posicionY + self.altura > ALTURA - ALTURA_BASE:   # Limite piso
            self.posicionY = ALTURA - ALTURA_BASE - self.altura     # Cte.
            self.velocidad = 0                                      # Reinicio de velocidad 

    def render(self):
        screen.blit(condor_img, (self.posicionX, self.posicionY))

    def hitbox(self):
        return pygame.Rect(self.posicionX, self.posicionY, self.ancho, self.altura)


# Multijugador
class Servidor_local:
    def __init__(self, nombre_servidor, nombre_host):
        self.nombre_servidor = nombre_servidor
        self.nombre_host = nombre_host
        self.ip_local = self.obtener_ip()
        self.jugadores = {nombre_host: None}  # Diccionario de jugadores {nombre: socket}
        self.info_jugadores = []
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor_iniciado = False
        # Juego
        self.inicio_juego = False
        self.juego_multijugador = Juego_multijugador()
        self.tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Reduce la latencia de paquetes TCP

    def cambio_datos(self, serv, host):
        self.nombre_servidor_nuevo = serv
        self.nombre_host_nuevo = host

    def actualizacion_datos(self):
        while True:
            self.nombre_servidor = self.nombre_servidor_nuevo
            self.nombre_host = self.nombre_host_nuevo

    def obtener_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
        finally:
            s.close()

    def iniciar(self):
        if self.servidor_iniciado:
            return                              # Se evita multiples inicios
        self.servidor_iniciado = True           # Se marca como iniciado
        self.servidor_activo = True

        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind((self.ip_local, PUERTO_TCP))
        self.tcp_socket.listen(1)
        
        threading.Thread(target=self.actualizacion_datos, daemon=True).start()
        threading.Thread(target=self.enviar_anuncios, daemon=True).start()
        threading.Thread(target=self.aceptar_clientes, daemon=True).start()

    def enviar_anuncios(self):      # Mandar existencia del servidor
        mensaje = f"{self.nombre_servidor},{self.ip_local},{PUERTO_TCP}".encode()
        ip_broadcast = '192.168.100.255'        # OBLIGATORIO:  Cambiar por IP de broadcast (ver Notas.txt)

        while self.servidor_iniciado:       # Se va a detener cuando el servidor se cierre
            try:
                self.udp_socket.sendto(mensaje, (ip_broadcast, PUERTO_UDP))
            except OSError as e:
                print(f"Error en enviar_anuncios: {e}")
                break
            time.sleep(3)

    def aceptar_clientes(self):  # Aceptar jugadores
        try:
            while True:
                cliente, direccion = self.tcp_socket.accept()
                nombre = cliente.recv(1024).decode()
                if nombre in self.jugadores:
                    cliente.send(b"Nombre en uso")
                    cliente.close()
                else:
                    self.jugadores[nombre] = cliente
                    self.info_jugadores.append(nombre)
                    self.enviar_lista_jugadores()
                    print(f"{nombre} se ha unido desde {direccion}")
                    threading.Thread(target=self.manejar_cliente, args=(nombre, cliente), daemon=True).start()
        except OSError as e:
            print(f"⚠️ Error en aceptar_clientes: {e}")

    def manejar_cliente(self, nombre, cliente):
        try:
            while True:
                data = cliente.recv(4096)
                if not data:
                    print(f"❌ [DEBUG] Cliente {nombre} se desconectó.")
                    break
                
                try:
                    mensaje = data.decode("utf-8")
                except UnicodeDecodeError:
                    print(f"⚠️ [DEBUG] Datos binarios recibidos de {nombre}, ignorando...")
                    continue  # 🔹 No terminamos la conexión, solo ignoramos los datos

                print(f"📩 [DEBUG] Mensaje recibido de {nombre}: {mensaje}")

                if mensaje == "SALIR":
                    print(f"🔴 [DEBUG] {nombre} salió del servidor.")
                    break

        except Exception as e:
            print(f"⚠️ Error en manejar_cliente ({nombre}): {e}")
        finally:
            print(f"⚠️ [DEBUG] Cerrando conexión con {nombre}")
            if nombre in self.jugadores:
                del self.jugadores[nombre]
            if nombre in self.info_jugadores:
                self.info_jugadores.remove(nombre)  # Ahora sí se elimina correctamente
            self.enviar_lista_jugadores()
            cliente.close()

    def enviar_lista_jugadores(self):
        jugadores_str = ",".join(self.jugadores.keys())
        print("Enviando lista de jugadores:", jugadores_str)  # Debug
        for cliente in self.jugadores.values():
            if cliente:
                cliente.send(f"JUGADORES:{jugadores_str}".encode())
    
    def expulsar_jugador(self, nombre):
        if nombre in self.jugadores and nombre != self.nombre_host:
            print(f"🔴 Expulsando a {nombre}...")  # Debug para confirmar expulsión

            try:
                self.jugadores[nombre].sendall(b"EXPULSADO")  # 🔹 Enviar mensaje al cliente
                print(f"✅ Mensaje 'EXPULSADO' enviado a {nombre}")  # 🔹 Debug
                time.sleep(0.5)  # 🔹 Pequeña espera para asegurar envío
                self.jugadores[nombre].close()  # 🔹 Cerrar la conexión
            except Exception as e:
                print(f"⚠️ Error enviando EXPULSADO a {nombre}: {e}")

            # 🔹 Eliminar del diccionario solo si aún existe
            if nombre in self.jugadores:
                del self.jugadores[nombre]

            if nombre in self.info_jugadores:
                self.info_jugadores.remove(nombre)  # Eliminar de la lista de información

            self.enviar_lista_jugadores()  # 🔹 Actualizar la lista de jugadores
        else:
            print(f"⚠️ No se puede expulsar a {nombre}, no está en la lista de jugadores.")
    
    def cerrar_servidor(self):
        if not self.servidor_iniciado:
            return

        self.servidor_activo = False
        self.servidor_iniciado = False      # Se detiene enviar_anuncios

        try:
            self.tcp_socket.shutdown(socket.SHUT_RDWR)      # Apagado del socket antes del cierre
            self.udp_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
            #print("Fallo: socket esta cerrado")    # Fallo en caso el socket este cerrado

        self.tcp_socket.close()
        self.udp_socket.close()

        self.jugadores.clear()
        self.info_jugadores.clear()

        print("Servidor cerrado.")

    # Juego
    def iniciar_juego_servidor(self):
        """Inicia el bucle principal del juego, envío de datos y recepción de jugadores en hilos separados."""
        for cliente in list(self.jugadores.values()):
            if cliente:
                try:
                    cliente.sendall(b"INICIO")
                    print(f"✅ [DEBUG] Señal 'INICIO' enviada a {cliente}")  # Debug
                except Exception as e:
                    print(f"⚠️ [DEBUG] Error enviando 'INICIO': {e}")
        
        #self.juego_servidor(True)

        # 🔹 Hilo para enviar datos periódicamente
        hilo_envio = threading.Thread(target=self._enviar_datos_periodicamente, daemon=True)
        hilo_envio.start()
        print("📤 [DEBUG] Hilo de envío de datos iniciado.")

        # 🔹 Hilo para recibir actualizaciones de jugadores
        for nombre, cliente in list(self.jugadores.items()):
            if cliente:
                hilo_cliente = threading.Thread(target=self.recibir_actualizaciones_jugador, args=(nombre, cliente), daemon=True)
                hilo_cliente.start()
                print(f"📡 [DEBUG] Hilo de escucha para {nombre} iniciado.")

        # 🔹 Ejecutar el bucle del juego en el hilo principal
        self.juego_servidor(True)

    def enviar_estado_juego(self):
        """Envía el estado del juego a todos los clientes conectados."""
        if not self.jugadores:
            return
        
        # 🔹 Empaquetar el estado del juego
        game_state = pickle.dumps(self.juego_multijugador.empaquetado_datos())

        # 🔹 Agregar un encabezado con el tamaño del mensaje
        game_state_size = len(game_state).to_bytes(4, 'big')  # 4 bytes para el tamaño

        # 🔍 Debug: Verificar tamaño y datos
        print(f"📤 [DEBUG] Enviando {len(game_state)} bytes de datos...")

        # 🔹 Enviar a todos los clientes conectados
        for cliente in self.jugadores.values():
            if cliente:
                try:
                    cliente.sendall(game_state_size + game_state)  # 🔥 Enviar tamaño + datos
                except Exception as e:
                    print(f"❌ [ERROR] Enviando datos a un cliente: {e}")

    def recibir_actualizaciones_jugador(self, nombre, cliente):
        """Recibe las actualizaciones de un jugador y actualiza su estado en el juego."""
        try:
            while True:
                data = cliente.recv(1024)
                if not data:
                    break
                
                update_data = pickle.loads(data)
                if "x" in update_data and "y" in update_data:
                    self.juego_multijugador.posicion_personaje(nombre, update_data["x"], update_data["y"])
        except Exception as e:
            print(f"Error recibiendo datos de {nombre}: {e}")
        finally:
            if nombre in self.jugadores:
                cliente = self.jugadores.pop(nombre, None)  # 🔥 Eliminamos de `self.jugadores` y obtenemos el cliente
                if cliente:
                    cliente.close()

    def _enviar_datos_periodicamente(self):
        """Envía el estado del juego cada 50 ms."""
        while self.servidor_iniciado:
            self.enviar_estado_juego()
            time.sleep(0.05)

    def juego_servidor(self, estado_juego):

        # COLOCAR DENTRO EL MENU DE FINAL, QUEDARA EN BUCLE CON EL PRIMERO
        #if not self.menu.menu_fin_un_jugador_data():
         #   self.estado_juego = True

        self.juego_multijugador.reinicio_valores()     #!
        if estado_juego:

            while self.juego_multijugador.estado_juego:        #!
                self.juego_multijugador.clock.tick(FPS)
                self.tecla = pygame.key.get_pressed()                           # Teclas presionadas
                self.mouse = pygame.mouse.get_pressed()[0]                      # Botón izquierdo
                #self.menu = Menu(self.puntuacion.puntaje(), self.puntuacion.puntuacion_maxima())             # Actualización de la puntuación

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()

                # Generación de obstáculos dentro del escenario
                self.juego_multijugador.posicionX_escenarios += self.juego_multijugador.velocidad_escenarios     #!
                self.juego_multijugador.escenarios_spawn += 1                            #!

                # Obstaculos en servidor
                if self.juego_multijugador.escenarios[-1].estado_generacion_sv:        #!
                    self.juego_multijugador.objetos_sv.append(self.juego_multijugador.escenarios[-1].obstaculos[-1])   #!
                    # AGREGAR MAS

                # Modificación en la generación de escenarios            
                for escenario in self.juego_multijugador.escenarios:   #!
                    if escenario.fin():
                        self.juego_multijugador.estado_transicion = True   #!
                        self.juego_multijugador.aparicion_transicion() #!
                        # SV
                        self.juego_multijugador.transicion_sv = True       #!

                # Generacion de la transicion
                if self.juego_multijugador.estado_transicion:                  # Declarar al iniciar su aparicion  #!
                    self.juego_multijugador.transicion.ciclo()     #!
                    # SV    
                    self.juego_multijugador.transicion_sv = True           #!

                    # Cambio de escenario unico
                    if self.juego_multijugador.transicion.fin() and not self.juego_multijugador.situacion:    #!
                        clase_escenario = random.choice(self.juego_multijugador.clases_escenarios) #!
                        self.juego_multijugador.escenarios.append(clase_escenario(0, self.juego_multijugador.velocidad_escenarios, self.juego_multijugador.condor))  #!
                        self.juego_multijugador.escenarios.pop(0)  #!
                        self.juego_multijugador.situacion = True   # Evasion de otros cambios  #!
                        # SV
                        self.juego_multijugador.escenarios_sv.append(self.juego_multijugador.escenarios[0])       #!
                        self.juego_multijugador.escenarios_sv.pop(0)                           #!

                    # Eliminacion al terminar la transicion
                    if self.juego_multijugador.transicion.transicion_completada:   #!
                        self.juego_multijugador.transicion = None  #!
                        self.juego_multijugador.estado_transicion = False  #!
                        # SV
                        self.juego_multijugador.transicion_sv = False      #!

                # Ciclos de las clases
                self.juego_multijugador.puntuacion.ciclo()                             # Puntuacion    #!
                for escenario in self.juego_multijugador.escenarios:                   # Escenarios    #!
                    escenario.ciclo()
                    if escenario.valor_colision():                             # Deteccion de colision
                        self.juego_multijugador.reinicio_valores()                     # Reinicio  #!
                        self.juego_multijugador.estado_juego = False                   # Se apaga el bucle juego   #!

                        #if self.menu.menu_fin_un_jugador_data():            # Jugar otra vez
                         #   self.menu.menu_fin_un_jugador(False)                # Menu fin del juego
                          #  estado_juego = True
                           # self.estado_juego = True
                        #elif not self.menu.menu_fin_un_jugador_data():      # Volver menu
                         #   self.menu.menu_fin_un_jugador(False)                # Menu fin del juego
                        
                self.juego_multijugador.condor.ciclo(self.tecla, self.mouse)           # Condor    #!

                # Renderizado de elementos: escenarios -> obstáculos -> condor -> puntuacion
                for escenario in self.juego_multijugador.escenarios:   #!
                    escenario.render()
                self.juego_multijugador.condor.render()    #!
                if self.juego_multijugador.estado_transicion:  #!
                    self.juego_multijugador.transicion.render()    #!
                self.juego_multijugador.puntuacion.mostrar_puntaje()   #!

                # Actualizar pantalla
                pygame.display.update()
                pygame.display.flip()


                '''# Envio datos
                self._enviar_datos_periodicamente()
                for nombre, cliente in self.jugadores.items():
                    if cliente:
                        self.recibir_actualizaciones_jugador(nombre, cliente)'''

class Cliente_local:
    def __init__(self, nombre):
        self.nombre = nombre
        self.tcp_socket = None
        self.expulsion = False
        self.juego_multijugador = Juego_multijugador()
        # Data
        self.menu_pausado = False  # 🔹 Indica si el menú debe pausarse
        self.juego_pendiente = False

    def obtener_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
        finally:
            s.close()

    def buscar_servidores(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)   ###
        self.udp_socket.bind(("", PUERTO_UDP))
        self.udp_socket.settimeout(0.5)     ###
        print("Buscando servidores...")
        servidores = set()
        start_time = time.time()
        while time.time() - start_time < 3:
            try:
                #self.udp_socket.settimeout(1)
                data, addr = self.udp_socket.recvfrom(1024)
                nombre, ip, puerto = data.decode().split(",")
                servidores.add((nombre, ip, int(puerto)))
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Error: {e}")
                break
        return list(servidores)

    def buscar_servidor_manual(self, ip_manual):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(("", PUERTO_UDP))
        self.udp_socket.settimeout(0.5)
        print("Buscando servidor...")
        servidores = set()
        start_time = time.time()
        while time.time() - start_time < 3:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                nombre, ip, puerto = data.decode().split(",")
                if ip == ip_manual:
                    servidores.add((nombre, ip, int(puerto)))
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Error: {e}")
                break
        return list(servidores)

    def conectar_a_servidor(self, ip, puerto, DSM, CPU, CPP, UPU):
        self.jugadores_conectados_cliente = []
        
        # 🔹 Asegurar que el socket se crea correctamente antes de usarlo
        if not hasattr(self, "tcp_socket") or not isinstance(self.tcp_socket, socket.socket):
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.tcp_socket.connect((ip, puerto))
        self.tcp_socket.send(self.nombre.encode())
        print("✅ [DEBUG] Conectado al servidor como:", self.nombre)
        
        '''self.esperando_inicio = True  
        self.menu_espera_partida_local(DSM, CPU, CPP, UPU)
        
        # 🔹 Asegurar que se inicie `escuchar_servidor()`
        threading.Thread(target=self.escuchar_servidor, daemon=True).start()
        print("📡 [DEBUG] Hilo de escucha del servidor iniciado.")'''

        # 🔹 Asegurar que se inicie `escuchar_servidor()`
        hilo_escucha = threading.Thread(target=self.escuchar_servidor, daemon=True)
        hilo_escucha.start()

        if hilo_escucha.is_alive():
            print("📡 [DEBUG] Hilo de escucha del servidor iniciado correctamente.")
        else:
            print("⚠️ [ERROR] El hilo de escucha no se inició correctamente.")
    
    def escuchar_servidor(self):
        print("📡 [DEBUG] Escuchando mensajes del servidor...")  # ✅ Verifica que la función inicia correctamente
        try:
            while True:
                mensaje = self.tcp_socket.recv(1024).decode()
                print(f"📩 [DEBUG] Mensaje recibido del servidor: {mensaje}")  

                if not mensaje:
                    print("⚠️ [DEBUG] Conexión cerrada por el servidor.")
                    break  

                if mensaje.startswith("JUGADORES:"):
                    jugadores = mensaje.split(":")[1]
                    self.jugadores_conectados_cliente.append(jugadores)
                    print(f"Jugadores en la partida: {jugadores}")

                '''if mensaje == "EXPULSADO":
                    print("❌ Has sido expulsado del servidor.")  # 🔹 Confirmar que la expulsión es recibida
                    self.expulsion = True  # 🔹 Cambiar el estado de expulsión correctamente
                    self.esperando_inicio = False  # 🔹 Forzar cierre del menú de espera
                    self.tcp_socket.close()  # 🔹 Cerrar el socket para evitar errores
#                    self.salir_del_servidor()  # 🔹 Salir del servidor para cerrar la conexión
                    return  # 🔹 Salir de `escuchar_servidor()` para no seguir recibiendo datos'''

                if mensaje == "INICIO":   
                    print("✅ [DEBUG] Señal de inicio recibida, iniciando juego...")
                    
                    self.esperando_inicio = False
    
        except Exception as e:
            print(f"⚠️ Error al escuchar al servidor: {e}")

    def salir_del_servidor(self):
        self.jugadores_conectados_cliente = []
        if hasattr(self, "tcp_socket") and isinstance(self.tcp_socket, socket.socket):
            try:
                self.tcp_socket.send(b"SALIR")
                self.tcp_socket.close()
                self.tcp_socket = None  
            except OSError as e:
                print(f"⚠️ Error al cerrar socket: {e}")
        else:
            print("⚠️ Intento de cerrar un socket inexistente o inválido.")
        
        print("Has salido del servidor.")
        
        # 🔹 Asegurar que el menú de espera termine
        self.esperando_inicio = False
        self.menu_pausado = False  # Por si está en pausa

    # Juego
    def iniciar_juego_cliente(self):
        """Método para iniciar el juego en el cliente tras recibir la señal del servidor."""
        print("🎮 [DEBUG] Juego iniciado en el cliente, ejecutando hilos...")

        threading.Thread(target=self.recibir_datos_servidor, daemon=True).start()
        print("📡 [DEBUG] Hilo de recepción de datos iniciado.")

        threading.Thread(target=self.enviar_datos_jugador, daemon=True).start()
        print("📤 [DEBUG] Hilo de envío de datos del jugador iniciado.")

        # 🔥 SUPERPONER EL BUCLE DEL JUEGO AQUÍ
        self.juego_multijugador.juego_cliente(True)

    def recibir_datos_servidor(self):
        """Recibe y procesa el estado del juego desde el servidor antes y después del inicio."""
        try:
            while True:
                # 🔹 Primero, recibir los 4 bytes que indican el tamaño del mensaje
                data_size = self.tcp_socket.recv(4)
                if not data_size:
                    print("⚠️ [DEBUG] Conexión cerrada por el servidor.")
                    break  # 🔥 Si no hay datos, salimos del bucle
                
                # 🔹 Convertir los 4 bytes a un número entero
                msg_length = int.from_bytes(data_size, 'big')
                print(f"📥 [DEBUG] Esperando {msg_length} bytes de datos...")

                # 🔹 Recibir el mensaje completo en fragmentos
                data = b""
                while len(data) < msg_length:
                    packet = self.tcp_socket.recv(msg_length - len(data))
                    if not packet:
                        print("❌ [ERROR] Conexión interrumpida mientras recibía datos.")
                        return
                    data += packet  # 🔥 Acumular los datos recibidos

                print(f"📩 [DEBUG] Datos completos recibidos: {len(data)} bytes.")

                # 🔹 Intentar desempaquetar los datos
                try:
                    datos_juego = pickle.loads(data)
                    print(f"📥 [DEBUG] Datos desempaquetados correctamente: {datos_juego}")  # 🔍 Verificar contenido

                    # 🔹 Validar que los datos tengan la estructura esperada
                    if not isinstance(datos_juego, dict):
                        print(f"⚠️ [ERROR] Datos recibidos no son un diccionario. Tipo: {type(datos_juego)} - Contenido: {datos_juego}")
                        continue

                    # 🔹 Validar cada sección de los datos
                    if "escenarios" not in datos_juego or "objetos" not in datos_juego or "personajes" not in datos_juego:
                        print("⚠️ [ERROR] Datos incompletos, faltan claves esenciales.")
                        continue

                    # 🔹 Validar contenido
                    if datos_juego["escenarios"] == ["MANTENER"] and datos_juego["objetos"] == ["MANTENER"]:
                        print("⚠️ [DEBUG] Datos del juego están vacíos, esperando actualizaciones...")
                        continue  # 🔥 No procesamos datos vacíos, solo esperamos más datos

                    # 🔥 Procesar los datos si todo está bien
                    self.juego_multijugador.lectura_datos(datos_juego)

                except pickle.UnpicklingError:
                    print(f"❌ [ERROR] No se pudieron desempaquetar datos de juego: {e}")
                    return  # 🔥 Salimos si falla

        except Exception as e:
            print(f"❌ [ERROR] Recibiendo datos del servidor: {e}")
    
    def enviar_datos_jugador(self):
        """Envía la posición del jugador al servidor periódicamente."""
        try:
            while True:
                # 🔹 Obtener posición real del personaje en `Juego_multijugador`
                player_x = self.juego_multijugador.condor.posicionX
                player_y = self.juego_multijugador.condor.posicionY

                player_data = pickle.dumps({"x": player_x, "y": player_y})
                self.tcp_socket.sendall(player_data)
                time.sleep(0.05)  # Enviar datos cada 50ms
        except Exception as e:
            print(f"Error enviando datos al servidor: {e}")

    def finalizar_juego(self):
        print("🏁 Juego terminado, reactivando menú de espera...")
        self.menu_pausado = False  # 🔹 Reactivar el menú

    def menu_espera_partida_local(self, DSM, CPU, CPP, UPU):
        # Data
        self.datos_servidor_manual = [DSM]
        self.CP_username = CPU
        self.CP_partyname = CPP
        self.UP_username = UPU

        self.esperando_inicio = True  # Asegurar que inicie correctamente

        while self.esperando_inicio:  # 🔹 Ahora se puede detener al salir
            
            if self.menu_pausado:  # 🔹 Si está pausado, entra en espera
                print("⏸ Menú de espera pausado...")
                while self.menu_pausado:
                    time.sleep(0.1)         # 🔹 Espera sin consumir CPU innecesaria
                print("▶️ Menú de espera reanudado.")    

            '''if not self.esperando_inicio:  # 🔹 Si el juego ha iniciado, pausa el menú
                self.menu_pausado = True
                print("🔄 Menú pausado mientras el juego está en curso.")'''

            if self.juego_pendiente:
                print("🎮 Ejecutando juego_cliente() en el hilo principal...")
                self.juego_pendiente = False  # 🔹 Reseteamos la señal
                self.juego_multijugador.juego_cliente(True)  # 🔹 Ahora se ejecuta correctamente
                return  # 🔹 Salir del menú correctamente       

            if self.expulsion:  # 🔹 Detecta la expulsión dentro del bucle de eventos
                print("❌ Has sido expulsado. Cerrando menú de espera.")
                self.esperando_inicio = False  # 🔹 Detener el while
                return  # 🔹 Salir del menú inmediatamente
            
            # 🔹 Pruebas de debug
            #print("🕒 Menú de espera activo - Expulsion:", self.expulsion)

            screen.blit(menu_img, (0, 0))

            # Definir rectangulos y botones
            boton_salir = pygame.Rect(970, 510, 180, 40)       # Boton salir
            rectangulo_data = pygame.Rect(50, 50, 300, 500)     # Rectangulo fondo data
            rectangulo_personajes_out = pygame.Rect(ANCHO // 12 - 20, ALTURA // 2, 240, 220)        # Borde_out personajes
            rectangulo_personajes_in = pygame.Rect(ANCHO // 12, ALTURA // 2 + 20, 200, 180)         # Borde_in personajes
            rectangulo_host = pygame.Rect(450, 180, 700, 69)

            # Dibujar botones con efecto hover
            mouse_x, mouse_y = pygame.mouse.get_pos()
            color_salir = ROJO if boton_salir.collidepoint((mouse_x, mouse_y)) else GRIS

            # Jugadores
            for i in range(len(self.jugadores_conectados_cliente)):         # n-1  =  i
                # Rectangulos
                rectangulo_jugador = pygame.Rect(450, (77 * (i + 1)) + 180, 700, 69)
                # Efecto hover
                color_jugadores = AZUL_CLARO if rectangulo_jugador.collidepoint((mouse_x, mouse_y)) else AZUL
                # Render rectangulos
                pygame.draw.rect(screen, color_jugadores, rectangulo_jugador, border_radius=10)
                # Jugadores
                nombre_jugador = self.jugadores_conectados_cliente[i]
                # Texto jugadores
                texto_jugador = font_texto.render(f"{nombre_jugador}", True, BLANCO)
                # Render texto jugador
                screen.blit(texto_jugador, (500, (77 * (i + 1)) + 214 - (texto_jugador.get_height() // 2)))

            # Titulo
            titulo_texto = font_titulo.render("CONDOR DASH", True, NEGRO)
            screen.blit(titulo_texto, (((ANCHO - ANCHO // 3) // 2) + ANCHO // 3 - titulo_texto.get_width() // 2 - 25, 50))

            # Render figuras
            pygame.draw.rect(screen, color_salir, boton_salir, border_radius=10)
            pygame.draw.rect(screen, GRIS, rectangulo_data, border_radius=10)
            pygame.draw.rect(screen, NARANJA, rectangulo_personajes_out, border_radius=10)
            pygame.draw.rect(screen, GRIS_CLARO, rectangulo_personajes_in, border_radius=10)
            pygame.draw.rect(screen, AZUL, rectangulo_host, border_radius=10)     # Host

            # Render textos
            (nombre_servidor, ip, puerto) = self.datos_servidor_manual[0]               #!
            texto_salir = font_boton.render("SALIR", True, BLANCO)
            texto_personajes = font_texto.render("PERSONAJE:", True, BLANCO)
            texto_username = font_texto.render("USERNAME:", True, BLANCO)
            texto_nombre_username = font_texto.render(f"{self.UP_username}", True, BLANCO)          #!
            texto_partyname = font_texto.render("PARTY NAME:", True, BLANCO)
            texto_nombre_partyname = font_texto.render(f"{nombre_servidor}", True, BLANCO)
            texto_jugadores = font_texto.render("JUGADORES:", True, NEGRO)
            texto_IP = font_texto.render(f"IP: {self.obtener_ip()}", True, BLANCO)             # Ingresar IP
            texto_host = font_texto.render(f"{self.CP_username}", True, BLANCO)                     #{self.servidor.nombre_host}", True, BLANCO)        #!
            screen.blit(texto_salir, (boton_salir.x + (180 // 2) - (texto_salir.get_width() // 2), boton_salir.y + (40 // 2) - (texto_salir.get_height() // 2)))
            screen.blit(texto_personajes, ((ANCHO // 6) - texto_personajes.get_width() // 2, (ALTURA // 2) - (texto_personajes.get_height() * 1.25)))
            screen.blit(texto_jugadores, (430, 140))
            screen.blit(texto_username, ((ANCHO // 6) - texto_username.get_width() // 2, (ALTURA // 2) - (texto_username.get_height() * 4)))
            screen.blit(texto_nombre_username, (ANCHO // 12 + 100 - (texto_nombre_username.get_width() // 2), 245 - (texto_nombre_username.get_height() // 2)))
            screen.blit(texto_partyname, ((ANCHO // 6) - texto_partyname.get_width() // 2, (ALTURA // 2) - (texto_partyname.get_height() * 6.75)))
            screen.blit(texto_nombre_partyname, (ANCHO // 12 + 100 - (texto_nombre_partyname.get_width() // 2), 175 - (texto_nombre_partyname.get_height() // 2)))
            screen.blit(texto_IP, ((ANCHO // 6) - texto_IP.get_width() // 2, (ALTURA // 2) - (texto_IP.get_height() * 8.55)))
            screen.blit(texto_host, (500, 214 - (texto_host.get_height() // 2)))

            # Renderizado texto ingresado
            texto_partyname = font_texto.render(self.CP_partyname, True, BLANCO)            #!
            texto_username = font_texto.render(self.CP_username, True, BLANCO)              #!

            # Manejo de eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if boton_salir.collidepoint(event.pos):
                        self.salir_del_servidor()
                        self.esperando_inicio = False                           ###################
                        return

            pygame.display.flip()

        # 🔥 En este punto, el menú termina y el juego inicia en el **mismo bucle**
        print("🎮 [DEBUG] Menú de espera finalizado. Iniciando juego...")
        #self.juego_multijugador.juego_cliente(True)  # 🔹 SUPERPONER EL JUEGO
        self.iniciar_juego_cliente()  # 🔹 Iniciar el juego en el cliente


# Obstaculos
class Obstaculo:
    def __init__(self, posicionX, velocidad):
        self.posicionX = posicionX
        self.velocidad = velocidad

    def ciclo(self):
        self.posicionX -= self.velocidad

    def update(self):
        pass

class Paloma(Obstaculo):
    def __init__(self, posicionX, velocidad):
        super().__init__(posicionX, velocidad)
        self.altura = 20
        self.ancho = 65
        self.posicionY = random.randint(0, ALTURA - ALTURA_BASE - self.altura)

    def ciclo_basico(self):
        self.posicionX -= self.velocidad

    def render(self):
        screen.blit(paloma_img, (self.posicionX, self.posicionY))

    def render_basico(self):
        screen.blit(paloma_img, (self.posicionX, self.posicionY))

    def hitbox(self):
        return pygame.Rect(self.posicionX, self.posicionY, self.ancho, self.altura)
    
    def update(self):
        return {"x": self.posicionX, "y": self.posicionY, "velocidad": self.velocidad, "tipo_obstaculo": "Paloma"}
    
    '''@staticmethod
    def rt_update(data):
        obj = Paloma(posicionX=data["x"], velocidad=data["velocidad"])
        obj.posicionY = data["y"]
        return obj'''
    
    @staticmethod
    def rt_update(data):
        if not isinstance(data, dict):
            print(f"❌ [ERROR] `data` debe ser un diccionario, pero se recibió: {type(data)}")
            return None

        obj = Paloma(
            posicionX=data.get("x", ANCHO),  # 🔹 Si "x" no está, usa 0 por defecto
            velocidad=data.get("velocidad", VELOCIDAD_OBSTACULOS)  # 🔹 Si "velocidad" no está, usa 1
        )
        obj.posicionY = data.get("y", 0)  # 🔹 Si "y" no está, usa 0 por defecto
        return obj

class CFC(Obstaculo):
    def __init__(self, posicionX, velocidad):
        super().__init__(posicionX, velocidad)
        self.altura = 70
        self.ancho = 150
        self.posicionY = random.randint(0, ALTURA - ALTURA_BASE - self.altura)

    def ciclo_basico(self):
        self.posicionX -= self.velocidad

    def render(self):
        screen.blit(cfc_img, (self.posicionX, self.posicionY))

    def render_basico(self):
        screen.blit(cfc_img, (self.posicionX, self.posicionY))

    def hitbox(self):
        return pygame.Rect(self.posicionX, self.posicionY, self.ancho, self.altura)
    
    def update(self):
        return {"x": self.posicionX, "y": self.posicionY, "velocidad": self.velocidad, "tipo_obstaculo": "CFC"}

    @staticmethod
    def rt_update(data):
        obj = CFC(posicionX=data["x"], velocidad=data["velocidad"])
        obj.posicionY = data["y"]
        return obj

class Tuberias(Obstaculo):
    def __init__(self, posicionX, velocidad):
        super().__init__(posicionX, velocidad)
        self.segmento = 40  # Tamaño de cada segmento de tubería
        self.longitud = random.randint(7, 15)  # Mayor número de segmentos
        self.trayectoria = []
        self.red = False
        if not self.red:
            self.generar_trayectoria()      # Se llama inmediatamente al metodo para su ejecucion  /  mas eficiente y evita errores
    
    def generar_trayectoria(self):
        # Generacion en una cuadricula de 40x40
        x = (self.posicionX // self.segmento) * self.segmento
        y = random.choice([40, ALTURA - ALTURA_BASE - 40])
        
        for _ in range(self.longitud):              # Funcionamiento similar al for() de C, sin usar el valor variable (i=0, ... , i++)
            if (x, y) in posiciones_ocupadas:
                break  # Se evita agregar tuberias en posiciones ya ocupadas
            
            self.trayectoria.append((x, y))     #######
            posiciones_ocupadas.add((x, y))     # Se agregar la posición como ocupada
            
            opciones_direccion = ['derecha', 'abajo', 'izquierda', 'arriba']
            random.shuffle(opciones_direccion)      # Generacion aleatoria de las tuberias
            
            # Generacion sin superposiciones
            for nueva_direccion in opciones_direccion:
                nuevo_x, nuevo_y = x, y
                if nueva_direccion == 'derecha':
                    nuevo_x += self.segmento
                elif nueva_direccion == 'izquierda':
                    nuevo_x -= self.segmento
                elif nueva_direccion == 'abajo':
                    nuevo_y += self.segmento
                elif nueva_direccion == 'arriba':
                    nuevo_y -= self.segmento
                    
                # Verificacion de no superposicion ni salida de limites del jeugo
                if (nuevo_x, nuevo_y) not in posiciones_ocupadas and 0 <= nuevo_x < ANCHO and 0 <= nuevo_y < ALTURA - ALTURA_BASE:
                    x, y = nuevo_x, nuevo_y
                    break
        
        self.asignar_tipos()
    
    def asignar_tipos(self):
        # Determinacion del tipo de segmento segun sus conexiones (rectos, esquina, T, cruce, extremo)
        self.tipos = []
        posiciones = set(self.trayectoria)      
        
        # Calculo segmento por segmento de las tuberias
        for i, (x, y) in enumerate(self.trayectoria):
            # Se analiza los segmentos adyacentes a cada segmento
            conexiones = set()
            if (x + self.segmento, y) in posiciones:
                conexiones.add("derecha")
            if (x - self.segmento, y) in posiciones:
                conexiones.add("izquierda")
            if (x, y + self.segmento) in posiciones:
                conexiones.add("abajo")
            if (x, y - self.segmento) in posiciones:
                conexiones.add("arriba")
            
        ##### Determinacion del tipo de segmento #####
            ### Esquinas
            if conexiones == {"derecha", "abajo"}:
                self.tipos.append(("esquina", 270))
            elif conexiones == {"izquierda", "abajo"}:
                self.tipos.append(("esquina", 180))
            elif conexiones == {"izquierda", "arriba"}:
                self.tipos.append(("esquina", 90))
            elif conexiones == {"derecha", "arriba"}:
                self.tipos.append(("esquina", 0))

            ### Rectos
            elif conexiones == {"izquierda", "derecha"} or conexiones == {"arriba", "abajo"}:
                self.tipos.append(("recto", 0 if "izquierda" in conexiones else 90))

            ### T
            elif len(conexiones) == 3:
                if conexiones == {"arriba", "abajo", "izquierda"}:
                    self.tipos.append(("bifurcacion", 0))
                elif conexiones == {"arriba", "abajo", "derecha"}:
                    self.tipos.append(("bifurcacion", 180))
                elif conexiones == {"izquierda", "derecha", "abajo"}:
                    self.tipos.append(("bifurcacion", 90))
                elif conexiones == {"izquierda", "derecha", "arriba"}:
                    self.tipos.append(("bifurcacion", 270))
                else:
                    self.tipos.append(("bifurcacion", 0))

            ### Cruces
            elif len(conexiones) == 4:
                self.tipos.append(("cruce", 0))

            ### Extremos
            elif len(conexiones) == 1:  # Solo una conexión, es un extremo
                angulo = {"derecha": 0, "izquierda": 180, "arriba": 90, "abajo": 270}[list(conexiones)[0]]
                self.tipos.append(("extremo", angulo))
            
            ### Caso de error
            else:
                self.tipos.append(("recto", 0))
    
    def ciclo(self):
        # Movimiento de toda la tuberia
        self.trayectoria = [(x - self.velocidad, y) for x, y in self.trayectoria]

    def ciclo_basico(self):
        '''self.ciclo_sv(self, self.trayectoria, self.velocidad)
        self.hitbox_sv(self.trayectoria, self.segmento)'''
        self.ciclo()
        self.hitbox()

    def ciclo_sv(self, trayectoria, velocidad):
        trayectoria = [(x - velocidad, y) for x, y in trayectoria] 
    
    def render(self):
        # Dibujado de la tuberia completa con sus imagenes respectivas
        for i, (x, y) in enumerate(self.trayectoria):
            tipo, angulo = self.tipos[i] if i < len(self.tipos) else ("recto", 0)
            textura = pygame.transform.rotate(texturas[tipo], angulo)
            screen.blit(textura, (x + (ANCHO // 7.5), y))

    def render_basico(self):
        for i, (x, y) in enumerate(self.trayectoria):
            tipo, angulo = self.tipos[i] if i < len(self.tipos) else ("recto", 0)
            textura = pygame.transform.rotate(texturas[tipo], angulo)
            screen.blit(textura, (x + (ANCHO // 7.5), y))        
    
    def hitbox(self):
        return [pygame.Rect(x + (ANCHO // 7.5), y, self.segmento, self.segmento) for x, y in self.trayectoria]
    
    def hitbox_sv(self, trayectoria, segmento):
        return [pygame.Rect(x + (ANCHO // 7.5), y, segmento, segmento) for x, y in trayectoria]
    
    def update(self):
        return {"x": ANCHO, "tipo_obstaculo": "Tuberias", "trayectoria": self.trayectoria, "tipos": self.tipos, "segmento": self.segmento, "velocidad": self.velocidad}          # Pendiente

    @staticmethod
    def rt_update(data):
        obj = Tuberias(posicionX=data["x"], velocidad=data["velocidad"])
        obj.red = True
        obj.trayectoria = data["trayectoria"]
        obj.tipos = data["tipos"]
        obj.segmento = data["segmento"]
        return obj


# Escenarios
class Escenario:
    def __init__(self, posicionX, velocidad, condor):   # 2 ult.
        # Escenario
        self.posicionX = posicionX
        self.velocidad = velocidad
        #Obstaculos
        self.posicionX_obstaculos = ANCHO   ###
        self.obstaculos_permitidos = []
        self.obstaculos = []
        self.obstaculos_spawn = 0
        self.velocidad_obstaculos = VELOCIDAD_OBSTACULOS
        self.indice_obstaculo = 0
        # Extras
        self.condor = condor
        self.colision = False
        # SV
        self.estado_generacion_sv = False
        self.estado_borrado_sv = False

    def generar_obstaculo(self):
        if self.obstaculos_permitidos:  # Si hay obstáculos válidos
            # Aparicion de obstaculos en orden              /           Ajuste de complejidad de los escenarios
            self.indice_obstaculo = (self.indice_obstaculo + 1) % len(self.obstaculos_permitidos)
            ObstaculoClase = self.obstaculos_permitidos[self.indice_obstaculo]
            # Se agrega el obstaculo
            nuevo_obstaculo = ObstaculoClase(self.posicionX_obstaculos, self.velocidad_obstaculos)
            self.obstaculos.append(nuevo_obstaculo)

    def ciclo_basico(self):
        self.posicionX -= self.velocidad

        for obstaculo in self.obstaculos:
            obstaculo.ciclo_basico()
            hitboxes = obstaculo.hitbox()

            # Conversion de una unica hitbox a una lista
            if isinstance(hitboxes, pygame.Rect):
                hitboxes = [hitboxes]
            # Comprobacion de colision
            for hitbox in hitboxes:
                if pygame.Rect.colliderect(self.condor.hitbox(), hitbox):
                    self.colision = True

    def ciclo(self):
        self.estado_borrado_sv = False
        self.estado_generacion_sv = False
        self.posicionX -= self.velocidad

        # Generación de obstáculos dentro del escenario
        self.obstaculos_spawn += 1
        if self.obstaculos_spawn % INTERVALO_OBSTACULOS == 0:  # Intervalo de generación
            self.estado_generacion_sv = True
            self.generar_obstaculo()
        if self.obstaculos_spawn % 120 == 0:
            posiciones_ocupadas.clear()

        ### Pruebas
        #print(f"{len(self.obstaculos)}")

        # Mover los obstáculos dentro del escenario
        for obstaculo in self.obstaculos:
            obstaculo.ciclo()
            hitboxes = obstaculo.hitbox()

            # Conversion de una unica hitbox a una lista
            if isinstance(hitboxes, pygame.Rect):
                hitboxes = [hitboxes]
            # Comprobacion de colision
            for hitbox in hitboxes:
                if pygame.Rect.colliderect(self.condor.hitbox(), hitbox):
                    self.colision = True
                 
        # Eliminacion de obstaculos ya renderizados
            self.obstaculos = [o for o in self.obstaculos if o.posicionX > -100]
            for o in self.obstaculos:
                if o.posicionX > -100:
                    self.estado_borrado_sv = True

    def fin(self):
        # Fin del escenario
        if (self.posicionX - ANCHO) == -2400:
            return True
        else:
            return False

    def valor_colision(self):
        return self.colision
            
    def render(self):
        for obstaculo in self.obstaculos:
            obstaculo.render()

    def render_basico(self):
        for obstaculo in self.obstaculos:
            obstaculo.render_basico()

    def update(self):
        pass

class Transicion(Escenario):
    def __init__(self, posicionX, velocidad, condor, modo, cantidad, tiempo_espera):
        super().__init__(posicionX, velocidad, condor)
        self.modo = modo
        self.cantidad = cantidad
        self.imagen_original = pygame.image.load('Proyecto\Prototipos\w_transicion.png')
        self.rectangulos = []
        self.alpha = 255  # Opacidad inicial
        self.tiempo_espera = tiempo_espera # 0.25  # Tiempo antes de desvanecimiento
        self.tiempo_inicio = None
        self.transicion_completada = False
        self.obstaculos_permitidos = []
        
        for i in range(self.cantidad):
            if self.modo == 1:  # Rebote vertical
                ancho, alto = ANCHO // cantidad, ALTURA
                x = ancho * i
                y = -ALTURA - (ALTURA // cantidad) * i
            else:  # Rebote horizontal
                ancho, alto = ANCHO, ALTURA // self.cantidad
                x = ANCHO + (ANCHO // self.cantidad) * i
                y = alto * i
            
            imagen_escalada = pygame.transform.scale(self.imagen_original, (ancho, alto))
            self.rectangulos.append({"x": x, "y": y, "ancho": ancho, "alto": alto, "velocidad": 0, "rebotes": 0, "imagen": imagen_escalada})

    def ciclo(self):
        gravedad = 0.7              # Velocidad caida
        rebote_factor = -0.3        # Coef. de rebote
        
        for rect in self.rectangulos:
            rect["velocidad"] += gravedad
            if self.modo == 1:
                rect["y"] += rect["velocidad"]
                if rect["y"] + rect["alto"] >= ALTURA:
                    rect["y"] = ALTURA - rect["alto"]
                    rect["velocidad"] *= rebote_factor
                    rect["rebotes"] += 1
            else:
                rect["x"] -= rect["velocidad"]
                if rect["x"] <= 0:# or rect["x"] + rect["ancho"] >= ANCHO:
                    rect["x"] = max(0, min(ANCHO - rect["ancho"], rect["x"]))
                    rect["velocidad"] *= rebote_factor
                    rect["rebotes"] += 1
        
        # Desvanecimiento con la animacion completa
        if self.fin():
            if self.tiempo_inicio is None:
                self.tiempo_inicio = time.time()
            elif time.time() - self.tiempo_inicio >= self.tiempo_espera:
                if self.alpha > 0:
                    self.alpha -= 5  # Velocidad desvanecimietno
                    for rect in self.rectangulos:
                        rect["imagen"].set_alpha(self.alpha)
                else:
                    self.transicion_completada = True

    def fin(self):
        return all(rect["rebotes"] > 4 for rect in self.rectangulos)
    
    def render(self):
        for rect in self.rectangulos:
            screen.blit(rect["imagen"], (rect["x"], rect["y"]))

class Valle(Escenario):
    def __init__(self, posicionX, velocidad, condor):
        super().__init__(posicionX, velocidad, condor)
        self.imagen = valle_img
        self.obstaculos_permitidos = [Paloma]  # Solo aparecen palomas en el Valle

    def render(self):
        screen.blit(self.imagen, (self.posicionX, 0))
        super().render()

    def render_basico(self):
        screen.blit(self.imagen, (self.posicionX, 0))
        super().render_basico()

    def update(self):
        return {"x": self.posicionX, "velocidad": self.velocidad, "data1": self.condor, "tipo_escenario": "Valle"}

    @staticmethod
    def rt_update(data):
        obj = Valle(posicionX=data["x"], velocidad=data["velocidad"], condor=data["data1"])
        return obj

class Ciudad(Escenario):
    def __init__(self, posicionX, velocidad, condor):
        super().__init__(posicionX, velocidad, condor)
        self.imagen = ciudad_img
        self.obstaculos_permitidos = [Paloma, CFC, Paloma, Tuberias]  # Solo aparecen CFCs en la Ciudad

    def render(self):
        screen.blit(self.imagen, (self.posicionX, 0))
        super().render()

    def render_basico(self):
        screen.blit(self.imagen, (self.posicionX, 0))
        super().render_basico()

    def update(self):
        return {"x": self.posicionX, "velocidad": self.velocidad, "data1": self.condor, "tipo_escenario": "Ciudad"}

    @staticmethod
    def rt_update(data):
        obj = Ciudad(posicionX=data["x"], velocidad=data["velocidad"], condor=data["data1"])
        return obj

class Industria(Escenario):
    def __init__(self, posicionX, velocidad, condor):
        super().__init__(posicionX, velocidad, condor)
        self.imagen = industria_img
        self.obstaculos_permitidos = [CFC, Tuberias]  # Ambos obstáculos aparecen en Industria

    def render(self):
        screen.blit(self.imagen, (self.posicionX, 0))
        super().render()

    def render_basico(self):
        screen.blit(self.imagen, (self.posicionX, 0))
        super().render_basico()

    def update(self):
        return {"x": self.posicionX, "velocidad": self.velocidad, "data1": self.condor, "tipo_escenario": "Industria"}

    @staticmethod
    def rt_update(data):
        obj = Industria(posicionX=data["x"], velocidad=data["velocidad"], condor=data["data1"])
        return obj

class Mina(Escenario):
    def __init__(self, posicionX, velocidad, condor):
        super().__init__(posicionX, velocidad, condor)
        self.imagen = mina_img
        self.obstaculos_permitidos = [Tuberias]  # No hay obstáculos en la Mina

    def render(self):
        screen.blit(self.imagen, (self.posicionX, 0))
        super().render()

    def render_basico(self):
        screen.blit(self.imagen, (self.posicionX, 0))
        super().render_basico()

    def update(self):
        return {"x": self.posicionX, "velocidad": self.velocidad, "data1": self.condor, "tipo_escenario": "Mina"}

    @staticmethod
    def rt_update(data):
        obj = Mina(posicionX=data["x"], velocidad=data["velocidad"], condor=data["data1"])
        return obj


# Extras
class Menu:
    def __init__(self, puntuacion, puntaje_maximo):
        self.puntuacion = puntuacion
        self.puntaje_maximo = puntaje_maximo
        # Clase
        self.servidor = Servidor_local(None, None)
        # Estados botones
        self.estado_1 = False           # Juego:            un jugador
        self.estado_2 = True            # Volver a jugar:   un jugador

        # Data crear partida
        self.CP_username = "Host"
        self.CP_partyname = "Sala"
        # Data unirse partida
        self.UP_username = "Jugador"
        self.UP_IP = ""

    def reinicio(self):
        # Estados botones
        self.estado_1 = False           # Juego: un jugador
        self.estado_2 = False           

    def menu_principal(self):
        
        # Extras
        self.reinicio()

        screen.blit(menu_img, (0, 0))
        # Definir botones (x, y, ancho, alto)
        boton_jugar = pygame.Rect(ANCHO//2 - 100, 300, 200, 50)     # Altura 1er boton
        boton_salir = pygame.Rect(ANCHO//2 - 100, 400, 200, 50)     # Altura 2do boton

        # Titulo
        titulo_texto = font_titulo.render("CONDOR DASH", True, NEGRO)
        screen.blit(titulo_texto, (ANCHO // 2 - titulo_texto.get_width() // 2, ALTURA // 7))

        # Dibujar botones con efecto hover
        mouse_x, mouse_y = pygame.mouse.get_pos()
        color_jugar = AZUL if boton_jugar.collidepoint((mouse_x, mouse_y)) else GRIS
        color_salir = ROJO if boton_salir.collidepoint((mouse_x, mouse_y)) else GRIS

        # Render botones
        pygame.draw.rect(screen, color_jugar, boton_jugar, border_radius=10)
        pygame.draw.rect(screen, color_salir, boton_salir, border_radius=10)

        # Dibujar texto en los botones
        texto_jugar = font_boton.render("JUGAR", True, BLANCO)
        texto_salir = font_boton.render("SALIR", True, BLANCO)
        screen.blit(texto_jugar, (boton_jugar.x + (200 // 2) - (texto_jugar.get_width() // 2), boton_jugar.y + (50 // 2) - (texto_jugar.get_height() // 2)))
        screen.blit(texto_salir, (boton_salir.x + (200 // 2) - (texto_salir.get_width() // 2), boton_salir.y + (50 // 2) - (texto_salir.get_height() // 2)))

        # Manejo de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if boton_jugar.collidepoint(event.pos):
                    self.menu_jugar(True)
                if boton_salir.collidepoint(event.pos):
                    pygame.quit()
                    quit()

        pygame.display.flip()

    def menu_jugar(self, estado):
        while estado:
            screen.blit(menu_img, (0, 0))

            # Definir botones (x, y, ancho, alto)
            boton_un_jugador = pygame.Rect(ANCHO//2 - 150, 259, 300, 50)
            boton_multijugador = pygame.Rect(ANCHO//2 - 150, 359, 300, 50)
            boton_volver = pygame.Rect(ANCHO//2 - 150, 459, 300, 50)

            # Titulo
            titulo_texto = font_titulo.render("CONDOR DASH", True, NEGRO)
            screen.blit(titulo_texto, (ANCHO // 2 - titulo_texto.get_width() // 2, ALTURA // 7))

            # Dibujar botones con efecto hover
            mouse_x, mouse_y = pygame.mouse.get_pos()
            color_un_jugador = AZUL if boton_un_jugador.collidepoint((mouse_x, mouse_y)) else GRIS
            color_multijugador = AZUL if boton_multijugador.collidepoint((mouse_x, mouse_y)) else GRIS
            color_volver = ROJO if boton_volver.collidepoint((mouse_x, mouse_y)) else GRIS

            # Render botones
            pygame.draw.rect(screen, color_un_jugador, boton_un_jugador, border_radius=10)
            pygame.draw.rect(screen, color_multijugador, boton_multijugador, border_radius=10)
            pygame.draw.rect(screen, color_volver, boton_volver, border_radius=10)

            # Dibujar texto en los botones
            texto_un_jugador = font_boton.render("UN JUGADOR", True, BLANCO)
            texto_multijugador = font_boton.render("MULTIJUGADOR", True, BLANCO)
            texto_volver = font_boton.render("VOLVER", True, BLANCO)
            screen.blit(texto_un_jugador, (boton_un_jugador.x + (300 // 2) - (texto_un_jugador.get_width() // 2), boton_un_jugador.y + (50 // 2) - (texto_un_jugador.get_height() // 2)))
            screen.blit(texto_multijugador, (boton_multijugador.x + (300 // 2) - (texto_multijugador.get_width() // 2), boton_multijugador.y + (50 // 2) - (texto_multijugador.get_height() // 2)))
            screen.blit(texto_volver, (boton_volver.x + (300 // 2) - (texto_volver.get_width() // 2), boton_volver.y + (50 // 2) - (texto_volver.get_height() // 2)))

            # Manejo de eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if boton_un_jugador.collidepoint(event.pos):
                        self.estado_1 = True                        # Juego un jugador
                        estado = False
                        #self.juego.juego(True)

                    if boton_multijugador.collidepoint(event.pos):
                        self.menu_multijugador(True)
                    if boton_volver.collidepoint(event.pos):
                        estado = False

            pygame.display.flip()

    def menu_multijugador(self, estado):
        while estado:
            screen.blit(menu_img, (0, 0))

            # Definir botones (x, y, ancho, alto)
            boton_crear_juego_local = pygame.Rect(ANCHO//2 - 225, 259, 450, 50)
            boton_unirse_juego_local = pygame.Rect(ANCHO//2 - 225, 359, 450, 50)
            boton_volver = pygame.Rect(ANCHO//2 - 150, 459, 300, 50)

            # Titulo
            titulo_texto = font_titulo.render("CONDOR DASH", True, NEGRO)
            screen.blit(titulo_texto, (ANCHO // 2 - titulo_texto.get_width() // 2, ALTURA // 7))

            # Dibujar botones con efecto hover
            mouse_x, mouse_y = pygame.mouse.get_pos()
            color_un_jugador = AZUL if boton_crear_juego_local.collidepoint((mouse_x, mouse_y)) else GRIS
            color_multijugador = AZUL if boton_unirse_juego_local.collidepoint((mouse_x, mouse_y)) else GRIS
            color_volver = ROJO if boton_volver.collidepoint((mouse_x, mouse_y)) else GRIS

            # Render botones
            pygame.draw.rect(screen, color_un_jugador, boton_crear_juego_local, border_radius=10)
            pygame.draw.rect(screen, color_multijugador, boton_unirse_juego_local, border_radius=10)
            pygame.draw.rect(screen, color_volver, boton_volver, border_radius=10)

            # Dibujar texto en los botones
            texto_un_jugador = font_boton.render("CREAR PARTIDA LOCAL", True, BLANCO)
            texto_multijugador = font_boton.render("UNIRSE A PARTIDA LOCAL", True, BLANCO)
            texto_volver = font_boton.render("VOLVER", True, BLANCO)
            screen.blit(texto_un_jugador, (boton_crear_juego_local.x + (450 // 2) - (texto_un_jugador.get_width() // 2), boton_crear_juego_local.y + (50 // 2) - (texto_un_jugador.get_height() // 2)))
            screen.blit(texto_multijugador, (boton_unirse_juego_local.x + (450 // 2) - (texto_multijugador.get_width() // 2), boton_unirse_juego_local.y + (50 // 2) - (texto_multijugador.get_height() // 2)))
            screen.blit(texto_volver, (boton_volver.x + (300 // 2) - (texto_volver.get_width() // 2), boton_volver.y + (50 // 2) - (texto_volver.get_height() // 2)))

            # Manejo de eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if boton_crear_juego_local.collidepoint(event.pos):
                        self.menu_crear_partida_local(True)
                    if boton_unirse_juego_local.collidepoint(event.pos):
                        self.menu_unirse_partida_local(True)
                    if boton_volver.collidepoint(event.pos):
                        estado = False

            pygame.display.flip()

    def menu_crear_partida_local(self, estado):
        estado_partyname = False
        estado_username = False

        while estado:
            screen.blit(menu_img, (0, 0))

            # Data
            if hasattr(self, "servidor") and self.servidor.servidor_iniciado:
                self.servidor.cambio_datos(self.CP_partyname, self.CP_username)
                #print("Servidor en ejecucion")
            else:
                self.servidor = Servidor_local(self.CP_partyname, self.CP_username)
                self.servidor.iniciar()

            self.jugadores_conectados = len(self.servidor.info_jugadores)       # Num. jugadores conectados (externos)   :   0 < n < 4

            # Definir rectangulos y botones
            boton_volver = pygame.Rect(970, 510, 180, 40)       # Boton volver
            boton_jugar = pygame.Rect(450, 510, 180, 40)        # Boton iniciar
            rectangulo_data = pygame.Rect(50, 50, 300, 500)     # Rectangulo fondo data
            rectangulo_personajes_out = pygame.Rect(ANCHO // 12 - 20, ALTURA // 2, 240, 220)        # Borde_out personajes
            rectangulo_personajes_in = pygame.Rect(ANCHO // 12, ALTURA // 2 + 20, 200, 180)         # Borde_in personajes
            rectangulo_username_in = pygame.Rect(ANCHO // 12 - 20, 230, 240, 30)                    # Ingreso username
            rectangulo_partyname_in = pygame.Rect(ANCHO // 12 - 20, 160, 240, 30)                   # Ingreso partyname
            rectangulo_host = pygame.Rect(450, 180, 700, 69)
            botones_expulsar = []

            # Dibujar botones con efecto hover
            mouse_x, mouse_y = pygame.mouse.get_pos()
            color_volver = AMARILLO if boton_volver.collidepoint((mouse_x, mouse_y)) else GRIS
            color_jugar = VERDE if boton_jugar.collidepoint((mouse_x, mouse_y)) else GRIS
            color_partyname = GRIS_NEGRO if estado_partyname else GRIS_OSCURO
            color_username = GRIS_NEGRO if estado_username else GRIS_OSCURO

            # Jugadores
            for i in range(self.jugadores_conectados):         # n-1  =  i
                # Rectangulos
                rectangulo_jugador = pygame.Rect(450, (77 * (i + 1)) + 180, 700, 69)
                boton_expulsar = pygame.Rect(980, (77 * (i + 1)) + 197, 135, 35)
                # Botones expulsar
                botones_expulsar.append(boton_expulsar)
                # Texto
                texto_expulsar = font_texto.render("EXPULSAR", True, BLANCO)
                # Efecto hover
                color_jugadores = AZUL_CLARO if rectangulo_jugador.collidepoint((mouse_x, mouse_y)) else AZUL
                color_expulsar = ROJO if boton_expulsar.collidepoint((mouse_x, mouse_y)) else GRIS
                # Render rectangulos
                pygame.draw.rect(screen, color_jugadores, rectangulo_jugador, border_radius=10)
                pygame.draw.rect(screen, color_expulsar, boton_expulsar, border_radius=10)
                # Render texto
                screen.blit(texto_expulsar, (1047 - (texto_expulsar.get_width() // 2),  (77 * (i + 1)) + 214 - (texto_expulsar.get_height() // 2)))
                # Jugadores
                nombre_jugador = self.servidor.info_jugadores[i]
                # Texto jugadores
                texto_jugador = font_texto.render(f"{nombre_jugador}", True, BLANCO)
                # Render texto jugador
                screen.blit(texto_jugador, (500, (77 * (i + 1)) + 214 - (texto_jugador.get_height() // 2)))

            # Titulo
            titulo_texto = font_titulo.render("CONDOR DASH", True, NEGRO)
            screen.blit(titulo_texto, (((ANCHO - ANCHO // 3) // 2) + ANCHO // 3 - titulo_texto.get_width() // 2 - 25, 50))

            # Render figuras
            pygame.draw.rect(screen, color_volver, boton_volver, border_radius=10)
            pygame.draw.rect(screen, color_jugar, boton_jugar, border_radius=10)
            pygame.draw.rect(screen, GRIS, rectangulo_data, border_radius=10)
            pygame.draw.rect(screen, NARANJA, rectangulo_personajes_out, border_radius=10)
            pygame.draw.rect(screen, GRIS_CLARO, rectangulo_personajes_in, border_radius=10)
            pygame.draw.rect(screen, color_username, rectangulo_username_in, border_radius=10)     # Username
            pygame.draw.rect(screen, color_partyname, rectangulo_partyname_in, border_radius=10)    # Partyname
            pygame.draw.rect(screen, AZUL, rectangulo_host, border_radius=10)     # Host

            # Render textos
            texto_volver = font_boton.render("VOLVER", True, BLANCO)
            texto_jugar = font_boton.render("JUGAR", True, BLANCO)
            texto_personajes = font_texto.render("PERSONAJES:", True, BLANCO)
            texto_username = font_texto.render("USERNAME:", True, BLANCO)
            texto_partyname = font_texto.render("PARTY NAME:", True, BLANCO)
            texto_jugadores = font_texto.render("JUGADORES:", True, NEGRO)
            texto_IP = font_texto.render(f"IP: {self.servidor.ip_local}", True, BLANCO)             # Ingresar IP
            texto_host = font_texto.render(f"{self.CP_username}", True, BLANCO)                     #{self.servidor.nombre_host}", True, BLANCO)
            screen.blit(texto_volver, (boton_volver.x + (180 // 2) - (texto_volver.get_width() // 2), boton_volver.y + (40 // 2) - (texto_volver.get_height() // 2)))
            screen.blit(texto_jugar, (boton_jugar.x + (180 // 2) - (texto_jugar.get_width() // 2), boton_jugar.y + (40 // 2) - (texto_jugar.get_height() // 2)))
            screen.blit(texto_personajes, ((ANCHO // 6) - texto_personajes.get_width() // 2, (ALTURA // 2) - (texto_personajes.get_height() * 1.25)))
            screen.blit(texto_jugadores, (430, 140))
            screen.blit(texto_username, ((ANCHO // 6) - texto_username.get_width() // 2, (ALTURA // 2) - (texto_username.get_height() * 4)))
            screen.blit(texto_partyname, ((ANCHO // 6) - texto_partyname.get_width() // 2, (ALTURA // 2) - (texto_partyname.get_height() * 6.75)))
            screen.blit(texto_IP, ((ANCHO // 6) - texto_IP.get_width() // 2, (ALTURA // 2) - (texto_IP.get_height() * 8.55)))
            screen.blit(texto_host, (500, 214 - (texto_host.get_height() // 2)))

            # Renderizado texto ingresado
            texto_partyname = font_texto.render(self.CP_partyname, True, BLANCO)
            texto_username = font_texto.render(self.CP_username, True, BLANCO)
            screen.blit(texto_partyname, (rectangulo_partyname_in.x + 10, rectangulo_partyname_in.y + 15 - (texto_partyname.get_height() // 2)))
            screen.blit(texto_username, (rectangulo_username_in.x + 10, rectangulo_username_in.y + 15 - (texto_username.get_height() // 2)))
            
            # Manejo de eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if boton_jugar.collidepoint(event.pos):                                 #####################
                        print("Juegar")
                        self.servidor.iniciar_juego_servidor()
                    for i in range(len(botones_expulsar)):
                            if botones_expulsar[i].collidepoint(event.pos):
                                self.servidor.expulsar_jugador(self.servidor.info_jugadores[i])
                                print(f"Boton expulsar presionado: {i + 1}")
                    if boton_volver.collidepoint(event.pos):
                        for i in range(len(botones_expulsar)):
                            self.servidor.expulsar_jugador(self.servidor.info_jugadores[i])
                        self.servidor.cerrar_servidor()
                        estado = False

                    # Rectangulos partyname y username
                    if rectangulo_partyname_in.collidepoint(event.pos):
                        estado_partyname = True
                    if not rectangulo_partyname_in.collidepoint(event.pos):
                        estado_partyname = False

                    if rectangulo_username_in.collidepoint(event.pos):
                        estado_username = True
                    if not rectangulo_username_in.collidepoint(event.pos):
                        estado_username = False
                
                if event.type == pygame.KEYDOWN:
                    if estado_partyname:
                        if event.key == pygame.K_RETURN:
                            print(f"{self.CP_partyname}")
                        elif event.key == pygame.K_BACKSPACE:
                            self.CP_partyname = self.CP_partyname[:-1]
                        else:
                            self.CP_partyname += event.unicode

                    if estado_username:
                        if event.key == pygame.K_RETURN:
                            print(f"{self.CP_username}")
                        elif event.key == pygame.K_BACKSPACE:
                            self.CP_username = self.CP_username[:-1]
                        else:
                            self.CP_username += event.unicode

            pygame.display.flip()

    def menu_unirse_partida_local(self, estado): 
        #########################       Colocar en juego
        manual = True
        automatico = False
        #########################
        estado_busqueda_automatica = True       # Analizar una unica vez
        self.datos_servidores_automaticos = []
        estado_busqueda_manual = False
        self.datos_servidor_manual = []
        #########################
        estado_username = False
        estado_IP = False

        while estado:
            screen.blit(menu_img, (0, 0))

            # Data
            self.partidas_disponibles = 0       # Num. partidas disponibles     /     Default
            self.cliente = Cliente_local(self.UP_username)

            # Definir rectangulos y botones
            boton_volver = pygame.Rect(970, 510, 180, 40)           # Boton volver
            boton_manual = pygame.Rect(475, 140, 300, 35)           # Boton manual
            boton_automatico = pygame.Rect(825, 140, 300, 35)       # Boton automatico
            rectangulo_data = pygame.Rect(50, 50, 300, 500)         # Rectangulo fondo data
            rectangulo_personajes_out = pygame.Rect(ANCHO // 12 - 20, ALTURA // 2, 240, 220)        # Borde_out personajes
            rectangulo_personajes_in = pygame.Rect(ANCHO // 12, ALTURA // 2 + 20, 200, 180)         # Borde_in personajes
            rectangulo_username_in = pygame.Rect(ANCHO // 12 - 20, 190, 240, 30)                    # Ingreso username

            # Dibujar botones con efecto hover
            mouse_x, mouse_y = pygame.mouse.get_pos()
            color_volver = AMARILLO if boton_volver.collidepoint((mouse_x, mouse_y)) else GRIS
            color_manual = AMARILLO if boton_manual.collidepoint((mouse_x, mouse_y)) else GRIS
            color_automatico = AMARILLO if boton_automatico.collidepoint((mouse_x, mouse_y)) else GRIS
            color_username = GRIS_NEGRO if estado_username else GRIS_OSCURO

            # Titulo
            titulo_texto = font_titulo.render("CONDOR DASH", True, NEGRO)
            screen.blit(titulo_texto, (((ANCHO - ANCHO // 3) // 2) + ANCHO // 3 - titulo_texto.get_width() // 2 - 25, 50))

            # Render figuras
            pygame.draw.rect(screen, color_volver, boton_volver, border_radius=10)
            pygame.draw.rect(screen, color_manual, boton_manual, border_radius=10)
            pygame.draw.rect(screen, color_automatico, boton_automatico, border_radius=10)
            pygame.draw.rect(screen, GRIS, rectangulo_data, border_radius=10)
            pygame.draw.rect(screen, NARANJA, rectangulo_personajes_out, border_radius=10)
            pygame.draw.rect(screen, GRIS_CLARO, rectangulo_personajes_in, border_radius=10)
            pygame.draw.rect(screen, color_username, rectangulo_username_in, border_radius=10)     # Username

            # Render textos
            texto_volver = font_boton.render("VOLVER", True, BLANCO)
            texto_manual = font_texto.render("MANUAL", True, BLANCO)
            texto_automatico = font_texto.render("AUTOMATICO", True, BLANCO)
            texto_personajes = font_texto.render("PERSONAJES:", True, BLANCO)
            texto_username = font_texto.render("USERNAME:", True, BLANCO)
            texto_IP = font_texto.render(f"IP: {self.servidor.ip_local}", True, BLANCO)          # Ingresar IP
            screen.blit(texto_volver, (boton_volver.x + (180 // 2) - (texto_volver.get_width() // 2), boton_volver.y + (40 // 2) - (texto_volver.get_height() // 2)))
            screen.blit(texto_manual, (boton_manual.x + (300 // 2) - (texto_manual.get_width() // 2), boton_manual.y + 17 - (texto_manual.get_height() // 2)))
            screen.blit(texto_automatico, (boton_automatico.x + (300 // 2) - (texto_automatico.get_width() // 2), boton_automatico.y + 17 - (texto_automatico.get_height() // 2)))
            screen.blit(texto_personajes, ((ANCHO // 6) - texto_personajes.get_width() // 2, (ALTURA // 2) - (texto_personajes.get_height() * 1.25)))
            screen.blit(texto_username, ((ANCHO // 6) - texto_username.get_width() // 2, (ALTURA // 2) - (texto_username.get_height() * 5.5)))
            screen.blit(texto_IP, ((ANCHO // 6) - texto_IP.get_width() // 2, (ALTURA // 2) - (texto_IP.get_height() * 8.55)))

            # Renderizado texto ingresado
            texto_username = font_texto.render(self.UP_username, True, BLANCO)
            screen.blit(texto_username, (rectangulo_username_in.x + 10, rectangulo_username_in.y + 15 - (texto_username.get_height() // 2)))

            # Modo manual (excepciones)
            rectangulo_IP_in = pygame.Rect(650, 224, 301, 35)
            boton_buscar = pygame.Rect(940, 224, 110, 35)

            # Manejo de eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Boton manual
                    if boton_manual.collidepoint(event.pos):
                        manual = True
                        automatico = False
                        estado_busqueda_automatica = False      # Busqueda manual servidores
                    # Boton automatico
                    if boton_automatico.collidepoint(event.pos):
                        botones_unirse = []
                        manual = False
                        automatico = True
                        estado_busqueda_automatica = True       # Busqueda automatica servidores
                        estado_busqueda_manual = False
                    # Boton volver
                    if boton_volver.collidepoint(event.pos):
                        self.partidas_disponibles = 0
                        estado = False
                    # Ingreso username
                    if rectangulo_username_in.collidepoint(event.pos):
                        estado_username = True
                    if not rectangulo_username_in.collidepoint(event.pos):
                        estado_username = False
                    # Ingreso IP
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if rectangulo_IP_in.collidepoint(event.pos):
                            estado_IP = True
                        if not rectangulo_IP_in.collidepoint(event.pos):
                            estado_IP = False
                    # Boton buscar manual
                        if boton_buscar.collidepoint(event.pos):
                            estado_busqueda_manual = True
                    # Boton unirse manual
                    if estado_boton_unirse_manual:
                        if boton_unirse_manual.collidepoint(event.pos):
                            self.cliente.conectar_a_servidor(self.UP_IP, PUERTO_TCP, self.datos_servidor_manual[0], self.CP_username, self.CP_partyname, self.UP_username)
                            print("Boton unirse manual ACTIVO")
                            self.cliente.menu_espera_partida_local(self.datos_servidor_manual[0], self.CP_username, self.CP_partyname, self.UP_username)
                    # Boton unirse automaticamente
                    if estado_boton_unirse_automatico:
                        # Ingresar botones
                        for i in range(len(botones_unirse)):
                            if botones_unirse[i].collidepoint(event.pos):
                                (nombre_servidor, ip, puerto) = self.datos_servidores_automaticos[i]
                                self.cliente.conectar_a_servidor(ip, PUERTO_TCP, self.datos_servidor_manual[0], self.CP_username, self.CP_partyname, self.UP_username)
                                print(f"Boton presionado: {i + 1}")

                # Ingreso texto
                if event.type == pygame.KEYDOWN:
                    if estado_username:
                        if event.key == pygame.K_RETURN:
                            print(f"{self.UP_username}")
                        elif event.key == pygame.K_BACKSPACE:
                            self.UP_username = self.UP_username[:-1]
                        else:
                            self.UP_username += event.unicode
                    
                    if estado_IP:
                        if event.key == pygame.K_RETURN:
                            print(f"{self.UP_IP}")
                        elif event.key == pygame.K_BACKSPACE:
                            self.UP_IP = self.UP_IP[:-1]
                        else:
                            self.UP_IP += event.unicode

            # Boton manual
            if manual:
                # Partidas manuales
                # Rectangulos
                rectangulo_IP = pygame.Rect(550, 224, 110, 35)
                # Texto
                texto_IP_in = font_texto.render("IP", True, BLANCO)
                texto_buscar = font_texto.render("BUSCAR", True, BLANCO)
                # Efecto hover
                color_buscar = VERDE if boton_buscar.collidepoint((mouse_x, mouse_y)) else GRIS
                color_IP = GRIS_OSCURO if estado_IP else GRIS
                # Render rectangulos
                pygame.draw.rect(screen, GRIS, rectangulo_IP, border_radius=10)
                pygame.draw.rect(screen, color_buscar, boton_buscar, border_radius=10)
                pygame.draw.rect(screen, color_IP, rectangulo_IP_in)
                pygame.draw.line(screen, GRIS_OSCURO, (650, 229), (650, 254), 2)
                pygame.draw.line(screen, GRIS_OSCURO, (950, 229), (950, 254), 2)
                # Render texto
                screen.blit(texto_IP_in, (600 - (texto_IP_in.get_width() // 2), 224 + 17 - (texto_IP_in.get_height() // 2)))
                screen.blit(texto_buscar, (1000 - (texto_buscar.get_width() // 2), 224 + 17 - (texto_buscar.get_height() // 2)))
                # Render texto ingresado
                texto_IP = font_texto.render(self.UP_IP, True, BLANCO)
                screen.blit(texto_IP, (rectangulo_IP_in.x + 10, rectangulo_IP_in.y + 17 - (texto_IP.get_height() // 2)))
                # Data
                estado_boton_unirse_automatico = False
                botones_unirse = []
                     
                # Buscando servidor
                if estado_busqueda_manual:
                    self.datos_servidor_manual = self.cliente.buscar_servidor_manual(self.UP_IP)
                    estado_busqueda_manual = False

                # Caso True:
                if len(self.datos_servidor_manual) != 0:
                    # Estado boton unirse
                    estado_boton_unirse_manual = True
                    
                    (nombre_servidor, ip, puerto) = self.datos_servidor_manual[0]
                    # Texto
                    texto_nombre_servidor = font_texto.render(f"{nombre_servidor}", True, BLANCO)
                    texto_ip = font_texto.render(f"{ip}", True, BLANCO)
                    # Rectangulos
                    rectangulo_partida = pygame.Rect(450, 300, 700, 69)
                    boton_unirse_manual = pygame.Rect(980, 300 + 17, 135, 35)          ######''''''######
                    texto_unirse = font_texto.render("UNIRSE", True, BLANCO)
                    # Efecto hover
                    color_partidas = AZUL_CLARO if rectangulo_partida.collidepoint((mouse_x, mouse_y)) else AZUL
                    color_unirse = VERDE if boton_unirse_manual.collidepoint((mouse_x, mouse_y)) else GRIS
                    # Render rectangulos
                    pygame.draw.rect(screen, color_partidas, rectangulo_partida, border_radius=10)
                    pygame.draw.rect(screen, color_unirse, boton_unirse_manual, border_radius=10)
                    # Render texto
                    screen.blit(texto_unirse, (1047 - (texto_unirse.get_width() // 2),  334 - (texto_unirse.get_height() // 2)))
                    screen.blit(texto_nombre_servidor, (500, 334 - (texto_nombre_servidor.get_height() // 2)))
                    screen.blit(texto_ip, (950 - texto_ip.get_width(), 334 - (texto_ip.get_height() // 2)))

                if len(self.datos_servidor_manual) == 0:
                    # Estado boton unirse
                    estado_boton_unirse_manual = False

                    texto_error = font_texto.render("¡NO SE ENCONTRARON PARTIDAS DISPONIBLES!", True, NEGRO)
                    # Render texto
                    screen.blit(texto_error, (800 - (texto_error.get_width() // 2), 315))

            # Boton automatico
            if automatico:
                # Buscando servidores
                if estado_busqueda_automatica:
                    self.datos_servidores_automaticos = self.cliente.buscar_servidores()
                    estado_busqueda_automatica = False
                self.partidas_disponibles = len(self.datos_servidores_automaticos)
                # Data
                estado_IP = False
                estado_boton_unirse_manual = False
                botones_unirse = []
                
                # Partidas automaticas
                if self.partidas_disponibles != 0:
                    
                    # Estado boton unirse
                    estado_boton_unirse_automatico = True

                    for i in range(self.partidas_disponibles):         # n-1  =  i
                        # Rectangulos
                        rectangulo_partida = pygame.Rect(450, (77 * (i + 1)) + 113, 700, 69)
                        boton_unirse = pygame.Rect(980, (77 * (i + 1)) + 130, 135, 35)              ######''''''######
                        # Botones unirse
                        botones_unirse.append(boton_unirse)
                        
                        # Prueba
                        #print(f"{len(botones_unirse)}")

                        # Texto
                        texto_unirse = font_texto.render("UNIRSE", True, BLANCO)
                        # Efecto hover
                        color_partidas = AZUL_CLARO if rectangulo_partida.collidepoint((mouse_x, mouse_y)) else AZUL
                        color_unirse = VERDE if boton_unirse.collidepoint((mouse_x, mouse_y)) else GRIS
                        # Render rectangulos
                        pygame.draw.rect(screen, color_partidas, rectangulo_partida, border_radius=10)
                        pygame.draw.rect(screen, color_unirse, boton_unirse, border_radius=10)
                        # Render texto
                        screen.blit(texto_unirse, (1047 - (texto_unirse.get_width() // 2),  (77 * (i + 1)) + 147 - (texto_unirse.get_height() // 2)))

                        (nombre_servidor, ip, puerto) = self.datos_servidores_automaticos[i]
                        # Texto
                        texto_nombre_servidor = font_texto.render(f"{nombre_servidor}", True, BLANCO)
                        texto_ip = font_texto.render(f"{ip}", True, BLANCO)
                        # Render texto
                        screen.blit(texto_nombre_servidor, (500 ,  (77 * (i + 1)) + 147 - (texto_nombre_servidor.get_height() // 2)))
                        screen.blit(texto_ip, (950 - texto_ip.get_width(),  (77 * (i + 1)) + 147 - (texto_ip.get_height() // 2)))

                if self.partidas_disponibles == 0:
                    # Estado boton unirse
                    estado_boton_unirse_automatico = False

                    texto_error = font_texto.render("¡NO SE ENCONTRARON PARTIDAS DISPONIBLES!", True, NEGRO)
                    # Render texto
                    screen.blit(texto_error, (800 - (texto_error.get_width() // 2), 315))

            pygame.display.flip()

    def menu_fin_un_jugador(self, estado):
        while estado:
            screen.blit(menu_img, (0, 0))

            # Fuentes
            font_titulo = pygame.font.Font('Proyecto\Prototipos\Fonts\Titulo\ka1.ttf', 75)
            font_boton = pygame.font.Font('Proyecto\Prototipos\Fonts\Texto\Righteous-Regular.ttf', 35)

            # Definir botones (x, y, ancho, alto)
            boton_jugar = pygame.Rect(ANCHO//2 - 150, 320, 300, 50)     # Altura 1er boton
            boton_volver = pygame.Rect(ANCHO//2 - 100, 400, 200, 50)     # Altura 2do boton

            # Titulo
            titulo_texto = font_titulo.render("CONDOR DASH", True, NEGRO)
            screen.blit(titulo_texto, (ANCHO // 2 - titulo_texto.get_width() // 2, ALTURA // 7))

            # Obtener posición del mouse
            mouse_x, mouse_y = pygame.mouse.get_pos()

            # Dibujar botones con efecto hover
            color_jugar = AZUL if boton_jugar.collidepoint((mouse_x, mouse_y)) else GRIS
            color_volver = ROJO if boton_volver.collidepoint((mouse_x, mouse_y)) else GRIS

            # Render botones
            pygame.draw.rect(screen, color_jugar, boton_jugar, border_radius=10)
            pygame.draw.rect(screen, color_volver, boton_volver, border_radius=10)

            # Dibujar texto en los botones
            texto_jugar = font_boton.render("VOLVER A JUGAR", True, BLANCO)
            texto_volver = font_boton.render("VOLVER", True, BLANCO)
            #texto_perdiste = font_boton.render("PERDISTE", True, BLANCO)
            texto_puntuacion = font_boton.render(f"PUNTUACION: {self.puntuacion}", True, NEGRO)
            screen.blit(texto_jugar, (boton_jugar.x + (300 // 2) - (texto_jugar.get_width() // 2), boton_jugar.y + (50 // 2) - (texto_jugar.get_height() // 2)))
            screen.blit(texto_volver, (boton_volver.x + (200 // 2) - (texto_volver.get_width() // 2), boton_volver.y + (50 // 2) - (texto_volver.get_height() // 2)))
            screen.blit(texto_puntuacion, (boton_jugar.x + (300 // 2) - (texto_puntuacion.get_width() // 2), boton_jugar.y - texto_puntuacion.get_height() - 20))

            # Manejo de eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if boton_jugar.collidepoint(event.pos):
                        estado = False
                        self.estado_2 = True
                    if boton_volver.collidepoint(event.pos):
                        estado = False
                        self.estado_2 = False
                        self.estado_1 = False

            pygame.display.flip()

    def menu_fin_un_jugador_data(self):
        return self.estado_2

class Puntuacion:
    def __init__(self, velocidad):
        self.distanciaX = 0
        self.velocidad = velocidad
        self.puntuacion = 0
        with open('Proyecto\Prototipos\CD_P.txt', 'r') as leer_puntaje:
            self.puntaje_maximo = int(leer_puntaje.read())

    def ciclo(self):
        self.distanciaX += self.velocidad
        self.puntuacion = self.distanciaX // 10

        if self.puntuacion > self.puntaje_maximo:
            self.puntaje_maximo = self.puntuacion
            with open('Proyecto\Prototipos\CD_P.txt', 'w') as escribir_puntaje:
                escribir_puntaje.write(f"{self.puntaje_maximo}") 

    def reinicio_puntaje(self):
        self.distanciaX = 0
        self.puntuacion = 0

    def reinicio_puntaje_maximo(self):
        with open('Proyecto\Prototipos\CD_P.txt', 'w') as escribir_puntaje:
            escribir_puntaje.write(f"0")         

    def puntaje(self):
        return self.puntuacion
    
    def puntuacion_maxima(self):
        return self.puntaje_maximo
    
    def mostrar_puntaje(self):
        puntuacion_texto = font.render(f"Puntaje: {self.puntuacion}", True, NEGRO)
        screen.blit(puntuacion_texto, (puntuacion_texto.get_width() // 8, puntuacion_texto.get_height() // 4))


# Juego
class Juego:
    def __init__(self):
        # Escenarios
        self.posicionX_escenarios = 0       ###
        self.escenarios = []
        self.escenarios_spawn = 0
        self.velocidad_escenarios = VELOCIDAD_ESCENARIOS
        # Transicion
        self.transicion = None              
        self.indice_escenario = 0          
        self.estado_transicion = False      
        self.situacion = False              # Cambio
        # Clases
            # Personaje
        self.condor = Condor()
            # Escenarios
        self.clases_escenarios = [Valle, Ciudad, Industria, Mina]
            # Extras
        self.puntuacion = Puntuacion(self.velocidad_escenarios)
        self.menu = Menu(self.puntuacion.puntaje(), self.puntuacion.puntuacion_maxima())    
        # Juego
        self.estado_juego = True
        self.clock = pygame.time.Clock()
        # Escenario 1
        self.escenarios.append(Valle(self.posicionX_escenarios, self.velocidad_escenarios, self.condor))

    # Reinicio de valores
    def reinicio_valores(self):
        # Escenarios
        self.posicionX_escenarios = 0
        self.escenarios = []
        self.escenarios_spawn = 0
        self.velocidad_escenarios = VELOCIDAD_ESCENARIOS
        # Transicion
        self.transicion = None              
        self.indice_escenario = 0          
        self.estado_transicion = False      
        self.situacion = False
        # Obstaculos
        posiciones_ocupadas.clear()
        # Puntuacion
        self.puntuacion.reinicio_puntaje()
        # Juego
        self.estado_juego = True
        self.escenarios.append(Valle(self.posicionX_escenarios, self.velocidad_escenarios, self.condor))

    def aparicion_transicion(self):
        if self.puntuacion.puntaje() >= 750:       
            self.transicion = Transicion(None, None, None, 2, 5, 0.05)         # Cambios
        elif self.puntuacion.puntaje() < 750:
            self.transicion = Transicion(None, None, None, 1, 10, 0.2)        # Cambios

        self.estado_transicion = True
        self.situacion = False      # Reestablecimiento

    def puntuacion_actual(self):
        return self.puntuacion.puntaje()
    
    def puntuacion_maxima(self):
        return self.puntuacion.puntuacion_maxima()

    # Juego
    def juego(self, estado_juego):

        # COLOCAR DENTRO EL MENU DE FINAL, QUEDARA EN BUCLE CON EL PRIMERO
        if not self.menu.menu_fin_un_jugador_data():
            self.estado_juego = True

        self.reinicio_valores()
        if estado_juego:

            while self.estado_juego:
                self.clock.tick(FPS)
                self.tecla = pygame.key.get_pressed()                           # Teclas presionadas
                self.mouse = pygame.mouse.get_pressed()[0]                      # Botón izquierdo
                self.menu = Menu(self.puntuacion.puntaje(), self.puntuacion.puntuacion_maxima())             # Actualización de la puntuación       #############

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()

                # Generacion de los escenarios          ### Debatiendo

                # Generación de obstáculos dentro del escenario
                self.posicionX_escenarios += self.velocidad_escenarios
                self.escenarios_spawn += 1

                # Modificación en la generación de escenarios            
                for escenario in self.escenarios:
                    if escenario.fin():
                        self.estado_transicion = True
                        self.aparicion_transicion()

                # Generacion de la transicion
                if self.estado_transicion:                  # Declarar al iniciar su aparicion
                    self.transicion.ciclo()

                    # Cambio de escenario unico
                    if self.transicion.fin() and not self.situacion:
                        clase_escenario = random.choice(self.clases_escenarios)
                        self.escenarios.append(clase_escenario(0, self.velocidad_escenarios, self.condor))
                        self.escenarios.pop(0)
                        self.situacion = True   # Evasion de otros cambios

                    # Eliminacion al terminar la transicion
                    if self.transicion.transicion_completada:
                        self.transicion = None
                        self.estado_transicion = False


                # Eliminacion de escenarios ya renderizados
                #self.escenarios = [e for e in self.escenarios if e.posicionX > -ANCHO_ESCENARIOS]

                # Ciclos de las clases
                self.puntuacion.ciclo()                             # Puntuacion
                for escenario in self.escenarios:                   # Escenarios
                    escenario.ciclo()
                    if escenario.valor_colision():                             # Deteccion de colision
                        self.menu.menu_fin_un_jugador(True)         # Aparece menu final
                        self.reinicio_valores()                     # Reinicio
                        self.estado_juego = False                   # Se apaga el bucle juego

                        if self.menu.menu_fin_un_jugador_data():            # Jugar otra vez
                            self.menu.menu_fin_un_jugador(False)                # Menu fin del juego
                            estado_juego = True
                            self.estado_juego = True
                        elif not self.menu.menu_fin_un_jugador_data():      # Volver menu
                            self.menu.menu_fin_un_jugador(False)                # Menu fin del juego
                        
                self.condor.ciclo(self.tecla, self.mouse)           # Condor

                # Renderizado de elementos: escenarios -> obstáculos -> condor -> puntuacion
                for escenario in self.escenarios:
                    escenario.render()
                    #print(f"{escenario.posicionX}")                                                         ### Prueba
                self.condor.render()
                if self.estado_transicion:
                    self.transicion.render()
                self.puntuacion.mostrar_puntaje()

                # Actualizar pantalla
                pygame.display.flip()

                ### Pruebas:
                print(f"{self.escenarios}") 


class Juego_multijugador:           # Servidor
    def __init__(self):
        # Escenarios
        self.posicionX_escenarios = 0       ###
        self.escenarios = []
        self.escenarios_spawn = 0
        self.velocidad_escenarios = VELOCIDAD_ESCENARIOS
        # Transicion
        self.transicion = None              
        self.indice_escenario = 0          
        self.estado_transicion = False      
        self.situacion = False              # Cambio
        # Clases
            # Personaje
        self.condor = Condor()
            # Escenarios
        self.clases_escenarios = [Valle, Ciudad, Industria, Mina]
            # Extras
        self.puntuacion = Puntuacion(self.velocidad_escenarios)
        #self.menu = Menu(self.puntuacion.puntaje(), self.puntuacion.puntuacion_maxima())
        # Juego
        self.estado_juego = True
        self.clock = pygame.time.Clock()
        # Escenario 1
        self.escenarios.append(Valle(self.posicionX_escenarios, self.velocidad_escenarios, self.condor))

        # Servidor
        self.escenarios_sv = []                     # Cambio escenarios
        self.transicion_sv = False                  # Estado_transicion_sv
        self.jugadores_sv = {}                      # Diccionario {nombre_jugador : personaje}
        self.puntajes_sv = []           # Puntajes
        self.objetos_sv = []            # Nuevos objetos (obstaculos)
        self.juego_activo = False       # Bucle del juego
        # Data
        self.escenarios_sv.append(self.escenarios[0])

        # Cliente
        self.jugadores_cl = {}
        self.puntajes_cl = []
        self.estado_juego_colision = False
 
    # Reinicio de valores
    def reinicio_valores(self):
        # Escenarios
        self.posicionX_escenarios = 0
        self.escenarios = []
        self.escenarios_spawn = 0
        self.velocidad_escenarios = VELOCIDAD_ESCENARIOS
        # Transicion
        self.transicion = None              
        self.indice_escenario = 0          
        self.estado_transicion = False      
        self.situacion = False
        # Obstaculos
        posiciones_ocupadas.clear()
        # Puntuacion
        self.puntuacion.reinicio_puntaje()
        # Juego
        self.estado_juego = True
        self.escenarios.append(Valle(self.posicionX_escenarios, self.velocidad_escenarios, self.condor))
        self.estado_juego_colision = False

    def aparicion_transicion(self):
        if self.puntuacion.puntaje() >= 750:       
            self.transicion = Transicion(None, None, None, 2, 5, 0.05)         # Cambios
        elif self.puntuacion.puntaje() < 750:
            self.transicion = Transicion(None, None, None, 1, 10, 0.2)        # Cambios

        self.estado_transicion = True
        self.situacion = False      # Reestablecimiento

    def puntuacion_actual(self):
        return self.puntuacion.puntaje()
    
    def puntuacion_maxima(self):
        return self.puntuacion.puntuacion_maxima()

    # Juego
    def juego_cliente(self, estado_juego):
        """Bucle principal del juego en el cliente."""
        print("🔄 [DEBUG] Entrando en el bucle del juego...")  

        # COLOCAR DENTRO EL MENU DE FINAL, QUEDARA EN BUCLE CON EL PRIMERO
        self.reinicio_valores()

        if not estado_juego:
            print("⚠️ [ERROR] `estado_juego` es False. No se ejecutará el bucle.")
            return

        while estado_juego:
            #print("🎮 [DEBUG] Bucle del juego activo")  
            self.clock.tick(FPS)

            for event in pygame.event.get():
                #print(f"🟢 Evento detectado: {event.type}")  # 🔹 Verifica si Pygame detecta eventos

                if event.type == pygame.QUIT:
                    print("❌ Cierre detectado, saliendo...")
                    pygame.quit()
                    sys.exit()

            self.tecla = pygame.key.get_pressed()                           # Teclas presionadas
            self.mouse = pygame.mouse.get_pressed()[0]                      # Botón izquierdo

            # Generación de obstáculos dentro del escenario
            self.posicionX_escenarios += self.velocidad_escenarios
            self.escenarios_spawn += 1

            # Modificación en la generación de escenarios            
            for escenario in self.escenarios:
                if escenario.fin():
                    self.estado_transicion = True
                    self.aparicion_transicion()

            # Generacion de la transicion
            if self.estado_transicion:                  # Declarar al iniciar su aparicion
                self.transicion.ciclo()

                # Cambio de escenario unico
                if self.transicion.fin() and not self.situacion:
                    self.escenarios.pop(0)
                    self.situacion = True   # Evasion de otros cambios

                # Eliminacion al terminar la transicion
                if self.transicion.transicion_completada:
                    self.transicion = None
                    self.estado_transicion = False

            # Ciclos de las clases
            self.puntuacion.ciclo()                             # Puntuacion
            for escenario in self.escenarios:                   # Escenarios
                escenario.ciclo_basico()
                if escenario.valor_colision():                             # Deteccion de colision
                    estado_juego = False
                    self.reinicio_valores()                     # Reinicio
                    
            self.condor.ciclo(self.tecla, self.mouse)           # Condor

            # Renderizado de elementos: escenarios -> obstáculos -> condor -> puntuacion
            for escenario in self.escenarios:
                escenario.render_basico()
            self.condor.render()
            if self.estado_transicion:
                self.transicion.render()
            self.puntuacion.mostrar_puntaje()

            # Actualizar pantalla
            pygame.display.flip()

            ### Pruebas:
            print(f"{self.escenarios}") 
            if self.escenarios:
                print(f"{self.escenarios[-1].obstaculos}") 

    # Metodos de paquetes de datos
    def empaquetado_datos(self):
        """Serializes the game state for network transmission."""
        juego_data = {
            "escenarios": [esc.update() for esc in self.escenarios_sv] if self.escenarios_sv else [],
            "objetos": [obj.update() for obj in self.objetos_sv] if self.objetos_sv else [],
            "personajes": {nombre: personaje.update() for nombre, personaje in self.jugadores_sv.items()} if self.jugadores_sv else {}
        }
        
        # 🔍 Verificar si los datos son correctos antes de enviarlos
        print(f"📦 [DEBUG] Datos empaquetados correctamente: {juego_data}")

        self.objetos_sv.clear()
        self.escenarios_sv.clear()
        return juego_data

    @staticmethod
    def desempaquetado_datos(data):
        """Deserializa los datos del servidor."""
        try:
            datos = pickle.loads(data)
            print(f"📥 [DEBUG] Datos desempaquetados correctamente: {datos}")
            return datos
        except pickle.UnpicklingError as e:
            print(f"❌ [ERROR] No se pudieron desempaquetar datos de juego: {e}")
            return None

    def lectura_datos(self, datos_juego):
        try:
            print("📥 [DEBUG] Datos recibidos:", datos_juego)  # 🔹 Verificar estructura

            # 🔹 Agregar escenarios correctamente
            for datos_obj in datos_juego.get("escenarios", []):
                escenario = self.crear_escenario(datos_obj)
                if escenario:
                    self.escenarios.append(escenario)

            # 🔹 Agregar obstáculos correctamente
            if self.escenarios:  # Asegurar que hay escenarios
                for datos_obj in datos_juego.get("objetos", []):
                    obstaculo = self.crear_obstaculo(datos_obj)
                    if obstaculo:
                        self.escenarios[-1].obstaculos.append(obstaculo)  # Agregar a último escenario
            
            # 🔹 Cargar jugadores
            self.jugadores_cl = datos_juego.get("personajes", {})

        except Exception as e:
            print(f"❌ [ERROR] en lectura_datos: {e}")

    def crear_obstaculo(self, data):
        if not isinstance(data, dict):
            print(f"❌ [ERROR] Se esperaba un diccionario en `crear_obstaculo`, pero se recibió: {type(data)}")
            return None  # 🔥 Evita errores si el tipo es incorrecto

        tipo_objeto = data.get("tipo_obstaculo")

        if tipo_objeto == "Paloma":
            return Paloma.rt_update(data)
        elif tipo_objeto == "CFC":
            return CFC.rt_update(data)
        elif tipo_objeto == "Tuberias":
            return Tuberias.rt_update(data)
        else:
            print(f"⚠️ [DEBUG] Tipo de obstáculo desconocido: {tipo_objeto}")
            return None  # 🔥 Evita errores con tipos desconocidos


    def crear_escenario(self, data):
        if not isinstance(data, dict):
            print(f"❌ [ERROR] Se esperaba un diccionario en `crear_escenario`, pero se recibió: {type(data)}")
            return None

        tipo_objeto = data.get("tipo_escenario")

        if tipo_objeto == "Valle":
            return Valle.rt_update(data)
        elif tipo_objeto == "Ciudad":
            return Ciudad.rt_update(data)
        elif tipo_objeto == "Industria":
            return Industria.rt_update(data)
        elif tipo_objeto == "Mina":
            return Mina.rt_update(data)
        else:
            print(f"⚠️ [DEBUG] Tipo de escenario desconocido: {tipo_objeto}")
            return None

    
    def posicion_personaje(self, nombre_jugador, x, y):
        """Updates a character's position based on client input."""
        if nombre_jugador in self.jugadores_sv:
            self.jugadores_sv[nombre_jugador].x = x
            self.jugadores_sv[nombre_jugador].y = y        

    def nuevo_objeto(self, objeto):
        """Adds a new object to be sent in the next update."""
        self.objetos_sv.append(objeto)        





    




# Ejecucion del juego
class Run:
    def __init__(self):
        # Datos
        self.estado = True
        # Clases
        self.juego = Juego()
        self.menu = Menu(self.juego.puntuacion_actual(), self.juego.puntuacion_maxima())

    def ciclo(self):
        while self.estado:
            # Datos
            self.menu.estado_1 = True
            # Menu principal - juego "monojugador"
            self.menu.menu_principal()
            self.juego.juego(self.menu.estado_1)    # Un jugador

# Inicializar objetos
run = Run()

if __name__ == "__main__":
    run.ciclo()




### Errores pendientes
# Actualizacion de nombre del servidor