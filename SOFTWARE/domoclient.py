#!/usr/bin/python
# -*- coding: utf-8 -*-
####################################################################
#
#   Este script permite enviar comandos al servidor de domótica.
#   Los comandos válidos son:
#       status         ["","json"] : Entrega el estado de los dispositivos conectados. Si se especifica "json", el estado es entregado en este formato. En caso contrario, se dibuja el panel con caracteres.
#       absent_mode    ["on | enabled | 1", "off | disabled | 0"] : Habilita o deshabilita el modo "Nadie en casa". En este modo, el sistema simula movimiento normal en el hogar. 
#

#############################################################
# Parte encargada de dibujar el recuadro
#############################################################
# Constantes
PANEL_WIDTH = 43
TOP_MARGIN = 2
BOTTOM_MARGIN = 1
NAME_PADDING = 2
NAME_WIDTH = 24
ENTRY_MARGIN = 1
LED_MIDDLE_MARGIN = 3
LED_WIDTH = 3
VERSION_TOP_MARGIN = 1
NAME = "Panel Domótica"
VERSION = "1.1"
TIMEOUT = 10

# Colores:
NEGRO='\033[0;30m'
AZUL='\033[0;34m'
VERDE='\033[0;32m'
CYAN='\033[0;36m'
ROJO='\033[0;31m'
MORADO='\033[0;35m'
CAFE='\033[0;33m'
GRIS_CLARO='\033[0;37m'
GRIS_OSCURO='\033[1;30m'
AZUL_CLARO='\033[1;34m'
VERDE_CLARO='\033[1;32m'
CYAN_CLARO='\033[1;36m'
ROJO_CLARO='\033[1;31m'
MORADO_CLARO='\033[1;35m'
AMARILLO='\033[1;33m'
BLANCO='\033[1;37m'
NO_COLOR='\033[0m'

# Variables para conexión con el servidor
HOSTS = ["","192.168.0.3","mexomagno.duckdns.org"] # Localhost, raspi local, raspi remota
PORT = 8004 # Definido por mi

def repeatChar(c,ntimes):
    return c*ntimes
def drawTop():
    # Borde arriba
    print " {} ".format(repeatChar('_',PANEL_WIDTH-2))
    # margen
    for i in range(TOP_MARGIN):
        print ("|{}|".format(repeatChar(' ',PANEL_WIDTH-2)))
    # on off
    print ("|{}{}{}{}{}|".format(repeatChar(' ',(2*NAME_PADDING+NAME_WIDTH)),"OFF",repeatChar(" ",(LED_MIDDLE_MARGIN)),"ON",repeatChar(' ',(PANEL_WIDTH-2-5-LED_MIDDLE_MARGIN-2*NAME_PADDING-NAME_WIDTH))))
def drawEntry(entry):
    name=entry['name']
    gpio=entry['gpio']
    value=entry['value'] if entry['value']!='' else "0"
    # Nombre
    text = "|{}{}{}".format(repeatChar(' ',NAME_PADDING),name,repeatChar(' ',(NAME_WIDTH-len(name)+NAME_PADDING)))
    # Led OFF y ON
    text += "{}{}{}{}".format(ROJO_CLARO,repeatChar(('#'if value=="0" else ' '),LED_WIDTH),NO_COLOR,repeatChar(' ',LED_MIDDLE_MARGIN))
    text += "{}{}{}{}|".format(VERDE_CLARO,repeatChar((' ' if value=="0" else '#'), LED_WIDTH),NO_COLOR,repeatChar(' ',(PANEL_WIDTH-2-2*LED_WIDTH-2*NAME_PADDING-NAME_WIDTH-LED_MIDDLE_MARGIN)))
    print (text)
    # GPIO
    print "|{}GPIO_{}{}|".format(repeatChar(' ',NAME_PADDING),gpio,repeatChar(' ',PANEL_WIDTH-2-(1 if int(gpio)<10 else 2)-5-NAME_PADDING))
    # Margen abajo
    for i in range(ENTRY_MARGIN):
        print "|{}|".format(repeatChar(' ',PANEL_WIDTH-2))
def drawBottom():
    # Margen
    for i in range(VERSION_TOP_MARGIN):
        print ("|{}|".format(repeatChar(' ',PANEL_WIDTH-2)))
    # Nombre
    namelength = len(NAME.decode("utf-8"));
    relleno = PANEL_WIDTH-2-namelength
    print ("|{}{}{}|".format(repeatChar(' ',((int)(relleno/2) if relleno%2==0 else (int)(relleno/2)+1)),NAME,repeatChar(' ',(int)(relleno/2))))
    # Versión
    versionlength = 8+len(VERSION.decode("utf-8"))
    relleno = PANEL_WIDTH-2-versionlength;
    print ("|{}Versión {}{}|".format( repeatChar(' ',( (int)(relleno/2) if relleno%2==0 else (int)(relleno/2)+1)), VERSION,repeatChar(' ',(int)(relleno/2))))
    # Final
    for i in range(BOTTOM_MARGIN+1):
        print ("|{}|".format(repeatChar(('_' if i==BOTTOM_MARGIN else ' '),(PANEL_WIDTH-2))))
def drawPanel(data):
    drawTop()
    for entry in data:
        drawEntry(entry)
    drawBottom()

###################################################################
# Parte encargada de validar argumentos
###################################################################

def showHelp(mensaje):
    help_msg = """
    Este script permite enviar comandos al servidor de domótica.
    Los comandos válidos son:
        status         ["","json"] : 
                Entrega el estado de los dispositivos conectados. Si se especifica "json", el estado es entregado en este formato. En caso contrario, se dibuja el panel con caracteres.
        
        absent_mode    ["on | enabled | 1", "off | disabled | 0"] :
                Habilita o deshabilita el modo "Nadie en casa". En este modo, el sistema simula movimiento normal en el hogar. 
        
        -h, --help :
                Muestra esta ayuda
    """
    if mensaje != "":
        print "Error: {}".format(mensaje)
    print help_msg
    exit()
# Definición de argumentos válidos
valid_args={    'absent_mode'   : ['on','off','enabled','disabled','1','0'],
                'status'        : ["",'json'],
                'help'          : ["-h", "--help", "-?"]}
def panic(mensaje, parser):
    print ROJO_CLARO + mensaje + NO_COLOR
    parser.print_help()
    exit(1)

def parseArguments():
    # import sys
    # # Obtener argumentos y validarlos
    # args=sys.argv
    # nargs=len(args) - 1
    # if nargs == 0:
    #     # comportamiento default
    #     command = "status"
    # else:
    #     command = args[1]
    # # Ver que el argumento es válido
    # if command not in valid_args:
    #     showHelp("Argumento inválido: '{}'".format(command))
    # # Obtener propiedad para el argumento
    # if nargs == 1:
    #     if "" not in valid_args[command]:
    #         showHelp("Falta parámetro para '{}'".format(command))
    # if nargs == 2:
    #     if args[2] not in valid_args[command]:
    #         showHelp("Parámetro desconocido para '{}'".format(command))
    #     command = command + " " + args[2]
    # if nargs >2:
    #     showHelp("Demasiados argumentos")
    # return command

    import argparse as AP
    parser = AP.ArgumentParser(description="Comunicación con servidor de domótica", epilog="Versión 1.1")
    on_off_choices = ["on", "off", "enabled", "disabled", "1", "0", "true", "false"]
    gpio_choices = ["2","3","4","17","18","15","14"]
    
    parser.add_argument("-s", "--status", nargs="?", const="graphic", choices=["graphic", "json"], help="Obtener estado de los dispositivos. Este es el comportamiento default del programa, si se lo llama sin argumentos. Si se desea output en formato json, se debe además incluir STAT='json'.")
    # Opciones configuración de un dispositivo
    parser.add_argument("-d", "--disp", nargs=1, choices=gpio_choices, help="Elige un dispositivo a configurar")
    parser.add_argument("-sv", "--set-value", nargs=1, choices=on_off_choices, help="Setea inmediatamente un estado para el dispositivo en cierto GPIO. Valor NO afectado por OVERRIDE.")
    parser.add_argument("-on", "--on-time", nargs=2, type=int, metavar=("HH", "MM"), help="Setea hora de encendido del dispositivo.")
    parser.add_argument("-off", "--off-time", nargs=2, type=int, metavar=("HH", "MM"), help="Setea hora de apagado del dispositivo.")
    # Opciones globales para el servicio
    parser.add_argument("-am", "--absent-mode", nargs=1, choices=on_off_choices, help="Activar|desactivar modo ausente. Utilizado cuando no hay nadie presente en la casa.")
    parser.add_argument("--override-status", nargs=1, choices=on_off_choices, help="Setea funcionalidad OVERRIDE. Si está activada, el servidor sobreescribirá output del pin si su estado ha sido cambiado por otro proceso. En caso contrario, se mantiene última modificación al output.")
    # Opciones de conexión con el servidor
    parser.add_argument("-H", "--host", nargs="+", help="Lista de hosts a los que intentar conectarse. Por defecto, se usa '{}'".format(HOSTS))
    parser.add_argument("-P", "--port", nargs=1, type=int, help="Puerto del host. Por defecto, se usa el '{}'".format(PORT))
    args = parser.parse_args()

    # PARSEAR ARGUMENTOS
    argsdict = vars(args)
    # Si todos son None, se asume status=graphic
    allnone = True
    for arg in argsdict:
        if argsdict[arg] != None:
            allnone = False
            break
    if allnone:
        return "status"
    # opciones para dispositivo NO pueden especificarse sin especificar qué dispositivo se quiere configurar
    if argsdict["disp"] == None:
        if argsdict["set_value"] != None or argsdict["on_time"] != None or argsdict["off_time"] != None:
            panic("Error: Debe especificar un dispositivo al cual asignar esta opción!", parser)
    # Horas ingresadas deben ser válidas
    if argsdict["on_time"] != None and (argsdict["on_time"][0] not in range(24) or argsdict["on_time"][1] not in range(60)):
        panic("Error: La hora de encendido '{}:{}' no es válida".format(argsdict["on_time"][0], argsdict["on_time"][1]), parser)
    if argsdict["off_time"] != None and (argsdict["off_time"][0] not in range(24) or argsdict["off_time"][1] not in range(60)):
        panic("Error: La hora de apagado '{}:{}' no es válida".format(argsdict["off_time"][0], argsdict["off_time"][1]), parser)
    print argsdict
    # Puerto debe ser válido
    if argsdict["port"] != None and argsdict["port"][0] < 1024:
        panic("Error: El nro de puerto debe ser mayor a 1024", parser)
    
    return argsdict  
##############################################################
# Conexión y funcionamiento general
##############################################################
def serve(command, reply):
    c_a = command.split()
    if c_a[0] == "absent_mode":
        if reply == "OK":
            print "Modo Ausente {}".format("Habilitado" if (c_a[1] == "on" or c_a[1] == "enabled" or c_a[1] == "1") else "Deshabilitado")
        else:
            print "Error: '{}'".format(reply)
    elif c_a[0] == "status":
        if len(c_a) == 1:
            from yaml import load
            drawPanel(load(reply))
        else:
            print reply

def connect():
    import socket
    for host in HOSTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: 
            s.settimeout(TIMEOUT)
            s.connect((host,PORT))
            s.settimeout(None)
            return s
        except socket.error, msg:
            s.settimeout(None)
            s.close()
            pass
    print "Fue imposible conectarse. Abortando."
    exit()

###########################################################################
# MAIN
###########################################################################
def main():
    command = parseArguments()
    #import socket
    #import yaml
    from subprocess import call
    s = connect()
    s.send(command)
    reply = s.recv(1024)
    serve(command, reply)
    s.close()

main()

#######################
"""
PENDIENTE:
- [DONE] independizarse del archivo en C
- Posibilidad de mostrar horas de inicio y término, y threshold random seteado
- [DONE]Mejorar parseo de opciones y usar mejores estándares
- [NOT]Añadir autocompletado a opciones
- Posibilidad de especificar host y puerto

"""

"""
De qué distintas formas se puede definir horarios de encendido y apagado para un dispositivo?

    - Una forma es definir un horario y repetirlo todos los días
        - Una extensión es permitir varios horarios para un día y repetirlos
    - Otra forma, especificar repeticiones como crontab, es decir "m h dom mon dow"

Cuál debiera ser el resultado para tener correctamente especificado un horario?
    - Debiera tener al menos una hora específica de inicio y término. Puede tener varias
    

"""