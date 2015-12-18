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
VERSION = "2.0"
TIMEOUT = 10
DEFAULT_PORT = 8004

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
KEY="VVT??/()(/*Q]A]SD[FMAi2!"

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
# valid_args={    'absent_mode'   : ['on','off','enabled','disabled','1','0'],
#                 'status'        : ["",'json'],
#                 'help'          : ["-h", "--help", "-?"]}
def panic(mensaje, parser):
    print ROJO_CLARO + mensaje + NO_COLOR
    parser.print_help()
    exit(1)

def parseArguments():
    import argparse as AP
    import sys
    parser = AP.ArgumentParser(description="Comunicación con servidor de domótica", epilog="Versión {}".format(VERSION))
    on_off_choices = ["on", "off", "enabled", "disabled", "1", "0", "true", "false"]
    gpio_choices = [2,3,4,17,18,15,14]
    
    parser.add_argument("-s", "--status", nargs="?", const="graphic", choices=["graphic", "json"], help="Obtener estado de los dispositivos. Este es el comportamiento default del programa, si se lo llama sin argumentos. Si se desea output en formato json, se debe además incluir STAT='json'.")
    # Opciones configuración de un dispositivo
    parser.add_argument("-d", "--disp",         nargs=1, type=int, choices=gpio_choices, help="Elige un dispositivo a configurar")
    parser.add_argument("-a","--add",           action="store_true",           help="Agrega (o lo intenta) nuevo dispositivo")
    parser.add_argument("-r","--remove",        action="store_true",           help="Elimina (o lo intenta) dispositivo existente")
    parser.add_argument("-sn", "--set-name",    nargs=1, metavar="NAME", help="Setea un nuevo nombre para el dispositivo")
    parser.add_argument("-sv", "--set-value",   nargs=1, choices=on_off_choices, help="Setea inmediatamente un estado para el dispositivo en cierto GPIO. Valor NO afectado por OVERRIDE.")
    parser.add_argument("-sr", "--set-randomize", nargs=1, metavar="THRES", default=0, type=int, help="Define rango en minutos de aleatorización de hora de inicio y término.")
    parser.add_argument("-on", "--on-time",     nargs=2, type=int, metavar=("HH", "MM"), help="Setea hora de encendido del dispositivo.")
    parser.add_argument("-off", "--off-time",   nargs=2, type=int, metavar=("HH", "MM"), help="Setea hora de apagado del dispositivo.")
    # Opciones globales para el servicio
    parser.add_argument("-am", "--absent-mode", nargs=1, choices=on_off_choices, help="Activar|desactivar modo ausente. Utilizado cuando no hay nadie presente en la casa.")
    parser.add_argument("-or","--override-status",    nargs=1, choices=on_off_choices, help="Setea funcionalidad OVERRIDE. Si está activada, el servidor sobreescribirá output del pin si su estado ha sido cambiado por otro proceso. En caso contrario, se mantiene última modificación al output.")
    # Opciones de conexión con el servidor
    parser.add_argument("-H", "--hosts",         nargs="+", help="Lista de hosts a los que intentar conectarse. Por defecto, se usa '{}'".format(HOSTS))
    parser.add_argument("-P", "--port",         nargs=1, type=int, help="Puerto del host. Por defecto, se usa el '{}'".format(PORT))
    args = parser.parse_args()

    # PARSEAR ARGUMENTOS
    argsdict = vars(args)
    # Puerto debe ser válido
    if args.port is None:
        args.port = [DEFAULT_PORT]
    if args.port[0] < 1024:
            panic("Error: El nro de puerto debe ser mayor a 1024", parser)
    # Si no se ingresan hosts, usar los por defecto
    if args.hosts is None:
        args.hosts = HOSTS
    # Si no se entregó argumentos (o solo puerto y/o hosts), se asume status=graphic
    if (len(sys.argv) == 1 or
            (not args.add and
             not args.remove and
             args.set_name is None and
             args.set_value is None and
             args.set_randomize == 0 and
             args.on_time is None and
             args.off_time is None and
             args.absent_mode is None and
             args.override_status is None)):
        args.status = "graphic"
        print argsdict
        return argsdict
    # opciones para dispositivo NO pueden especificarse sin especificar qué dispositivo se quiere configurar
    if args.disp is None:
        if (args.set_value is not None or
            args.on_time is not None or
            args.off_time is not None or
            args.set_name is not None or
            args.set_randomize != 0 or
            args.add or
            args.remove):
            panic("Error: Debe especificar un dispositivo al cual asignar esta opción!", parser)
    # Horas ingresadas deben ser válidas
    if (args.on_time is not None and
            (args.on_time[0] not in range(24) or
             args.on_time[1] not in range(60))):
        panic("Error: La hora de encendido '{}:{}' no es válida".format(args.on_time[0], args.on_time[1]), parser)
    if (args.off_time is not None and
            (args.off_time[0] not in range(24) or
             args.off_time[1] not in range(60))):
        panic("Error: La hora de apagado '{}:{}' no es válida".format(args.off_time[0], args.off_time[1]), parser)
    # Si quiere agregar dispositivo, debe tener Nombre, gpio, hora inicio y hora término
    if (args.add and
            (args.set_name is None or
             args.disp is None or
             args.on_time is None or
             args.off_time is None)):
        panic("Error: Faltan parámetros para agregar dispositivo. Debe especificar --disp --set-name --on-time --off-time", parser)
    # No se puede agregar y eliminar al mismo tiempo un dispositivo
    if args.add and args.remove:
        panic("Error: No se puede simultáneamente agregar y eliminar un dispositivo", parser)
    # Reemplazar on-1-enabled-true por True
    # Reemplazar off-0-disabled-false por False
    for arg in argsdict:
        if argsdict[arg] is not None and type(argsdict[arg]) is list and argsdict[arg][0] in on_off_choices:
            if argsdict[arg][0] in ["on", "1", "enable", "true"]:
                argsdict[arg] = True
            else:
                argsdict[arg] = False

    print argsdict
    return argsdict  
##############################################################
# Conexión y funcionamiento general
##############################################################
"""
    Recibe los argumentos enviados al servidor, y la respuesta del servidor a la petición.
    Según lo que se le pidió al servidor, se despliega la respuesta correspondientemente.
    Puede recibir:
        - "OK" si se le pidió setear un dispositivo
        - json con status, si se le pidió el status
"""
def serve(args, reply):
    print "Respuesta: "+ reply
    # Si se pidió status, ignorar todo el resto y priorizar esta orden (eso es lo que hará el servidor)
    if args["status"] is not None:
        if args["status"] == "graphic":
            from yaml import load
            drawPanel(load(reply))
        else:
            print reply
    else:
        # Abortar si el servidor no fue capaz de procesar la petición
        if reply != "OK":
            print ROJO_CLARO + "Error: El servidor encontró errores en la petición" + NO_COLOR
            return
        return


    # c_a = args.split()
    # if c_a[0] == "absent_mode":
    #     if reply == "OK":
    #         print "Modo Ausente {}".format("Habilitado" if (c_a[1] == "on" or c_a[1] == "enabled" or c_a[1] == "1") else "Deshabilitado")
    #     else:
    #         print "Error: '{}'".format(reply)
    # elif c_a[0] == "status":
    #     if len(c_a) == 1:
    #         from yaml import load
    #         drawPanel(load(reply))
    #     else:
    #         print reply

def connect(HOSTS, PORT):
    import socket
    for host in HOSTS:
        print "Intentando conectarse con '{}:{}'".format(host, PORT)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: 
            s.settimeout(TIMEOUT)
            s.connect((host,PORT))
            s.settimeout(None)
            s.send(KEY)
            reply = s.recv(1024)
            if reply != "OK":
                s.close()
                print ROJO_CLARO + "Llave del cliente no coincide con la del servidor" + NO_COLOR
                exit(1)
            print "Conexión establecida con éxito"
            return s
        except socket.error, msg:
            print "Except al intentar conectarse: {}".format(msg)
            s.settimeout(None)
            s.close()
            pass
    print "Fue imposible conectarse. Abortando."
    exit()

###########################################################################
# MAIN
###########################################################################
def main():
    args = parseArguments()
    #import socket
    #import yaml
    from subprocess import call
    s = connect(args["hosts"], args["port"][0])
    print "Enviando request..."
    import json
    s.send(json.dumps(args))
    reply = s.recv(2048)
    s.close()
    serve(args, reply)

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