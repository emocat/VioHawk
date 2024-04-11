import glob
import sys
def get_best(path, best_actual,rep):
    for file in glob.glob(path):
        file_reader = open(file, 'r')
        data = file_reader.read()
        data_parts = data.split('\n')
        data_part = data_parts[rep]
        if len(data_part) == 0:
            continue
        sub_data_parts = data_part.split('#')
        actual = sub_data_parts[0].split('],')[1]
        actual_parts = actual.split(',')
        for actual_part_index in range(len(actual_parts)):
            if float(actual_parts[actual_part_index]) > 1:
                actual_parts[actual_part_index] = 1
            if float(actual_parts[actual_part_index]) < best_actual[actual_part_index]:
                if float(actual_parts[actual_part_index]) < 0:
                    best_actual[actual_part_index] = 0
                else:
                    best_actual[actual_part_index] = float(actual_parts[actual_part_index])
    return best_actual

def handle_data(folder_path, file_writer):
        for rep in range(20):
            best_actual = [10, 10, 10, 10, 10, 10]
            for objective in range(6):
                objective_file = "*objective_" + str(objective) + "*.log"
                best_actual = get_best(folder_path+objective_file,best_actual,rep)
            file_writer.write(str(1 - sum(best_actual) / 6) + ",")
        file_writer.write("\n")


if __name__ == "__main__":
    main_path = "Sample_data/RQ1/"
    folder_names = ["RBF_HDBScan"]
    # folder_names =
    file_writer = open ("output-RQ1.txt","w")
    for folder in folder_names:
        folder_path = main_path + folder+"/"
        if folder == "RBF_HDBScan":
            file_writer.write("$RF_{cl}$,")
            handle_data(folder_path, file_writer)
