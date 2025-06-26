
import csv
import os
from datetime import datetime

class ViolationLogger:
    def __init__(self):
        self.entries = []

    def collect(self, subsystem_name, time, violations):
        for entry in violations:
            self.entries.append({
                "time": round(float(time), 2),
                "subsystem": subsystem_name,
                "contract_id": entry.get("contract_id"),
                "message": entry.get("message")
            })

    def save(self, directory="logs"):
        if not os.path.exists(directory):
            os.makedirs(directory)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(directory, f"violations_log_{timestamp}.csv")
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["time", "subsystem", "contract_id", "message"])
            writer.writeheader()
            writer.writerows(self.entries)
        return filepath
