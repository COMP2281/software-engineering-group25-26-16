import os
import pickle
from pathlib import Path

from anomaly_detection.engine_coolant import EngineCoolantClassifier


try:
    from . import engine_coolant, catalytic, fuel_tank, intake_air_temperature
    from .base_warning import BaseWarning
except:
    import engine_coolant, catalytic, fuel_tank, intake_air_temperature
    from base_warning import BaseWarning

UPLOADED_FOLDER = "../uploaded_data"

"""
This is a conglomeration of all the anomaly detection models.
"""
class AnomalyDetectionModel:
    # this will train the models to detect anomalies
    # currently supports engine coolant, catalytic, and fuel tank warnings
    def __init__(self, data_path: str, models_path: Path | None = None):
        
        # try to load engine coolant classifier from file
        if models_path is not None:
            # try to load from file
            try:
                with open(models_path / "ect_model.pkl", "rb") as f:
                    self.engine_coolant: EngineCoolantClassifier = pickle.load(f)
                print("Loaded ECT anomaly detector model from file")
            except:
                print("Could not ECT anomaly detector model from file")
                # if file could not be loaded

                # train engine coolant classifier from sample data
                self.engine_coolant = engine_coolant.EngineCoolantClassifier(data_path)

                # save to file
                try:
                    with open(models_path / "ect_model.pkl", "wb") as f:
                        pickle.dump(self.engine_coolant, f)
                        print("Saved ECT anomaly detector model to file")
                except:
                    print("Failed to save ECT anomaly detector model to file")
        else:
            # train engine coolant classifier from sample data
            self.engine_coolant = engine_coolant.EngineCoolantClassifier(data_path)

        self.catalytic = catalytic.CatalyticClassifier()
        self.fuel_tank = fuel_tank.FuelTankClassifier()
        self.iat = intake_air_temperature.IntakeAirTemperatureClassifier()

    def generate_warnings(self, filepath) -> list[BaseWarning]:
        fuel_tank_warnings = self.fuel_tank.generate_warnings(filepath)
        engine_coolant_warnings_initial = self.engine_coolant.generate_warnings(filepath)
        catalytic_warnings = self.catalytic.generate_warnings(filepath)
        iat_warnings = self.iat.generate_warnings(filepath)

        # run times that models other than the engine coolant one generated warnings at
        other_run_times = set([w.run_time() for w in fuel_tank_warnings + catalytic_warnings + iat_warnings])

        # remove engine coolant warnings that occur at the same time as other warnings
        engine_coolant_warnings = [w for w in engine_coolant_warnings_initial if w.run_time() not in other_run_times]

        warnings = []
        warnings.extend(fuel_tank_warnings)
        warnings.extend(engine_coolant_warnings)
        warnings.extend(catalytic_warnings)
        warnings.extend(iat_warnings)

        return warnings

# for testing purposes only
# if __name__ == "__main__":
    # model = AnomalyDetectionModel("sample_data/")
    # warnings = model.generate_warnings(f"../sample_data/idle1test.csv")
    # for warning in warnings:
    #     print(warning.to_dict())



# # for testing purposes only
# if __name__ == "__main__":
#     normal_data = []
#     anomalous_data = []
#
#     num_files_idle = 47
#     num_files_drive = 13
#     ratio_anomaly = 0.5
#
#     ratio_test = 0.2
#
#     num_anomalous = int(num_files_idle * ratio_anomaly)
#     windows = load_data_frame(f"../sample_data/idle1.csv")
#
#     # anomalous data (idle)
#     for file in range(1, int(num_files_idle * ratio_anomaly) + 1):
#         anomalous_data.extend(process_file(f"../sample_data/idle{file}.csv", anomalous=True))
#
#     # normal data (idle)
#     for file in range(int(num_files_idle * ratio_anomaly) + 1, num_files_idle + 1):
#         normal_data.extend(process_file(f"../sample_data/idle{file}.csv", anomalous=False))
#
#
#     # anomalous data (drive)
#     for file in range(1, int(num_files_drive * ratio_anomaly) + 1):
#         anomalous_data.extend(process_file(f"../sample_data/drive{file}.csv", anomalous=True))
#
#     # normal data (drive)
#     for file in range(int(num_files_drive * ratio_anomaly) + 1, num_files_drive + 1):
#         normal_data.extend(process_file(f"../sample_data/drive{file}.csv", anomalous=False))
#
#     anomalous_train = anomalous_data[:int(len(anomalous_data) * (1 - ratio_test))]
#     anomalous_test = anomalous_data[int(len(anomalous_data) * (1 - ratio_test)):]
#     normal_train = normal_data[:int(len(normal_data) * (1 - ratio_test))]
#     normal_test = normal_data[int(len(normal_data) * (1 - ratio_test)):]
#
#     # show sizes
#     print(f"Anomalous train samples: {len(anomalous_train)}")
#     print(f"Anomalous test samples: {len(anomalous_test)}")
#     print(f"Normal train samples: {len(normal_train)}")
#     print(f"Normal test samples: {len(normal_test)}")
#
#     knn = train_knn(anomalous_train, normal_train)
#     test_knn(knn, anomalous_test, normal_test)
#
#
