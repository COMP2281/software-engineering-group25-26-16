import sklearn as sk
import pandas as pd

UPLOADED_FOLDER = "../uploaded_data"

def windowing(df, n=5):
    # window each feature
    for col in df.columns:
        df[f"{col} MEAN"] = df[col].rolling(window=n).mean()
        df[f"{col} STD"] = df[col].rolling(window=n).std()
        df[f"{col} MIN"] = df[col].rolling(window=n).min()
        df[f"{col} MAX"] = df[col].rolling(window=n).max()

def feature_selection(df):
    cols = ["ENGINE LOAD", "ENGINE RPM", "LONG TERM FUEL TRIM BANK 1", "FUEL TANK", "INTAKE MANIFOLD PRESSURE", "CATALYST TEMPERATURE BANK1 SENSOR1", "CATALYST TEMPERATURE BANK1 SENSOR2", "COOLANT TEMPERATURE", "COOLANT TEMPERATURE STD"]
    return df[cols]

def clean_data(df, n=5) -> pd.DataFrame:
    # add standard deviation of coolant temperature as a feature
    std_temp = df["COOLANT TEMPERATURE"].rolling(n).std()

    # normalise between 0 and 1
    std_temp_min = std_temp.min()
    std_temp_max = std_temp.max()
    df["COOLANT TEMPERATURE STD"] = (std_temp - std_temp_min) / (std_temp_max - std_temp_min)

    # perform feature extraction
    #windowing(df, n=5)

    # perform feature selection
    feature_selection(df)

    # save to file
    path = "cleaned_drive1.csv"
    df.to_csv(path, index=False)

    return df



def load_data_frame(path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=False)

if __name__ == "__main__":
    df = load_data_frame(f"../sample_data/drive1.csv")
    print(clean_data(df))
