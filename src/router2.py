#!/usr/bin/env python3
'''
------ROUTER2-------
Riceve pacchetti su due porte different (lato client e lato server) e deve smistarli opportunamente.
'''
import socket
import time
from threading import Thread

BUFSIZ = 1024    # Definisco la dimensione massima del buffer
# Apro una porta lato client
router = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
router.bind(("localhost", 9100))
# Apro una porta lato server
router_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
router_server.bind(("localhost", 9200))
# Definisco il router
router_mac_eth0 = "32:03:0A:DA:11:DC"
router_mac_eth1 = "32:03:0A:CF:10:DB"
# Il router conosce le info del server in quanto si trovano sullo stesso nodo
server = ("localhost", 8000)
server_ip = "195.001.010.010"
server_mac = "52:AB:0A:DF:10:DC"

router.listen(5)
router_server.connect(server) # Creo una connessione tra router e server
print("Connessione con il server effettuata.")
arp_table_socket = {server_ip : router_server}  # Aggiorno l'arp table
arp_table_mac = {server_ip : server_mac}

def attendi_da_server():    # Gestisce l'arrivo di nuovi messaggi da parte del server
    while True:
        received_message = router_server.recv(BUFSIZ)   # Metto in ascolto
        received_message =  received_message.decode("utf-8")
        # Decodifico l'header ed estraggo le informazioni
        source_mac = received_message[0:17]
        destination_mac = received_message[17:34]
        source_ip = received_message[34:49]
        destination_ip =  received_message[49:64]
        message = received_message[64:]
        # Creo il nuovo header andando a cercare il mac di destinazione nell'arp table
        ethernet_header = router_mac_eth0 + arp_table_mac[destination_ip]
        IP_header = source_ip + destination_ip
        packet = ethernet_header + IP_header + message
        try:    # Mi salvaguardo da eventuali errori di mancata connessione nel caso in cui il client si sia disconnesso
            destination_socket = arp_table_socket[destination_ip]
            destination_socket.send(bytes(packet, "utf-8")) # Invio il pacchetto dati
            print("Inoltro pacchetto da server (%s) a %s." % (source_ip, destination_ip))
        except ConnectionResetError:
            continue    # Se avviene un errore mi rimetto in ascolto direttamente passando al ciclo successivo
        #time.sleep(1)   # Attendo un secondo tra un ciclo e quello successivo in modo da non sovraccaricare la macchina

def attendi_da_clients(conn):    # Gestisce l'arrivo di nuovi messaggi da parte dei clients
    while True:
        try:
            received_message = conn.recv(BUFSIZ)    # Metto in ascolto
            received_message =  received_message.decode("utf-8")
        except ConnectionResetError:
            break   # Se avviene un errore mi esco dal ciclo
        # Decodifico l'header ed estraggo le informazioni
        source_mac = received_message[0:17]
        destination_mac = received_message[17:34]
        source_ip = received_message[34:49]
        destination_ip =  received_message[49:64]
        message = received_message[64:]
        # Aggiorno l'arp table
        arp_table_socket[source_ip] = conn
        arp_table_mac[source_ip] = source_mac
        # Creo il nuovo header andando a cercare il mac di destinazione nell'arp table
        ethernet_header = router_mac_eth1 + arp_table_mac[destination_ip]
        IP_header = source_ip + destination_ip
        packet = ethernet_header + IP_header + message
        # Scelgo il socket relativo al destination_ip coerente sfruttando l'arp table
        destination_socket = arp_table_socket[destination_ip]
        destination_socket.send(bytes(packet, "utf-8")) # Invio il pacchetto dati
        print("Inoltro pacchetto di: %s a %s." % (source_ip, destination_ip))
        #time.sleep(1)   # Attendo un secondo tra un ciclo e quello successivo in modo da non sovraccaricare la macchina

# Creo il thread che in background attenderà l'arrivo di nuovi messaggi da parte del server
Thread(target=attendi_da_server).start()

while True: # Attendo le connessioni da parte dei clients
    print("In attesa di connessioni...")
    client, address = router.accept()   # Accetto nuove connessioni
    Thread(target=attendi_da_clients, args=(client,)).start() # Creo un thread per mettermi in ascolto del client
    print("Client connesso.")
