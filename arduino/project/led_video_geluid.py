from gpiozero import DigitalInputDevice, LED

# importeert digitale signalen van de pinnen en klasse om LED te activeren uit raspberry pi bibliotheek
from signal import pause
import subprocess

# andere programma's aanroepen vanuit python
import os

# operating system functies
import threading

# parallele taken binnen 1 programma
import time
import signal

# om signalen te versturen naar processen (zoals mpv stoppen)

GPIO_SOUND = 17  # geluidssensor op GPIO17
GPIO_LED = 27  # LED op GPIO27

VIDEO = "/home/wokkel/kalmeer_video.mp4"
LOCK_TIME = 60  # 1 minuut projectie + lockout

# LM393 is meestal active-low → pull_up=True
sensor = DigitalInputDevice(GPIO_SOUND, pull_up=True)
led = LED(GPIO_LED)

locked = False  # niet locked dus actie kan uitgevoerd worden
player = None  # placeholder voor mpv proces
timer = None


def stop_show():
    """Stop video + LED en maak systeem weer klaar voor nieuwe trigger."""
    global locked, player, timer

    # Stop mpv als het nog draait
    if player and player.poll() is None:
        try:
            # We starten mpv in z'n eigen process group -> killpg stopt mpv netjes/hard
            os.killpg(player.pid, signal.SIGTERM)
            # SIGTERM is een vriendelijk signaal om te stoppen, als mpv niet reageert kan je ook SIGKILL gebruiken
            # player.pid is het proces ID van mpv, killpg stopt alle processen in die groep (handig als mpv subprocesses heeft)
        except Exception:
            pass

    player = None
    timer = None
    led.off()
    locked = False
    print(" 1 minuut voorbij -> video uit, LED uit, weer klaar")


def triggered():
    global locked, player, timer

    if locked:
        print("Trigger genegeerd (nog in lock)")
        return

    locked = True
    led.on()
    print(" Trigger -> video START (max 60s)")

    env = (
        os.environ.copy()
    )  # kopieer huidige omgeving (handig om DISPLAY door te geven)
    env["DISPLAY"] = ":0"

    # Start mpv fullscreen
    # start_new_session=True => eigen process group (handig om later te stoppen)
    player = subprocess.Popen(
        ["mpv", "--fs", "--no-border", "--really-quiet", "--no-terminal", VIDEO],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    # Start 60s timer (nieuwe triggers verlengen dit niet)
    timer = threading.Timer(LOCK_TIME, stop_show)
    timer.start()


sensor.when_activated = triggered

print("Klaar. Wacht op geluid (GPIO17). LED op GPIO27.")
pause()
