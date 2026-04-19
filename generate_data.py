import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# --- CONFIG ---
start_date = datetime(2023, 1, 1)
end_date   = datetime(2024, 12, 31)

production_lines = ["Ligne A", "Ligne B", "Ligne C", "Ligne D"]
machines = {
    "Ligne A": ["Machine A1", "Machine A2", "Machine A3"],
    "Ligne B": ["Machine B1", "Machine B2"],
    "Ligne C": ["Machine C1", "Machine C2", "Machine C3"],
    "Ligne D": ["Machine D1", "Machine D2"],
}
products = ["Engrais DAP", "Engrais MAP", "Acide Phosphorique", "Phosphate Brut"]
defect_types = [
    "Contamination",
    "Sous-dosage",
    "Surdosage",
    "Granulométrie incorrecte",
    "Humidité excessive",
    "Emballage défectueux",
]
shifts = ["Matin", "Après-midi", "Nuit"]
operators = [f"OP{str(i).zfill(3)}" for i in range(1, 21)]

# --- GÉNÉRATION ---
records = []
current_date = start_date

while current_date <= end_date:
    for line in production_lines:
        for shift in shifts:
            # Unités produites ce shift
            units_produced = np.random.randint(800, 1500)

            # Taux de défaut de base par ligne (Ligne C est la plus problématique)
            base_defect_rate = {
                "Ligne A": 0.03,
                "Ligne B": 0.025,
                "Ligne C": 0.06,
                "Ligne D": 0.02,
            }[line]

            # Augmenter le taux la nuit
            if shift == "Nuit":
                base_defect_rate *= 1.4

            # Nombre de défauts
            num_defects = int(units_produced * base_defect_rate * np.random.uniform(0.7, 1.3))

            for _ in range(num_defects):
                defect = np.random.choice(defect_types, p=[0.30, 0.20, 0.15, 0.15, 0.12, 0.08])
                machine = np.random.choice(machines[line])
                records.append({
                    "Date":            current_date.strftime("%Y-%m-%d"),
                    "Month":           current_date.strftime("%Y-%m"),
                    "Week":            current_date.strftime("%Y-W%U"),
                    "Production Line": line,
                    "Machine":         machine,
                    "Shift":           shift,
                    "Product":         np.random.choice(products),
                    "Defect Type":     defect,
                    "Operator":        np.random.choice(operators),
                    "Units Produced":  units_produced,
                })

    current_date += timedelta(days=1)

df = pd.DataFrame(records)
df.to_csv("quality_control_data.csv", index=False)

print(f"✅ Dataset généré : {len(df):,} défauts")
print(f"Période : {df['Date'].min()} → {df['Date'].max()}")
print(f"\nDéfauts par ligne :\n{df['Production Line'].value_counts()}")
print(f"\nDéfauts par type :\n{df['Defect Type'].value_counts()}")