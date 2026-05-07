from gpiozero import DigitalInputDevice, LED
from signal import pause
import subprocess
import os
import threading
import time
import signal
import sys

# ── Configuration ────────────────────────────────────────────────────────────
GPIO_SOUND = 17
GPIO_LED = 27
VIDEO = "/home/wokkel/kalmeer_video.mp4"
LOCK_TIME = 60  # seconds video plays / system stays locked
TRIGGER_WINDOW = 45  # seconds within which triggers must occur
TRIGGERS_NEEDED = 3

# ── Startup checks ───────────────────────────────────────────────────────────
if not os.path.isfile(VIDEO):
    raise FileNotFoundError(f"Video niet gevonden: {VIDEO}")

if not os.access("/dev/fb0", os.W_OK):
    raise PermissionError(
        "Geen schrijfrechten op /dev/fb0.\n"
        "Voer uit: sudo chmod a+w /dev/fb0\n"
        "Of maak een udev regel aan voor een permanente oplossing."
    )

# Verberg terminal cursor en wis scherm
subprocess.run(["setterm", "--cursor", "off"], stderr=subprocess.DEVNULL)
subprocess.run(["clear"], stderr=subprocess.DEVNULL)

# ── Hardware ─────────────────────────────────────────────────────────────────
sensor = DigitalInputDevice(GPIO_SOUND, pull_up=False, bounce_time=None)
led = LED(GPIO_LED)

# ── Shared state (always access inside `state_lock`) ─────────────────────────
state_lock = threading.Lock()
locked = False
player = None
timer = None
trigger_times = []
_running = True  # set to False on shutdown to stop background timers
TRIGGER_COOLDOWN = 10  # seconds between accepted triggers
last_trigger_time = 0.0


# ── Display helpers ───────────────────────────────────────────────────────────
FB_DEVICE = "/dev/fb0"


def _fb_size():
    """Geeft de totale grootte van de framebuffer in bytes."""
    try:
        with open("/sys/class/graphics/fb0/virtual_size") as f:
            w, h = map(int, f.read().strip().split(","))
        with open("/sys/class/graphics/fb0/bits_per_pixel") as f:
            bpp = int(f.read().strip())
        return w * h * (bpp // 8)
    except Exception:
        return 1920 * 1080 * 4  # fallback: Full HD 32-bit


def screen_off():
    """Maakt de framebuffer zwart -> volledig zwart scherm op de projector."""
    try:
        size = _fb_size()
        with open(FB_DEVICE, "wb") as fb:
            chunk = b"\x00" * (1024 * 1024)
            written = 0
            while written < size:
                block = min(len(chunk), size - written)
                fb.write(chunk[:block])
                written += block
    except Exception as e:
        print(f"screen_off fout: {e}")


def screen_on():
    """Ververs de tty zodat mpv een schoon scherm krijgt."""
    subprocess.run(["chvt", "2"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["chvt", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ── Counter reset (runs every second in background) ──────────────────────────
def reset_counter():
    global trigger_times

    if not _running:
        return  # stop spawning timers on shutdown

    with state_lock:
        if not locked and trigger_times:
            now = time.time()
            old_count = len(trigger_times)
            trigger_times = [t for t in trigger_times if now - t <= TRIGGER_WINDOW]
            if old_count > 0 and not trigger_times:
                print("45 seconden voorbij -> teller reset naar 0/3")

    threading.Timer(1, reset_counter).start()


# ── Stop show ────────────────────────────────────────────────────────────────
def stop_show():
    global locked, player, timer, trigger_times

    with state_lock:
        if player and player.poll() is None:
            try:
                os.killpg(os.getpgid(player.pid), signal.SIGTERM)
            except Exception:
                pass
        player = None
        timer = None
        trigger_times = []
        locked = False
        last_trigger_time = 0.0

    led.off()
    screen_off()
    print("Video uit, scherm in slaapstand, teller reset naar 0/3")


# ── Start show ───────────────────────────────────────────────────────────────
def start_show():
    global locked, player, timer, trigger_times

    with state_lock:
        locked = True
        trigger_times = []

    screen_on()
    led.on()
    print("Signalen waargenomen: 3/3")
    print("3 geluidssignalen binnen 45 seconden -> video START")

    proc = subprocess.Popen(
        [
            "mpv",
            "--vo=drm",
            "--fs",
            "--no-border",
            "--really-quiet",
            "--no-terminal",
            "--no-config",
            "--cache=no",
            VIDEO,
        ],
        env=os.environ.copy(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # own process group → os.killpg works correctly
    )

    with state_lock:
        player = proc

    t = threading.Timer(LOCK_TIME, stop_show)
    t.start()

    with state_lock:
        timer = t


# ── Sound trigger callback (runs in gpiozero thread) ─────────────────────────
def triggered():
    global trigger_times, last_trigger_time

    with state_lock:
        if locked:
            print("Trigger genegeerd: video speelt of lock actief")
            return

        now = time.time()

        # Cooldown: ignore signals within 10s of the last accepted trigger
        if now - last_trigger_time < TRIGGER_COOLDOWN:
            remaining = round(TRIGGER_COOLDOWN - (now - last_trigger_time))
            print(f"Trigger genegeerd: cooldown actief ({remaining}s resterend)")
            return

        last_trigger_time = now
        trigger_times = [t for t in trigger_times if now - t <= TRIGGER_WINDOW]
        trigger_times.append(now)
        count = min(len(trigger_times), TRIGGERS_NEEDED)

    print(f"Signalen waargenomen: {count}/3")

    if count >= TRIGGERS_NEEDED:
        start_show()


# ── Clean shutdown ────────────────────────────────────────────────────────────
def shutdown():
    global _running
    _running = False
    stop_show()
    sensor.close()
    led.close()
    subprocess.run(["setterm", "--cursor", "on"], stderr=subprocess.DEVNULL)
    print("Afgesloten.")


# ── Main ──────────────────────────────────────────────────────────────────────
screen_off()
sensor.when_activated = triggered
reset_counter()

print("Klaar. Wacht op 3 geluidssignalen binnen 45 seconden.")
print("Scherm staat in slaapstand zolang er geen video speelt.")

try:
    pause()
except KeyboardInterrupt:
    shutdown()
    sys.exit(0)
