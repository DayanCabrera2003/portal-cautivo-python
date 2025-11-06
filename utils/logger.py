import logging
import os

#Ruta al archivo de logs
LOG_FILE = "data/portal.log"

#Revisar que el archivo para guardar los logs exista
os.makedirs(os.path.dirname(LOG_FILE), exist_ok = True)

#Configuacion del logger
logger = logging.getLogger("portal_logger")
logger.setLevel(logging.INFO)

#Formato de los logs
formatter = logging.Formatter('%(asctime)s - %(levelname)s -%(message)s')

#Handler para la consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

#Handler para el archivo
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

#Agregar handlers al logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)