import adi
import numpy as np
import time

# ============================================================
#               RF TRANSMITTER CONFIGURATION
# ============================================================

PLUTO_IP = "ip:192.168.6.1"      # Change if SDR 5 uses another I

FREQUENCY = 2.4e9                # 2.4 GHz
SAMPLE_RATE = int(2e6)
BUFFER_SIZE = 4096

TX_GAIN = -10                    # Start safely
AMPLITUDE = 0.7                  # Signal amplitude

# ============================================================
#               CONNECT TO SDR
# ============================================================

print("Connecting to RF Source...")

sdr = adi.Pluto(PLUTO_IP)

sdr.sample_rate = SAMPLE_RATE
sdr.tx_rf_bandwidth = SAMPLE_RATE
sdr.tx_lo = int(FREQUENCY)
sdr.tx_hardwaregain_chan0 = TX_GAIN

print("Connected.")
print(f"Frequency : {FREQUENCY/1e9:.1f} GHz")
print(f"TX Gain   : {TX_GAIN} dB")

# ============================================================
#               CREATE TRANSMITTED SIGNAL
# ============================================================

t = np.arange(BUFFER_SIZE)

tone = (
    AMPLITUDE
    * np.exp(2j * np.pi * 100000 * t / SAMPLE_RATE)
).astype(np.complex64)

# ============================================================
#               START TRANSMITTING
# ============================================================

print("\nStarting transmission...")
print("Press Ctrl+C to stop.\n")

sdr.tx_cyclic_buffer = True
sdr.tx(tone)

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:

    print("\nStopping transmitter...")

    sdr.tx_destroy_buffer()

    print("Done.")
