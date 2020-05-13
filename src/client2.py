#!/usr/bin/env python3
'''
------CLIENT 2-------
Riceve pacchetti dalla rete e a sua volta ne può inviare alcuni
pkt = ethernet_header + IP_header + messaggio
Il messaggio contiene come primo elemento l'indirizzo IP dello user effettivo a cui il messaggio è indirizzato.
In questo modo il server è in grado di capire a chi è rivolto tale messaggio.
Per fare in modo che l'applicativo sia estendibile ed utilizzabile anche con Client con IP differenti ho scelto di usare IP "completi", inserendo 0 in modo da avere quattro triplette di caratteri.
'''
import sys
import socket
from threading import Thread
import tkinter as tkt

BUFSIZ = 1024   # Definisco la dimensione massima del buffer
# Definisco il client
client_ip = "092.010.010.020"
client_mac = "10:AF:CB:EF:19:CF"
router_mac = "55:04:0A:EF:11:CF" # Il client conosce il mac del router in quanto si trovano sullo stesso nodo
server_ip = "195.001.010.010"

router = ("localhost", 8100)
# Apro una porta sul client
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.bind(("localhost", 1200))
client.connect(router)

def receive():  # Gestisce l'arrivo di messaggi
    while True:
        # Attendo i messaggi in entrata
        try:
            msg = client.recv(BUFSIZ).decode("utf8")
            msg = msg[64:]
            msg_list.insert(tkt.END, msg) # Faccio display dei messaggi nel Listbox
            # Nel caso di errore e' probabile che il client abbia abbandonato la chat.
        except OSError:
            break

def send(event=None):  # Gestisce l'invio di nuovi messaggi
    msg = my_msg.get()  # Leggo il messaggio che l'utente ha inserito
    user_destination_ip = dest_ip.get() # Leggo il destinatario del messaggio
    my_msg.set("Message here")  # Reimposto le diciture delle textvariable
    dest_ip.set("Destination IP")
    # Creo l'header (il destinatario è il server, ma inserisco come mac-adress quello del router a cui sono collegato così che possa indirizzare il messaggio al destinatario)
    header = create_header(client_ip, client_mac, server_ip, router_mac)
    message = "" + user_destination_ip + msg  # Nel messaggio inserisco l'informazione di quello che sarà il destinatario effettivo del messaggio (user fisico)
    packet = header + message   # Impacchetto header e messaggio
    client.send(bytes(packet, "utf-8")) # Spedisco il pacchetto al router

def ask_for_nickname():    # Gestisco la richiesta del nickname
    nickname = my_nickname.get()    # Leggo il nickname che l'utente ha inserito
    # Creo l'header (il destinatario è il server, ma inserisco come mac-adress quello del router a cui sono collegato così che possa indirizzare il messaggio al destinatario)
    header = create_header(client_ip, client_mac, server_ip, router_mac)
    message = "" + server_ip + nickname # Creo il messaggio, qui il destinatario effettivio è il server stesso (userà questo pacchetto "introduttivo" per salvare le info relative al client)
    packet = header + message
    client.send(bytes(packet, "utf-8")) # Spedisco il pacchetto

def create_header(source_ip, source_mac, destination_ip, destination_mac):  # Creo l'header con i parametri passati al metodo
    IP_header = "" + source_ip + destination_ip
    ethernet_header = "" + source_mac + destination_mac
    header = ethernet_header + IP_header
    return header   # restituisco una variabile che è l'header costruito

def on_closing(event=None): # Gestisce cosa accade alla pressione del tasto quit
    msg = "{quit}"  # Questo è il messaggio che verrà inviato al server e lo riconoscerà come richiesta di disconnessione
    header = create_header(client_ip, client_mac, server_ip, router_mac)    # Creo l'header
    message = "" + server_ip + msg  # Il destinatario effettivo del messaggio è il server stesso
    packet = header + message
    client.send(bytes(packet, "utf-8")) # Invio il messaggio
    client.close()  # Termino la connessione tra client e router
    finestra.destroy()
    sys.exit()

# Creo la GUI e avvio il mainloop
# Gestisco la creazione dell'interfaccia grafica minimale per l'applicativo
finestra = tkt.Tk() # Creo la finestra
finestra.title("Client 2 - %s" % client_ip)  # Al posto del nome dell'applicativo imposto il clientIP per facilitare l'utilizzo
messages_frame = tkt.Frame(finestra)    # Creo il frame per i messaggi
my_nickname = tkt.StringVar()   # Variabile tipo stringa per contenere il nickname
my_nickname.set("Nickname here")
my_msg = tkt.StringVar()    # Variabile tipo stringa per contenere il messaggio
my_msg.set("Message here")
dest_ip = tkt.StringVar()   # Variabile tipo stringa per contenere l'IP del destinatario
dest_ip.set("Destination IP")
scrollbar = tkt.Scrollbar(messages_frame)   # Creo una scrollbar per navigare tra i messaggi.
msg_list = tkt.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)   # Creo un Listbox per contentere i messaggi
scrollbar.pack(side=tkt.RIGHT, fill=tkt.Y)
msg_list.pack(side=tkt.LEFT, fill=tkt.BOTH)
msg_list.pack()
messages_frame.pack()
msg_list.insert(tkt.END, "Welcome! \nSet your nickname to join the chat!") # Indico all'utente come comportarsi non appena avvia l'applicativo

input_nick_frame = tkt.Frame(finestra)    # Creo il frame per gestire l'input del nickname
nickname_field = tkt.Entry(input_nick_frame, textvariable=my_nickname)  # Creo il campo di input e lo associo alla variabile my_nickname
nickname_field.bind("<Return>", ask_for_nickname)   # lego la funzione ask_for_nickname al tasto Return
send_nick_button = tkt.Button(input_nick_frame, text="Set Nickname", command=ask_for_nickname)  # Creo il tasto Set Nickname e lo associo alla funzione ask_for_nickname
nickname_field.pack(side=tkt.LEFT, fill=tkt.BOTH)
send_nick_button.pack(side=tkt.RIGHT, fill=tkt.Y)
input_nick_frame.pack()

dest_field = tkt.Entry(finestra, textvariable=dest_ip)  # Creo il campo di input e lo associo alla variabile dest_ip
dest_field.pack(side=tkt.LEFT, fill=tkt.BOTH)
entry_field = tkt.Entry(finestra, textvariable=my_msg)  # Creo il campo di input e lo associo alla variabile my_msg
entry_field.bind("<Return>", send)  # lego la funzione send al tasto Return
entry_field.pack(side=tkt.LEFT, fill=tkt.BOTH)
bottom_buttons_frame = tkt.Frame(finestra)    # Creo il frame per gestire i bottoni
send_button = tkt.Button(bottom_buttons_frame, text="Send", command=send)   # Creo il tasto Send e lo associo alla funzione send
quit_button = tkt.Button(finestra, text="Quit", command=on_closing) # Creo il tasto Quit e lo associo alla funzione on_closing
send_button.pack(side=tkt.LEFT, fill=tkt.BOTH)
quit_button.pack(side=tkt.RIGHT, fill=tkt.Y)
bottom_buttons_frame.pack()

finestra.protocol("WM_DELETE_WINDOW", on_closing)
receive_thread = Thread(target=receive).start() # Creo il thread che in background attenderà l'arrivo di nuovi messaggi
tkt.mainloop()  # Avvio il mainloop di tkinter
