import pandas as pd

from engine_coolant import add_noise_for_engine_coolant_temperature

df_orig = pd.read_csv("../sample_data/drive1.csv")

# Add anomalies to the "COOLANT TEMPERATURE" column
df = df_orig.copy()
df = add_noise_for_engine_coolant_temperature(df, snr_db=18, alpha=1.0, random_state=42)

# Save the modified DataFrame to a new CSV file
df.to_csv("../sample_data/drive1_noisy.csv", index=False)

# reverse order of rows by only in the COOLANT TEMPERATURE column
df_reversed = df_orig.copy()
df_reversed["COOLANT TEMPERATURE"] = df_reversed["COOLANT TEMPERATURE"].iloc[::-1].values

# Save the modified DataFrame to a new CSV file
df_reversed.to_csv("../sample_data/drive1_reversed.csv", index=False)

df_catalytic = df_orig.copy()

# Add anomalies to the "CATALYST TEMPERATURE" column
df_catalytic["CATALYST TEMPERATURE BANK1 SENSOR2"] = df_catalytic["CATALYST TEMPERATURE BANK1 SENSOR1"].apply(lambda x: x * 1.1)

# Save the modified DataFrame to a new CSV file
df_catalytic.to_csv("../sample_data/drive1_catalytic_anomalous.csv", index=False)
