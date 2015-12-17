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
        
        help :
                Muestra esta ayuda
    """
    if mensaje != "":
        print "Error: {}".format(mensaje)
    print help_msg
    exit()
# Definición de argumentos válidos
valid_args={    'absent_mode'   : ['on','off','enabled','disabled','1','0'],
                'status'        : ["",'json']}
def validarArgumentos():
    import sys
    # Obtener argumentos y validarlos
    args=sys.argv
    nargs=len(args) - 1
    if nargs == 0:
        # comportamiento default
        command = "status"
    else:
        command = args[1]
    # Ver que el argumento es válido
    if command not in valid_args:
        showHelp("Argumento inválido: '{}'".format(command))
    # Obtener propiedad para el argumento
    if nargs == 1:
        if "" not in valid_args[command]:
            showHelp("Falta parámetro para '{}'".format(command))
    if nargs == 2:
        if args[2] not in valid_args[command]:
            showHelp("Parámetro desconocido para '{}'".format(command))
        command = command + " " + args[2]
    if nargs >2:
        showHelp("Demasiados argumentos")
    return command

##############################################################
# Conexión y funcionamiento general
##############################################################
def atender(command, reply):
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

def conectar():
    import socket
    hosts = ["","192.168.0.3","mexomagno.duckdns.org"] # Localhost, raspi local, raspi remota
    port = 8004 # Definido por mi
    for host in hosts:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: 
            s.settimeout(TIMEOUT)
            s.connect((host,port))
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
    command = validarArgumentos()
    #import socket
    #import yaml
    from subprocess import call
    s = conectar()
    s.send(command)
    reply = s.recv(1024)
    atender(command, reply)
    s.close()

main()

#######################
"""
PENDIENTE:
- [DONE] independizarse del archivo en C
- Posibilidad de mostrar horas de inicio y término, y threshold random seteado
- Mejorar parseo de opciones y usar mejores estándares
- Añadir autocompletado a opciones
- Posibilidad de especificar host y puerto

"""