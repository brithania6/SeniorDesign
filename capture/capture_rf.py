import numpy as np
import time
import csv
import os

# ============================================================
#                 RF MULTI-SDR CONFIGURATION
# ============================================================

# Name of this experiment
TEST_NAME = "Indoor_Test_01"

# Folder and output file
DATA_FOLDER = "data"
OUTPUT_CSV = os.path.join(DATA_FOLDER, "rf_capture_log.csv")

# SDR Receiver Configuration
SDR_CONFIG = [

    {
        "sdr_id": 1,
        "name": "SDR 1",
        "ip": "ip:192.168.2.1",
        "frequency": 5.8e9,
        "antenna": "Vivaldi",
        "role": "Receiver",
        "simulated": False
    },

    {
        "sdr_id": 2,
        "name": "SDR 2",
        "ip": "ip:192.168.3.1",
        "frequency": 5.8e9,
        "antenna": "Vivaldi",
        "role": "Receiver",
        "simulated": False
    },

    {
        "sdr_id": 3,
        "name": "SDR 3",
        "ip": "ip:192.168.4.1",
        "frequency": 2.4e9,
        "antenna": "Patch Array",
        "role": "Receiver",
        "simulated": False
    },

    {
        "sdr_id": 4,
        "name": "SDR 4",
        "ip": "ip:192.168.5.1",
        "frequency": 2.4e9,
        "antenna": "Patch Array",
        "role": "Receiver",
        "simulated": False
    }

]

# ============================================================
#               CAPTURE PARAMETERS
# ============================================================

SAMPLE_RATE = int(2e6)

RX_BANDWIDTH = SAMPLE_RATE

GAIN = 60

BUFFER_SIZE = 4096

DELAY_BETWEEN = 0.5

NUM_ROUNDS = 0      

os.makedirs(DATA_FOLDER, exist_ok=True)

# ============================================================
#           SIGNAL STRENGTH CLASSIFIER
# ============================================================

def classify_signal(peak_db):

    if peak_db >= 60:
        return "VERY STRONG"

    elif peak_db >= 45:
        return "STRONG"

    elif peak_db >= 30:
        return "MODERATE"

    elif peak_db >= 15:
        return "WEAK"

    else:
        return "VERY WEAK"

# ============================================================
#             ELAPSED TIME FORMATTER
#               Format: HH:MM:SS.mmm
# ============================================================

def format_elapsed(start_time):
    
    elapsed = time.time() - start_time

    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = elapsed % 60

    return f"{hours:02}:{minutes:02}:{seconds:06.3f}"

# ============================================================
#              REAL SDR READING
# ============================================================

def read_real_sdr(sdr_obj, cfg, round_num, start_time):
   
    try:

        samples = sdr_obj.rx()

        power = 20 * np.log10(np.abs(samples) + 1e-10)

        avg_db = float(np.mean(power))
        peak_db = float(np.max(power))

        return {

            "round": round_num,

            "sdr_id": cfg["sdr_id"],

            "ip": cfg["ip"],

            "role": cfg["role"],

            "antenna": cfg["antenna"],

            "source_type": "REAL",

            "connection": "CONNECTED",

            "frequency_mhz": f"{cfg['frequency']/1e6:.1f}",

            "avg_strength_db": f"{avg_db:.2f}",

            "peak_strength_db": f"{peak_db:.2f}",

            "signal_level": classify_signal(peak_db),

            "timestamp": format_elapsed(start_time)

        }

    except Exception as e:

        print(f"\nERROR reading SDR {cfg['sdr_id']}")
        print(e)

        return None

# ============================================================
#           CONNECT TO REAL PLUTO SDRs
# ============================================================

def connect_sdrs(configs):

    try:
        import adi
    except ImportError:
        print("\nERROR: pyadi-iio is not installed.")
        return {}

    connections = {}

    print("\nSearching for PlutoSDRs...\n")

    for cfg in configs:

        
        if cfg["role"] != "RECEIVER":
            continue

        print(f"Connecting to SDR {cfg['sdr_id']} ({cfg['ip']})...")

        try:

            sdr = adi.Pluto(cfg["ip"])

            
            sdr.sample_rate = int(SAMPLE_RATE)
            sdr.rx_rf_bandwidth = int(SAMPLE_RATE)
            sdr.rx_lo = int(cfg["frequency"])
            sdr.rx_hardwaregain_chan0 = GAIN
            sdr.rx_buffer_size = BUFFER_SIZE

            connections[cfg["sdr_id"]] = sdr

            print(f"✓ SDR {cfg['sdr_id']} Connected")
            print(f"   Frequency : {cfg['frequency']/1e9:.1f} GHz")
            print(f"   Antenna   : {cfg['antenna']}")
            print(f"   Gain      : {GAIN} dB\n")

        except Exception as e:

            print(f"✗ SDR {cfg['sdr_id']} Connection Failed")
            print(f"   {e}\n")

    print(f"Successfully connected to {len(connections)} receiver(s).\n")

    return connections
# ============================================================
#               DISPLAY SDR READING
# ============================================================

def print_reading(reading):

    print("=" * 60)
    print(f"Round        : {reading['round']}")
    print(f"SDR ID       : {reading['sdr_id']}")
    print(f"IP Address   : {reading['ip']}")
    print(f"Role         : {reading['role']}")
    print(f"Antenna      : {reading['antenna']}")
    print(f"Connection   : {reading['connection']}")
    print(f"Source Type  : {reading['source_type']}")
    print(f"Frequency    : {reading['frequency_mhz']} MHz")
    print(f"Average dB   : {reading['avg_strength_db']} dB")
    print(f"Peak dB      : {reading['peak_strength_db']} dB")
    print(f"Signal Level : {reading['signal_level']}")
    print(f"Timestamp    : {reading['timestamp']}")
    print("=" * 60)
    print()
# ============================================================
#                        MAIN PROGRAM
# ============================================================

def main():

    print("=" * 65)
    print("        RF Multi-SDR Capture System")
    print("        Senior Design Project")
    print("=" * 65)

    print(f"\nSample Rate : {SAMPLE_RATE/1e6:.1f} MSPS")
    print(f"Gain        : {GAIN} dB")
    print(f"Buffer Size : {BUFFER_SIZE}")
    print(f"Output File : {OUTPUT_CSV}")

    print("\nConnecting to PlutoSDRs...")

    sdr_connections = connect_sdrs(SDR_CONFIG)

    if len(sdr_connections) == 0:
        print("\nERROR: No SDRs were connected.")
        print("Program terminated.")
        return

    print("\nAll available SDRs are ready.\n")

    csv_fields = [
        "round",
        "sdr_id",
        "ip",
        "role",
        "antenna",
        "connection",
        "source_type",
        "frequency_mhz",
        "avg_strength_db",
        "peak_strength_db",
        "signal_level",
        "timestamp"
    ]

    csv_file = open(OUTPUT_CSV, "w", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
    writer.writeheader()

    print(f"Logging data to {OUTPUT_CSV}")
    print("\nPress Ctrl+C to stop.\n")

    start_time = time.time()
    round_num = 0

    try:

        while True:

            round_num += 1

            print(f"\n{'='*25} ROUND {round_num} {'='*25}\n")

            for cfg in SDR_CONFIG:

                sid = cfg["sdr_id"]

               
                if cfg["role"] != "RECEIVER":
                    continue

           
                if sid not in sdr_connections:
                    print(f"Skipping SDR {sid} (Not Connected)")
                    continue

                reading = read_real_sdr(
                    sdr_connections[sid],
                    cfg,
                    round_num,
                    start_time
                )

                if reading is not None:

                    print_reading(reading)

                    writer.writerow(reading)

            csv_file.flush()

            if NUM_ROUNDS > 0 and round_num >= NUM_ROUNDS:
                break

            time.sleep(DELAY_BETWEEN)

    except KeyboardInterrupt:

        print("\nCapture stopped by user.")

    finally:

        csv_file.close()

        print("\nCapture Complete")
        print(f"Rounds Captured : {round_num}")
        print(f"CSV Saved To    : {OUTPUT_CSV}")
