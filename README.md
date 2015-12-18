# Domotica plazanorte

Acumulación de diseños de hardware y software de la implementación de domótica presente en mi casa.

Actualmente el sistema actual tiene las siguientes funcionalidades:
  - Servidor de archivos (con soporte SMB)
  - Servidor de descargas
  - Servidor web
  - Manejo de outputs de los GPIO

La automatización cubre:
  - Luz delantera
  - Luz trasera
  - Riego trasero y delantero

El hardware adicional documentado acá involucra:
  - Circuito para relés
  - Panel de status y de conexión de dispositivos

TODO:
  * Adaptar domotica.py a upgrades de domoclient.py
  * Capacidad de definir hora de encendido, hora de apagado, factor de aleatorización para dispositivos, con servidor ya inicializado
  * Capacidad de encender y apagar dispositivos
  * Integrar como servicio linux en init.d
  * Interfaz gráfica sencilla
  * Capacidad de setear característica Override-pin-state (si debiera tener cierto estado, pero no lo tiene (algo lo cambió por otro lado), forzarlo)
  * Implementar mayor flexibilidad para fijar horarios, tipo crontab