# ------------------------------------------------------------
# OUTPUT-TEST VOOR HOOFDSCRIPT (GEEN HARDWARE NODIG)
# ------------------------------------------------------------
# Dit bestand simuleert ALLE logica van jullie hoofdscript:
# - trigger teller (3 signalen binnen 45s)
# - cooldown van 10s
# - lock tijdens video
# - automatische reset na 45s
# - prints die identiek zijn aan het echte script
#
# Er wordt GEEN hardware gebruikt:
# - geen GPIO
# - geen mpv
# - geen schermcommando’s
# - geen threading
#
# Hierdoor kan je de logica testen op een gewone computer.


import time

# ------------------------------------------------------------
# GLOBALE VARIABELEN (zoals in jullie hoofdscript)
# ------------------------------------------------------------

locked = False  # True wanneer video speelt of lock actief is
trigger_times = []  # lijst met tijdstippen van triggers
last_trigger_time = 0.0  # tijdstip van laatste geaccepteerde trigger

TRIGGER_WINDOW = 45  # tijdsvenster waarin 3 triggers moeten vallen
TRIGGERS_NEEDED = 3  # aantal triggers nodig om video te starten
TRIGGER_COOLDOWN = 10  # minimum tijd tussen twee geldige triggers


# ------------------------------------------------------------
# FUNCTIE: reset_counter_sim
# ------------------------------------------------------------
# In het echte script draait deze functie elke seconde.
# Ze verwijdert oude triggers die ouder zijn dan 45 seconden.
# Als hierdoor de teller leeg wordt, print ze een reset-melding.
def reset_counter_sim(now):
    global trigger_times
    old = len(trigger_times)

    # verwijder triggers ouder dan 45 seconden
    trigger_times = [t for t in trigger_times if now - t <= TRIGGER_WINDOW]

    # als er vroeger triggers waren maar nu niet meer → reset
    if old > 0 and not trigger_times:
        print("45 seconden voorbij -> teller reset naar 0/3")


# ------------------------------------------------------------
# FUNCTIE: stop_show_sim
# ------------------------------------------------------------
# Simuleert het einde van de video:
# - lock uit
# - teller reset
# - print identiek aan hoofdscript
def stop_show_sim():
    global locked, trigger_times, last_trigger_time
    locked = False
    trigger_times = []
    last_trigger_time = 0.0
    print("Video uit, scherm in slaapstand, teller reset naar 0/3")


# ------------------------------------------------------------
# FUNCTIE: start_show_sim
# ------------------------------------------------------------
# Simuleert het starten van de video:
# - lock aan
# - teller reset
# - prints identiek aan hoofdscript
# - daarna direct stop_show_sim() (in echt script gebeurt dit na 60s)
def start_show_sim():
    global locked, trigger_times
    locked = True
    trigger_times = []

    print("Signalen waargenomen: 3/3")
    print("3 geluidssignalen binnen 45 seconden -> video START")

    # In het echte script speelt mpv 60 seconden.
    # In de test stoppen we onmiddellijk.
    stop_show_sim()


# ------------------------------------------------------------
# FUNCTIE: triggered_sim
# ------------------------------------------------------------
# Simuleert de geluidssensor-trigger:
# - checkt lock
# - checkt cooldown
# - telt triggers binnen 45s
# - start video bij 3 triggers
# - print identiek aan hoofdscript
def triggered_sim(now):
    global locked, trigger_times, last_trigger_time

    # 1. Als video speelt → trigger negeren
    if locked:
        print("Trigger genegeerd: video speelt of lock actief")
        return

    # 2. Cooldown check (10 seconden)
    if now - last_trigger_time < TRIGGER_COOLDOWN:
        remaining = round(TRIGGER_COOLDOWN - (now - last_trigger_time))
        print(f"Trigger genegeerd: cooldown actief ({remaining}s resterend)")
        return

    # 3. Trigger accepteren
    last_trigger_time = now

    # verwijder oude triggers
    trigger_times = [t for t in trigger_times if now - t <= TRIGGER_WINDOW]
    trigger_times.append(now)

    # teller printen
    count = min(len(trigger_times), TRIGGERS_NEEDED)
    print(f"Signalen waargenomen: {count}/3")

    # 4. Bij 3 triggers → video starten
    if count >= TRIGGERS_NEEDED:
        start_show_sim()


# ------------------------------------------------------------
# TESTCASES
# ------------------------------------------------------------
# Deze testcases simuleren typische scenario’s uit jullie project.


print("TEST 1 — drie geldige triggers binnen 45 seconden")
t = 0
triggered_sim(t)  # 1/3
triggered_sim(t + 15)  # 2/3
triggered_sim(t + 30)  # 3/3 → video start → video stopt


print("\nTEST 2 — cooldown werkt")
t = 100
triggered_sim(t)  # 1/3
triggered_sim(t + 3)  # genegeerd (cooldown)
triggered_sim(t + 12)  # 2/3


print("\nTEST 3 — lock werkt")
locked = True
triggered_sim(200)  # genegeerd omdat video speelt


print("\nTEST 4 — reset na 45 seconden")
trigger_times = [0]  # 1 oude trigger
reset_counter_sim(50)  # moet reset printen
