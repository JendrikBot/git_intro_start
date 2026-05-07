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
def _display_env():
    """Build env for X11 apps (mpv). Uses wokkel's Xauthority."""
    env = os.environ.copy()
    env["DISPLAY"] = ":0"
    env["XAUTHORITY"] = "/home/wokkel/.Xauthority"
    return env


def _try_vcgencmd(power: str) -> bool:
    """Try vcgencmd display_power. Returns True if it succeeded."""
    r = subprocess.run(
        ["vcgencmd", "display_power", power],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return r.returncode == 0


def _try_xrandr(on: bool):
    """Fallback: use xrandr to turn the display on or off."""
    env = _display_env()
    # Detect the connected output name (e.g. HDMI-1, HDMI-A-1)
    result = subprocess.run(["xrandr"], env=env, capture_output=True, text=True)
    output = None
    for line in result.stdout.splitlines():
        if " connected" in line:
            output = line.split()[0]
            break
    if output:
        action = "--auto" if on else "--off"
        subprocess.run(
            ["xrandr", "--output", output, action],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def screen_off():
    """Turn display off — tries vcgencmd first, falls back to xrandr."""
    if not _try_vcgencmd("0"):
        print("vcgencmd niet beschikbaar, gebruik xrandr")
        _try_xrandr(on=False)


def screen_on():
    """Turn display on — tries vcgencmd first, falls back to xrandr."""
    if not _try_vcgencmd("1"):
        _try_xrandr(on=True)


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

    env = _display_env()
    proc = subprocess.Popen(
        [
            "mpv",
            "--fs",
            "--no-border",
            "--really-quiet",
            "--no-terminal",
            "--no-config",
            "--cache=no",
            VIDEO,
        ],
        env=env,
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
