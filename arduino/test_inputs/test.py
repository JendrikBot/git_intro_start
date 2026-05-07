from gpiozero import DigitalInputDevice, LED
import subprocess
import os
import time
import sys
import threading

# ── Zelfde instellingen als hoofdscript ──────────────────────────────────────
GPIO_SOUND = 17
GPIO_LED = 27
VIDEO = "/home/wokkel/kalmeer_video.mp4"

DISPLAY_ENV = {**os.environ, "DISPLAY": ":0", "XAUTHORITY": "/home/wokkel/.Xauthority"}

PASS = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"
INFO = "\033[94m→\033[0m"


def header(title):
    print(f"\n\033[1m{'─'*50}\033[0m")
    print(f"\033[1m  {title}\033[0m")
    print(f"\033[1m{'─'*50}\033[0m")


def ask(question):
    return input(f"\n  {INFO} {question} [j/n]: ").strip().lower() == "j"


def wait(msg, seconds):
    print(f"  {INFO} {msg}", end="", flush=True)
    for _ in range(seconds):
        time.sleep(1)
        print(".", end="", flush=True)
    print()


results = {}

# ════════════════════════════════════════════════════════════════════════════
# TEST 1 — Videobestand
# ════════════════════════════════════════════════════════════════════════════
header("TEST 1 — Videobestand aanwezig")
if os.path.isfile(VIDEO):
    size_mb = os.path.getsize(VIDEO) / (1024 * 1024)
    print(f"  {PASS} Gevonden: {VIDEO} ({size_mb:.1f} MB)")
    results["video_bestand"] = True
else:
    print(f"  {FAIL} Niet gevonden: {VIDEO}")
    print(f"       Zorg dat het bestand op het juiste pad staat.")
    results["video_bestand"] = False

# ════════════════════════════════════════════════════════════════════════════
# TEST 2 — vcgencmd (schermcontrole)
# ════════════════════════════════════════════════════════════════════════════
header("TEST 2 — Scherm AAN/UIT via vcgencmd")
try:
    r = subprocess.run(["vcgencmd", "display_power"], capture_output=True, text=True)
    print(f"  {INFO} Huidige status: {r.stdout.strip()}")

    print(f"  {INFO} Scherm UIT over 2 seconden...")
    time.sleep(2)
    subprocess.run(
        ["vcgencmd", "display_power", "0"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)
    subprocess.run(
        ["vcgencmd", "display_power", "1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  {INFO} Scherm terug AAN.")

    ok = ask("Was het scherm 3 seconden zwart en daarna terug aan?")
    results["vcgencmd"] = ok
    print(
        f"  {PASS if ok else FAIL} vcgencmd schermcontrole: {'OK' if ok else 'MISLUKT'}"
    )
except FileNotFoundError:
    print(f"  {FAIL} vcgencmd niet gevonden — niet op een Raspberry Pi?")
    results["vcgencmd"] = False

# ════════════════════════════════════════════════════════════════════════════
# TEST 3 — LED op GPIO 27
# ════════════════════════════════════════════════════════════════════════════
header("TEST 3 — LED op GPIO 27")
try:
    led = LED(GPIO_LED)
    print(f"  {INFO} LED aan voor 3 seconden...")
    led.on()
    time.sleep(3)
    led.off()
    ok = ask("Brandde de LED 3 seconden?")
    results["led"] = ok
    print(f"  {PASS if ok else FAIL} LED test: {'OK' if ok else 'MISLUKT'}")
    led.close()
except Exception as e:
    print(f"  {FAIL} GPIO fout: {e}")
    results["led"] = False

# ════════════════════════════════════════════════════════════════════════════
# TEST 4 — Geluidssensor pin-uitlezing (raw)
# ════════════════════════════════════════════════════════════════════════════
header("TEST 4 — Geluidssensor pin-waarde (raw, 5 seconden)")
try:
    # Test both pull_up=True and pull_up=False to see what changes
    for pull, label in [
        (True, "pull_up=True  (actief = LAAG)"),
        (False, "pull_up=False (actief = HOOG)"),
    ]:
        sensor_raw = DigitalInputDevice(GPIO_SOUND, pull_up=pull)
        values = []
        print(f"\n  {INFO} {label}")
        print(f"       Maak 5 seconden lang geluid (klap, fluiten, ...)")
        print(f"       Meting loopt", end="", flush=True)
        for _ in range(50):
            values.append(sensor_raw.value)
            time.sleep(0.1)
            print(".", end="", flush=True)
        print()
        unique = set(values)
        changed = len(unique) > 1
        counts = {v: values.count(v) for v in unique}
        print(f"       Waarden gezien: {counts}")
        if changed:
            print(f"  {PASS} Pin veranderde van waarde → sensor reageert met {label}")
        else:
            print(
                f"  {FAIL} Pin bleef constant op {values[0]} → geen reactie met {label}"
            )
        sensor_raw.close()
        time.sleep(0.5)

    results["sensor_raw"] = ask("Veranderde een van de twee metingen van waarde?")
except Exception as e:
    print(f"  {FAIL} GPIO fout: {e}")
    results["sensor_raw"] = False

# ════════════════════════════════════════════════════════════════════════════
# TEST 5 — when_activated callback
# ════════════════════════════════════════════════════════════════════════════
header("TEST 5 — Trigger callback (pull_up=False, 10 seconden)")
trigger_count = 0


def on_trigger():
    global trigger_count
    trigger_count += 1
    print(f"  {PASS} Trigger #{trigger_count} ontvangen!")


try:
    sensor_cb = DigitalInputDevice(GPIO_SOUND, pull_up=False, bounce_time=0.05)
    sensor_cb.when_activated = on_trigger

    print(f"  {INFO} Maak meerdere keren geluid in de volgende 10 seconden...")
    wait("Wachten", 10)
    sensor_cb.close()

    if trigger_count >= 3:
        print(f"  {PASS} {trigger_count} triggers ontvangen — callback werkt correct")
        results["callback"] = True
    elif trigger_count > 0:
        print(
            f"  {INFO} {trigger_count} trigger(s) ontvangen — werkt, maar gevoeligheid aanpassen?"
        )
        results["callback"] = True
    else:
        print(f"  {FAIL} Geen enkele trigger ontvangen")
        print(f"       Controleer:")
        print(f"       • DO-pin van sensor → GPIO {GPIO_SOUND}")
        print(f"       • GND sensor → GND Pi")
        print(f"       • VCC sensor → 3.3V of 5V Pi")
        print(f"       • Drempel-potentiometer op de sensor bijstellen")
        results["callback"] = False
except Exception as e:
    print(f"  {FAIL} GPIO fout: {e}")
    results["callback"] = False

# ════════════════════════════════════════════════════════════════════════════
# TEST 6 — MPV videospeler
# ════════════════════════════════════════════════════════════════════════════
header("TEST 6 — MPV videospeler (5 seconden)")
if not results.get("video_bestand"):
    print(f"  {INFO} Overgeslagen — videobestand niet gevonden (zie Test 1)")
    results["mpv"] = False
else:
    try:
        print(f"  {INFO} Video start over 2 seconden voor 5 seconden...")
        time.sleep(2)
        proc = subprocess.Popen(
            [
                "mpv",
                "--fs",
                "--no-border",
                "--really-quiet",
                "--no-terminal",
                "--length=5",
                VIDEO,
            ],
            env=DISPLAY_ENV,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        proc.wait(timeout=10)
        ok = ask("Speelde de video 5 seconden fullscreen?")
        results["mpv"] = ok
        print(f"  {PASS if ok else FAIL} MPV test: {'OK' if ok else 'MISLUKT'}")
    except FileNotFoundError:
        print(f"  {FAIL} mpv niet gevonden — installeer: sudo apt install mpv")
        results["mpv"] = False
    except Exception as e:
        print(f"  {FAIL} Fout: {e}")
        results["mpv"] = False

# ════════════════════════════════════════════════════════════════════════════
# SAMENVATTING
# ════════════════════════════════════════════════════════════════════════════
header("SAMENVATTING")
labels = {
    "video_bestand": "Videobestand aanwezig",
    "vcgencmd": "Schermcontrole (vcgencmd)",
    "led": "LED op GPIO 27",
    "sensor_raw": "Sensor pin-uitlezing",
    "callback": "Trigger callback",
    "mpv": "MPV videospeler",
}
all_ok = True
for key, label in labels.items():
    ok = results.get(key, False)
    if not ok:
        all_ok = False
    print(f"  {PASS if ok else FAIL}  {label}")

print()
if all_ok:
    print(f"  \033[92mAlle tests geslaagd — hoofdscript zou moeten werken.\033[0m")
else:
    print(f"  \033[91mEen of meer tests mislukt — zie details hierboven.\033[0m")
print()
