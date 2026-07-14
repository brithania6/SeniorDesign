import numpy as np
import time
import csv

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────

SDR_CONFIG = [
    {
        "sdr_id": 1,
        "ip": "ip:192.168.2.1",
        "frequency": 5.8e9,   # Vivaldi antenna
        "simulated": False
    },
    {
        "sdr_id": 2,
        "ip": "ip:192.168.3.1",
        "frequency": 5.8e9,   # Vivaldi antenna
        "simulated": False
    },
    {
        "sdr_id": 3,
        "ip": "ip:192.168.4.1",
        "frequency": 2.4e9,   # green patch antenna
        "simulated": False
    },
    {
        "sdr_id": 4,
        "ip": "ip:192.168.5.1",
        "frequency": 2.4e9,   # green patch antenna
        "simulated": False
    },
]

SAMPLE_RATE   = 2e6
GAIN          = 50
BUFFER_SIZE   = 1024
NUM_ROUNDS    = 0
DELAY_BETWEEN = 0.2
OUTPUT_CSV    = "data/rf_capture_log.csv"

# ─────────────────────────────────────────────
#  SIGNAL STRENGTH CLASSIFIER
# ─────────────────────────────────────────────

def classify_signal(peak_db):

    if peak_db > 50:
        return "HIGH"
    elif peak_db > 30:
        return "MEDIUM"
    else:
        return "LOW"

# ─────────────────────────────────────────────
#  ELAPSED TIME FORMATTER  →  HH:MM:SS.mmm
# ─────────────────────────────────────────────

def format_elapsed(start_time):
    
    elapsed = time.time() - start_time
    hours   = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = elapsed % 60
    return f"{hours:02}:{minutes:02}:{seconds:06.3f}"

# ─────────────────────────────────────────────
#  SIMULATED SDR (fallback if real one fails)
# ─────────────────────────────────────────────

def simulate_sdr_reading(sdr_id, frequency, round_num, start_time):
    
    noise   = np.random.normal(0, 0.01, BUFFER_SIZE) + 1j * np.random.normal(0, 0.01, BUFFER_SIZE)
    spike   = np.random.choice([0, 1], p=[0.7, 0.3])
    signal  = spike * (np.random.uniform(0.5, 1.5) * np.exp(1j * np.random.uniform(0, 2 * np.pi)))
    samples = noise + signal
    power   = 20 * np.log10(np.abs(samples) + 1e-10)

    return {
        "round":            round_num,
        "sdr_id":           sdr_id,
        "source_type":      "SIMULATED",
        "frequency_mhz":    f"{frequency / 1e6:.1f}",
        "avg_strength_db":  f"{float(np.mean(power)):.2f}",
        "peak_strength_db": f"{float(np.max(power)):.2f}",
        "signal_level":     classify_signal(np.max(power)),
        "timestamp":        format_elapsed(start_time)
    }

# ─────────────────────────────────────────────
#  REAL SDR READING
# ─────────────────────────────────────────────

def read_real_sdr(sdr_obj, sdr_id, frequency, round_num, start_time):
    
    try:
        samples = sdr_obj.rx()
        power   = 20 * np.log10(np.abs(samples) + 1e-10)

        return {
            "round":            round_num,
            "sdr_id":           sdr_id,
            "source_type":      "REAL",
            "frequency_mhz":    f"{frequency / 1e6:.1f}",
            "avg_strength_db":  f"{float(np.mean(power)):.2f}",
            "peak_strength_db": f"{float(np.max(power)):.2f}",
            "signal_level":     classify_signal(np.max(power)),
            "timestamp":        format_elapsed(start_time)
        }
    except Exception as e:
        
        print(f"  Warning: Error reading SDR {sdr_id}: {e} — using simulated.")
        return simulate_sdr_reading(sdr_id, frequency, round_num, start_time)

# ─────────────────────────────────────────────
#  CONNECT TO REAL SDRs
# ─────────────────────────────────────────────

def connect_sdrs(configs):
    try:
        import adi
    except ImportError:
        print("Warning: 'adi' library not found. All SDRs will simulate.")
        return {}

    connections = {}
    for cfg in configs:
        if cfg["simulated"]:
            print(f"  [SDR_{cfg['sdr_id']}] Simulated — skipping connection.")
            continue

        print(f"  [SDR_{cfg['sdr_id']}] Connecting to {cfg['ip']}...")
        try:
            sdr = adi.Pluto(cfg["ip"])
            sdr.sample_rate           = int(SAMPLE_RATE)
            sdr.rx_rf_bandwidth       = int(SAMPLE_RATE)
            sdr.rx_lo                 = int(cfg["frequency"])
            sdr.rx_hardwaregain_chan0 = GAIN
            sdr.rx_buffer_size        = BUFFER_SIZE

            connections[cfg["sdr_id"]] = sdr
            print(f"  [SDR_{cfg['sdr_id']}] Connected! Tuned to {cfg['frequency']/1e6:.1f} MHz")
        except Exception as e:
            print(f"  [SDR_{cfg['sdr_id']}] Connection failed: {e} — falling back to simulated.")

    return connections

# ─────────────────────────────────────────────
#  PRINT ONE READING
# ─────────────────────────────────────────────

def print_reading(r):
    print(f"  Round {r['round']} | SDR {r['sdr_id']} ({r['source_type']})")
    print(f"  Frequency     : {r['frequency_mhz']} MHz")
    print(f"  Avg Strength  : {r['avg_strength_db']} dB")
    print(f"  Peak Strength : {r['peak_strength_db']} dB")
    print(f"  Signal Level  : {r['signal_level']}")
    print(f"  Timestamp     : {r['timestamp']}")
    print()

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  RF Multi-SDR Capture System")
    print("  Senior Design — Signal Detection Module")
    print("  Press Ctrl+C to stop capturing")
    print("=" * 55)
    print()

    print("Connecting to SDRs...")
    sdr_connections = connect_sdrs(SDR_CONFIG)
    print()

    csv_fields = ["round", "sdr_id", "source_type", "frequency_mhz",
                  "avg_strength_db", "peak_strength_db", "signal_level", "timestamp"]


    csv_file = open(OUTPUT_CSV, "w", newline="")
    writer   = csv.DictWriter(csv_file, fieldnames=csv_fields)
    writer.writeheader()

    print(f"Logging to: {OUTPUT_CSV}")
    print()

    start_time = time.time()
    round_num  = 0

    try:
        while True:
            round_num += 1
            print(f"━━━  Round {round_num}  {'━' * 40}")

            for cfg in SDR_CONFIG:
                sid  = cfg["sdr_id"]
                freq = cfg["frequency"]

                
                if not cfg["simulated"] and sid in sdr_connections:
                    reading = read_real_sdr(sdr_connections[sid], sid, freq, round_num, start_time)
                else:
                    reading = simulate_sdr_reading(sid, freq, round_num, start_time)

                if reading:
                    print_reading(reading)
                    writer.writerow(reading)

                time.sleep(DELAY_BETWEEN)

            csv_file.flush()  

            
            if NUM_ROUNDS > 0 and round_num >= NUM_ROUNDS:
                break

    except KeyboardInterrupt:
        print("\nCapture stopped by user.")

    finally:
        csv_file.close()
        print(f"\nDone. {round_num} rounds captured. Data saved to '{OUTPUT_CSV}'.")

if __name__ == "__main__":
    main()
