from . import engine_coolant, catalytic
from .base_warning import BaseWarning

UPLOADED_FOLDER = "../uploaded_data"

"""
This is a conglomeration of all the anomaly detection models
"""
class AnomalyDetectionModel():
    # this will train the models to detect anomalies
    # currently only supports fuel tank and engine coolant sensor warnings,
    # will be expanded for other things soon!
    def __init__(self, data_path: str):
        self.engine_coolant = engine_coolant.EngineCoolantClassifier(data_path)
        self.catalytic = catalytic.CatalyticClassifier()

    def generate_warnings(self, filepath) -> list[BaseWarning]:
        warnings = []
        warnings.extend(self.engine_coolant.generate_warnings(filepath))
        warnings.extend(self.catalytic.generate_warnings(filepath))
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
