#!/usr/bin/python
# -*- coding: utf-8 -*-
import getpass # para obtener usuario actual

def alreadyRunning():
    from subprocess import Popen, PIPE
    ps = Popen("ps -e".split(),stdout=PIPE)
    #tr = Popen(['tr','" "','_'],stdin=ps.stdout,stdout=PIPE)
    grep = Popen(['grep','domotica.py'],stdin=ps.stdout,stdout=PIPE)
    output = grep.communicate()[0]
    if output.count("domotica.py")>1:
        return output.split()[0]
    return 0

# chequear que se ejecuta como root
if (getpass.getuser() != "root"):
    # logWrite("{}Usuario no es root{}".format(rojo_claro,no_color))
    print "Debe ejecutar como root. Saliendo..."
    exit(1)
    #panic("Debe ejecutar como root. Saliendo...")
pid = alreadyRunning()
#if pid:
#    print "Ya existe una instancia de este programa ejecutándose (pid={}).".format(pid)
#    exit(1)
    

## Para evitar stdout de ciertas funciones
#import contextlib
#import sys
#import cStringIO
import RPi.GPIO as io
import signal
from datetime import datetime, timedelta
import time # para control de tiempos
from random import randint
import threading,json,socket
# Para guardar logs
from include.python.logs import *
# Iniciar archivo de logs
logInit()
# constantes
SLEEP_TIME =  10 # segundos
TIME_FORMAT = "%H:%M"
DEFAULT_PORT = 8004
PORT = DEFAULT_PORT
KEY="VVT??/()(/*Q]A]SD[FMAi2!"

# variables globales
OVERRIDE_ALWAYS = True
ABSENT_MODE = False # Para implementación del modo ausente
run = False

########### MENSAJES CONSOLA ##
VERBOSE = True # Mensajes de error
DEBUG = False # Mensajes de debug
def log (mensaje, debug = False, file = False):
    """
        Si file = True, escribe el log en el archivo de logs de este programa
    """
    if (debug):
        if (DEBUG): print "DEBUG: "+mensaje
    else:
        if (VERBOSE): print mensaje

def panic(mensaje):
    log(mensaje)
    endProgram(1)

########### FUNCIONES VARIAS ##
def inInterval(time, ontime, offtime):
    """
        {   datetime.time(),
            datetime.time(),
            datetime.time() }
        ---->
            boolean

        Retorna:    True si time está entre ontime y offtime
                    False en caso contrario
    """
    if (ontime == offtime): return False
    if ((ontime <= time <= offtime) or (offtime <= ontime <= time) or (time <= offtime <= ontime)):
        return True
    else: return False 
#    caso 1: 00:00 < ontime < time < offtime < 23:59
#    caso 2: 00:00 < offtime < ontime < time < 23:59
#    caso 3: 00:00 < time < offtime < ontime < 23:59
# hora1=datetime.strptime("8:00",TIME_FORMAT)
# hora2=datetime.strptime("22:00",TIME_FORMAT)
# hora= datetime.strptime("13:00",TIME_FORMAT)
# print "13 entre 8 y 22 ?: {}".format(inInterval(hora,hora1,hora2))
# print "13 entre 22 y 8 ?: {}".format(inInterval(hora,hora2,hora1))
# print "8 entre 22 y 13 ?: {}".format(inInterval(hora1,hora2,hora))
# print "8 entre 13 y 22 ?: {}".format(inInterval(hora1,hora,hora2))
# print "22 entre 13 y 8 ?: {}".format(inInterval(hora2,hora,hora1))
# print "22 entre 8 y 13 ?: {}".format(inInterval(hora2,hora1,hora))

class Device():
    """ Variables internas:
    self.value          : int, 0 o 1 | Indica si está on o off
    self.name           : string | Nombre seteado por el usuario.
    self.gpio           : int en valid_gpio | Indica el pin gpio asociado.
    self.ontime         : datetime.datetime | Indica hora de encendido.
    self.offtime        : datetime.datetime | Hora de apagado.
    self.ontime_real    : datetime.datetime | respaldo de ontime, para implementar randomización.
    self.offtime_real   : datetime.datetime | respaldo de offtime, para implementar randomización.
    self.r_threshold    : int | Umbral que fija rango de randomización del encendido y apagado.

        Variables globales de la clase:
    Device.DEFAULT_VALUE       : int, 0 o 1 | Valor con el que inicializan los gpio output.
    Device.valid_gpio   : [int] | lista de gpios habilitados para domótica.
    Device.used_gpio    : [int] | lista de los gpios inicializados y en uso por el programa.
    Device.init_all     : boolean | Indica si se ejecutó por lo menos una vez la función initAll()
    """

    """ Métodos:
    --- CONSTRUCTORES Y DESTRUCTORES ---
    initAll()           : void -> void | Inicializa los pines disponibles para el programa.
    __init__()          : string,int,string TIME_FORMAT, string TIME_FORMAT -> Device | Constructor
    kill()              : void -> void | Libera el gpio
    --- SETTERS ---
    setValue()          : int -> void | Setea valor de output.
    setOnTime()         : string TIME_FORMAT -> void | setea el ontime
    setOffTime()        : string TIME_FORMAT -> void | setea el offtime
    --- GETTERS ---
    getValue()          : void -> int | Retorna el valor actual del gpio
    getGpio()           : void -> int | Retorna gpio asociado al dispositivo
    getName()           : void -> string | retorna nombre asignado

    @classmethod
    getValidGPIO()      : void -> int [] | Retorna listado de GPIO's habilitados en el sistema.
    getUsedGPIO()      : void -> int [] | Retorna listado de GPIO's con dispositivos asociados.
    --- OTROS ---
    update()            : void -> void | Actualiza el estado (valor) de un dispositivo según la hora.
    randomize()         : int -> void | añade el factor de aleatoreidad al cambio de estado del dispositivo.
    """
    DEFAULT_VALUE=0
    valid_gpio=[2,3,4,17,18,15,14] # en orden panel domotica: 2, 3, 4, 17, 18, 15, 14
    used_gpio=[]
    THRESHOLD_LIMIT = 120 # 2 horas
    init_all = False
    @classmethod
    def initAll(cls):
        """
            HAY que llamar a esta función antes de usar esta clase
        """
        if (Device.init_all):
            return
        logWrite("Iniciando outputs en 0...")
        for gpio in Device.valid_gpio:
            io.setmode(io.BCM)
            io.setup(gpio,io.OUT,0)
        Device.init_all = True


    def __init__(self,name,gpio,ontime="00:00",offtime="00:00",r_threshold=0):
        """
            Recibe un nombre y un gpio
            Retorna:    0 si todo ok
                        bota el programa en caso de error
            Escribe errores dependiendo del nivel de verbosidad
        """
        ## Validando que se ejecutó initAll
        if (not Device.init_all):
            #log("NO SE HA EJECUTADO INIT_ALL. Ejecutando...")
            #logWrite("NO SE HA EJECUTADO initAll()!!. Ejecutando...")
            Device.initAll()
        ## HAY QUE VALIDAR LAS HORAS
        self.setOnTime(ontime)
        self.setOffTime(offtime)
        self.ontime_real = self.ontime
        self.offtime_real = self.offtime
        #HAY QUE VALIDAR TODO
        self.name=name.strip().title()
        if (gpio in Device.valid_gpio):
            if (not (gpio in Device.used_gpio)):
                self.gpio=gpio
                Device.used_gpio.append(gpio)
            else:
                panic("GPIO={} ya está en uso".format(gpio))
        else:
            panic("GPIO={} No válido".format(gpio))
        ## HAY QUE ELIMINAR EL STDOUT
        io.setup(self.gpio,io.OUT)
        self.r_threshold = r_threshold
        logWrite("Nuevo dispositivo: {}'{}'{} en GPIO {}. Enciende: {}{}{} Apaga: {}{}{}".format(amarillo,self.name,no_color,self.gpio,azul_claro,self.ontime_real.time(),no_color,azul_claro,self.offtime_real.time(),no_color))
        self.setValue(Device.DEFAULT_VALUE)
    
    def kill(self):
        # Liberar el pin gpio
        self.setValue(0)
        log("Liberando el pin {}".format(self.gpio))
        Device.used_gpio.remove(self.gpio)
    
    ## SETTERS
    def setValue(self,value):
        """
            Recibe 0 o 1 (int)
            Asigna el valor y lo escribe en el pin gpio
        """
        self.value = 0 if (value == 0) else 1
        io.output(self.gpio,self.value)
        # Prepararse para el próximo cambio de estado
        self.randomize(self.r_threshold)
    def setName(self, newname):
        if newname != "":
            self.name = newname
    def setOnTime(self,ontime):
        """
            Recibe string con horas del tipo "hh:mm"
            Las guarda en datetime.time()
            Retorna:    0 si todo está ok
                        1 en error
        """
        # Tomar string y convertirlo en objeto de hora, si es posible
        self.ontime = datetime.strptime(ontime,TIME_FORMAT) #.time()
    def setOffTime(self,offtime):
        """
            Recibe string con horas del tipo "hh:mm"
            Las guarda en datetime.time()
            Retorna:    0 si todo ok
                        1 en error
        """
        self.offtime = datetime.strptime(offtime,TIME_FORMAT) #.time()
    def setRandomizeThreshold(self, r_threshold):
        if r_threshold <= Device.THRESHOLD_LIMIT and r_threshold >= 0:
            self.r_threshold = r_threshold
    ## GETTERS
    def getValue(self):
        return self.value
    def getGpio(self):
        return self.gpio
    def getName(self):
        return self.name
    def getRandomizeThreshold(self):
        return self.r_threshold
    @classmethod
    def getValidGPIO(cls):
        return cls.valid_gpio
    @classmethod
    def getUsedGPIO(cls):
        return cls.used_gpio

    def update(self):
        # obtener hora actual
        current_time = datetime.now().time()
        lastval = self.value
        # Ver si valor actual concuerda con el estado del pin, en caso contrario, lo corrige
        if OVERRIDE_ALWAYS and self.value != io.input(self.gpio):
            print "Activando OVERRIDE (otro proceso cambió el estado del pin!)"
            io.output(self.gpio, self.value)
        # ver si se está dentro del intervalo
        if (inInterval(current_time,self.ontime.time(), self.offtime.time())):
            # Cambiar estado si hay que hacerlo
            if (self.value == 0):
                log("--- '{}' se enciende".format(self.name))
                self.setValue(1)
            else:
                log("--- '{}' no cambia".format(self.name), True)
        else:
            if (self.value == 1): 
                log("--- '{}' se apaga".format(self.name))
                self.setValue(0)
            else:
                log("--- '{}' no cambia".format(self.name), True)
        # Cambió de valor. Escribir en el log
        if (lastval != self.value):
            logWrite("--- Actualizando {}'{}'{}... nuevo valor: {}{}{}".format(amarillo,self.name,no_color,cyan_claro,("ON" if (self.value == 1) else "OFF"),no_color))

    
    def randomize(self,threshold):
        """
        Recibe: Int con valor en minutos del umbral alrededor del que se randomizará la hora de encendido y apagado.

        Si se ingresa X minutos, se encenderá y apagará el dispositivo a ontime+-X y offtime+-X respectivamente (minutos).
        """
        # mapear threshold entre 0 y THRESHOLD_LIMIT
        th = threshold if (threshold >= 0 and threshold <= Device.THRESHOLD_LIMIT) else (0 if (threshold < 0) else Device.THRESHOLD_LIMIT)
        if (self.r_threshold == 0 and th != 0):
            # Respaldar ontime y offtime originales
            log ("Randomizando con threshold {}".format(threshold),debug = True)
            self.ontime_real = self.ontime
            self.offtime_real = self.offtime
        if (th == 0 and self.r_threshold != 0):
            # Recuperar los valores reales anteriores
            log ("Eliminando randomización...",debug = True)
            self.ontime = self.ontime_real
            self.offtime = self.offtime_real
        self.r_threshold = th
        if (th > 0):
            # modificar ontime u offtime, dependiendo del que venga próximo
            sumaresta = 1 if (randint(0,1) == 1) else -1
            if (self.value == 0):
                self.ontime = self.ontime_real + (sumaresta*timedelta(minutes = (randint(0,th))))
                log ("Ontime: original: {} nuevo: {}".format(self.ontime_real.time(),self.ontime.time()),debug = True)
                logWrite("{}'{}'{}: randomizado +-{} minutos, {}ON{} antes: {}{}{}, ahora: {}{}{}".format( amarillo,self.name,no_color,self.r_threshold,cyan_claro,no_color,azul_claro,self.ontime_real.time(), no_color,azul_claro,self.ontime.time(), no_color));
            else:
                self.offtime = self.offtime_real + (sumaresta*timedelta(minutes = (randint(0,th))))
                log ("Offtime: original: {} nuevo: {}".format(self.offtime_real.time(),self.offtime.time()),debug = True)
                logWrite("{}'{}'{}: randomizado +-{} minutos. {}OFF{} antes: {}{}{}, ahora: {}{}{}".format(amarillo,self.name,no_color,self.r_threshold,cyan_claro,no_color,azul_claro,self.offtime_real.time(),no_color,azul_claro,self.offtime.time(),no_color));

# Handler de SIGINT
def terminate(signal,frame):
    endProgram(0)

def endProgram(rc):
    global run
    if ('run' in globals()):
        logWrite("Matando el servicio...")
        log("Dejando de ejecutar servicio...")
        run = False
    if ('disps' in globals()):
        log("Matando los dispositivos...")
        for disp in disps:
            logWrite("--- Liberando '{}'".format(disp.getName()))
            log("--- Matando dispositivo '{}'".format(disp.getName()))
            disp.kill()
    if (len(Device.used_gpio) != 0):
        log("Liberando GPIOs...")
        logWrite("Liberando GPIOs...")
        io.cleanup()
    if (rc == 0): log("Fin. Adiós!")
    else: log("Fin. Programa terminado con código {}".format(rc))
    # Finalizar escritura de logs
    logEnd(rc)
    exit(rc)

def serverThread():
    global run, PORT
    HOST = ''
    print "Comienza el servidor"
    print "Usando puerto {}".format(PORT)
    # Creación de socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST,PORT))
    except socket.error, msg:
        print "Error al tomar puerto: {}".format(msg[1])
        exit()
    print "Socket escuchando puerto {}".format(PORT)
    s.listen(1)
    logWrite("Servidor paralelo iniciado en {}:{}".format(HOST,PORT))
    # comandos válidos
    print "Esperando conexiones..."
    while run:
        # Esperar conexión
        (conn, addr) = s.accept()
        print 'Conectado con ' + addr[0] + ':' + str(addr[1])
        # Recibir llave autenticación
        data = conn.recv(1024)
        if data != KEY:
            print "WARNING: Se recibió llave inválida"
            conn.send("KO")
            conn.close()
            continue
        else:
            conn.send("OK")
        # Procesar datos
        data = conn.recv(2048)
        reply = atender(data)
        # Responder
        conn.send(reply)
        print "Cliente atendido. Respuesta: {}".format(reply)
        logWrite("Cliente atendido.\n Request: '{}'\n Response: '{}'".format(data,reply))
        conn.close()

def atender(data):
    global ABSENT_MODE, OVERRIDE_ALWAYS
    """
        Toma los datos enviados por el cliente, los analiza y hace operaciones correspondientes.
        Retorna lo que corresponda retornar.
        "data" es directamente lo recibido desde el cliente. Es un diccionario conteniendo los valores 
        (previamente validados por el cliente) de los argumentos ingresados.

        Puede recibir dos tipos de requests:
        - configuración y seteo de valores
            - respuesta posible OK o ERROR
        - Petición de status e información
            - Respuesta es la información pedida
    """
    from yaml import load
    d = load(data)
    # Status request
    if d["status"] != None:
        print "Request de status"
        disp_array = []
        valid_gpio = Device.getValidGPIO()
        for gpio in valid_gpio:
            device = seekDisp(gpio, "gpio")
            disp_array.append(device if device is not None else {"name": "<no device>", "gpio": "{}".format(gpio), "value": ""})
        return json.dumps(disp_array)
    # Configuración de un dispositivo
    if d["disp"] != None:
        print "Se pide configurar dispositivo en GPIO {}".format(d["disp"][0])
        # Crear un dispositivo
        if d["add"]:
            if d["remove"]:
                return "No se puede añadir y eliminar al mismo tiempo"
            # Verificar que no exista ya
            disp = seekDisp(d["disp"][0], "gpio")
            if disp is not None:
                return "GPIO {} ya usado".format(d["disp"][0])
            # Verificar que se entregaron todos los datos para la creación
            if (d["set_name"] is None or
                d["on_time"] is None or
                d["off_time"] is None):
                return "Faltan datos para agregar dispositivo"
            # Crear dispositivo y agregar
            disps.append(Device(d["set_name"][0], d["disp"][0], "{}:{}".format(d["on_time"][0], d["on_time"][1]), "{}:{}".format(d["off_time"][0], d["off_time"][1]),r_threshold=d["set_randomize"]))
            print "Agregado dispositivo '{}' en GPIO {}".format(d["set_name"][0], d["disp"][0])
            return "OK"
        # Modificar un dispositivo
        # ver si existe
        disp = seekDispObject(d["disp"][0], "gpio")
        if disp is None:
            return "No existe el dispositivo"
        if d["remove"]:
            # Eliminar un dispositivo
            if d["add"]:
                return "No se puede añadir y eliminar al mismo tiempo"
            for device in disps:
                print "FOR"
                if device.getGpio() == d["disp"][0]:
                    print "Eliminado dispositivo '{}' en GPIO {}".format(device.getName(), device.getGpio())
                    device.setValue(0)
                    disps.remove(device)
                    return "OK"
        # Modificar configuraciones de cada dispositivo
        if d["set_name"] is not None:
            print "Cambiando nombre de dispositivo {} a '{}'".format(d["disp"][0], d["set_name"][0])
            disp.setName(d["set_name"][0])
        if d["on_time"] is not None:
            print "Cambiando hora encendido de dispositivo {} a '{}:{}'".format(d["disp"][0], d["on_time"][0], d["on_time"][1])
            disp.setOnTime( "{}:{}".format(d["on_time"][0], d["on_time"][1]))
        if d["off_time"] is not None:
            print "Cambiando hora apagado de dispositivo {} a '{}:{}'".format(d["disp"][0], d["off_time"][0], d["off_time"][1])
            disp.setOffTime( "{}:{}".format(d["off_time"][0], d["off_time"][1]))
        if d["set_randomize"] is not None and d["set_randomize"] != disp.getRandomizeThreshold():
            print "Cambiando random threshold de dispositivo {} a +-{} mins".format(d["disp"][0], d["set_randomize"])
            disp.setRandomizeThreshold(d["set_randomize"])
        if d["set_value"] is not None:
            print "{} dispositivo {}".format("Encendiendo" if d["set_value"] else "Apagando" ,d["disp"][0])
            disp.setValue(1 if d["set_value"] else 0)
    # Configuración de absent mode
    if d["absent_mode"] is not None:
        if ABSENT_MODE == d["absent_mode"]:
            print "Modo ausente ya estaba {}".format("activado" if ABSENT_MODE else "desactivado")
        else:
            ABSENT_MODE = d["absent_mode"]
            print "{} modo ausente...".format("Activando" if ABSENT_MODE else "Desactivando")
    # Configuración de override status
    if d["override_status"] is not None:
        if OVERRIDE_ALWAYS == d["override_status"]:
            print "Modo OVERRIDE ya estaba {}".format("activado" if OVERRIDE_ALWAYS else "desactivado")
        else:
            OVERRIDE_ALWAYS = d["override_status"]
            print "{} modo OVERRIDE...".format("Activando" if OVERRIDE_ALWAYS else "Desactivando")
    return "OK"
def seekDisp(key, criterion="name"):
    global disps
    """
    Recibe llave de búsqueda, busca según el criterio ("name","gpio") y retorna diccionario con info del dispositivo ([name, gpio, value])
    Diccionario está formado por sólo strings.
    Si no encuentra nada, retorna 'None'
    """
    for disp in disps:
        if criterion=="name":
            if disp.getName() == key:
                return {"name": key, "gpio": "{}".format(disp.getGpio()), "value":"{}".format(disp.getValue())}
        if criterion == "gpio":
            if disp.getGpio() == int(key):
                return {"name": disp.getName(), "gpio": "{}".format(disp.getGpio()), "value": "{}".format(disp.getValue())}
    return None#{"name": None, "gpio": (key if criterion == "gpio" and int(key) in Device.getValidGPIO() else ""), "value": ""}
def seekDispObject(key, criterion="name"):
    global disps
    """
    Retorna objeto buscado, no diccionario con info
    """
    for disp in disps:
        if criterion=="name":
            if disp.getName() == key:
                return disp
        if criterion == "gpio":
            if disp.getGpio() == int(key):
                return disp
    return None
############ MAIN ##
def main():
    global run,disps,PORT
    # Parsear argumentos
    import argparse
    parser = argparse.ArgumentParser(description="Servidor de domótica", epilog = "Versión 1.1")
    parser.add_argument("-p", "--port", nargs=1, type=int, help="Puerto por el cual escuchar peticiones de clientes. Por defecto: {}".format(DEFAULT_PORT))
    args = parser.parse_args()
    if vars(args)["port"] != None:
        if vars(args)["port"][0] < 1024:
            panic("El puerto debe ser mayor o igual a 1024")
        PORT = vars(args)["port"][0]
    # Activar/Desactivar warnings de Rpi.GPIO
    io.setwarnings(DEBUG)
    # Inicializar dispositivos
    logWrite("Inicializando dispositivos...")
    log("Inicializando dispositivos...")
    disps = []
    # agregar dispositivos
    # disps.append(Device("luz entrada",2,"20:20","07:20", r_threshold = 10))    
    # disps.append(Device("luz delantera",3,"20:40","07:30", r_threshold = 20))
    # disps.append(Device("Riego alrededor", 17, "22:00", "22:30", r_threshold = 0))
    # Inicializar handler señal SIGINT
    log("Inicializando handler de SIGINT...", True)
    signal.signal(signal.SIGINT, terminate)
    # Crear server thread
    logWrite("Inicializando servidor paralelo...")
    sdaemon = threading.Thread(target = serverThread)
    sdaemon.setDaemon(True)
    sdaemon.start()
    run = True
    while run:
        # Recorrer todos los dispositivos
        log("Revisando los dispositivos...")
        for disp in disps:
            # Actualizar
            log("--- Actualizando {}'{}'{}".format(amarillo,disp.getName(),no_color), True)
            disp.update()
        # dormir un tiempo apropiado
        log("A dormir {} s".format(SLEEP_TIME), True)
        time.sleep(SLEEP_TIME)
main()


"""
PENDIENTE
- Implementación de repeticiones (tipo calendario o crontab)
- Revisar colisiones de horario en hora randomizada
- Implementar modo ausente
- Implementar configurabilidad del modo ausente
"""
