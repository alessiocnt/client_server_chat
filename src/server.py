#!/usr/bin/env python3
'''
------SERVER-------
Riceve pacchetti dalla rete, apre il messaggio e ne ricava le informazioni necessarie per svolgere i compiti a lui assodati:
- Inoltrare un messaggio al destinatario effettivio
- Gestire la connessione di un nuovo utente
- Gestire la disconnessione di un utente su richiesta esplicita
'''
import socket
import time
from threading import Thread

BUFSIZ = 1024   # Definisco la dimensione massima del buffer
# Definisco il server
server_ip = "195.001.010.010"
server_mac = "52:AB:0A:DF:10:DC"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("localhost", 8000))
server.listen(5)

online_users = {}   # Dictionary per per tener traccia degli utenti online {IP_user : mac_adress}
nicknames = {}  # Dictionary per per tener traccia dei nickname riferiti agli utenti {IP_user : nickname}
clients = {}    # Dictionary per per tener traccia delle connessioni dirette al server {mac_adress : socket}

def attendi_posta(conn):    # Gestisce l'arrivo di nuovi messaggi
    while True:
        received_message = conn.recv(BUFSIZ)  # Metto in ascolto
        received_message =  received_message.decode("utf-8")
        # Salvo la connessione, se già presente andrà a sovrascrivere
        clients[received_message[0:17]] = conn
        if am_i_receiver(received_message) == False:    # Controllo se il destinatario effettivo del messaggio è il server o un altro utente aprendo il messaggio
            # Giunto qui sono certo che il destinatario sia un'utente diverso dal server
            # Il server deve quindi indirizzare il messaggio all'utente corretto
            # Se il destinatario non è online devo notificarlo al mittente
            sender = received_message[34:49]
            reciver = received_message[64:79]
            # Ricompongo header e messaggio
            if reciver in online_users: # Se il destinatario è in linea gli mando il messaggio
                # Creo il nuovo header andando a cercare il mac di destinazione nella tabella online_users
                header = create_header(server_ip, server_mac, reciver, online_users[reciver])
                message = "[" + nicknames[sender] + "] \n" + received_message[79:]
                packet = header + message
                clients[online_users[reciver]].send(bytes(packet, "utf-8")) # Invio il pacchetto dati sul socket corretto
                print("Messaggio di: [%s] - %s inoltrato a: [%s] - %s" % (nicknames[sender], sender, nicknames[reciver], reciver))
            else: # Avverto il mittente che il destinatario da lui scelto non si trova in linea
                try:    # Prevengo il caso in cui un utente mai registrato cerchi di inviare un messaggio
                    # Creo il nuovo header andando a cercare il mac di destinazione del mittente
                    header = create_header(server_ip, server_mac, sender, online_users[sender])
                    message = "Sorry! This user is not online."
                    packet = header + message
                    clients[online_users[sender]].send(bytes(packet, "utf-8"))  # Invio il pacchetto dati sul socket corretto
                    print("Utente non in linea.")
                except KeyError:    # Passo di nuovo in attesa
                    continue

def am_i_receiver(recv_msg):    # Controllo se il destinatario è il server o un utente ed agisco di conseguenza
    destination_ip = recv_msg[64:79]
    if destination_ip == server_ip: # Se il destinatario è il server o c'è una richiesta di connessione oppure di disconnessione
        if exit_check(recv_msg) == False: # Il mittente non è intenzionato ad uscire dall'applicativo
            save_nickname(recv_msg) # Salvo il nickname dell'utente
            save_user(recv_msg) # Salvo le info relative al mittente
        return True
    return False

def save_nickname(recv_msg):    # Salvo il nickname dell'utente
    user_ip = recv_msg[34:49]
    nicknames[user_ip] = recv_msg[79:]  # Aggiorno la tabella nicknames

def save_user(recv_msg):    # Salvo le info relative al mittente
    source_ip = recv_msg[34:49]
    source_mac = recv_msg[0:17]
    online_users[source_ip] = source_mac    # Aggiorno la tabella online_users
    print("Nuovo utente [%s] con IP: %s salvato." % (nicknames[source_ip], source_ip))
    send_welcome_message(source_ip)

def send_welcome_message(destination_ip):   # Invio un messaggio di benvenuto
    header = create_header(server_ip, server_mac, destination_ip, online_users[destination_ip])
    message = "You are connected! - Start chatting now."
    packet = header + message
    clients[online_users[destination_ip]].send(bytes(packet, "utf-8"))  # Invio il pacchetto dati sul socket corretto

def exit_check(recv_msg):   # Controllo se devo uscire -> True se esce, False altrimenti
    message = recv_msg[79:]
    if message == "{quit}": # Controllo se il messaggio corrisponde alla sequenza necessaria per la disconnessione
        user_ip = recv_msg[34:49]
        try:    # Prevengo il caso in cui un utente mai registrato cerchi di uscire
            print("Disconnessione utente [%s] con IP: %s." % (nicknames[user_ip], user_ip))
            del online_users[user_ip]   # Rimuovo l'utente dalle varie tabelle in cui è salvato
            del nicknames[user_ip]
            return True
        except KeyError:    # Considero il caso come un'uscita dall'applicativo
            return True
    return False

def create_header(source_ip, source_mac, destination_ip, destination_mac):  # Creo l'header con i parametri passati al metodo
    IP_header = "" + source_ip + destination_ip
    ethernet_header = "" + source_mac + destination_mac
    header = ethernet_header + IP_header
    return header   # restituisco una variabile che è l'header costruito

while True: # Attendo le connessioni
    print("In attesa di connessioni...")
    socket, address = server.accept()   # Accetto nuove connessioni
    Thread(target=attendi_posta, args=(socket,)).start()    # Creo un thread per mettermi in ascolto del client
    print("Connessione effettuata")
