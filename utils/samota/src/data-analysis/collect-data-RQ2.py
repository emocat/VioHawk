import glob
import sys


def get_data(folder_names,file_name):
    file_writer = open(file_name, 'w')

    for folder in folder_names:

        list_of_all_files = (glob.glob("Sample_data/RQ2/"+folder + "/*.log"))
        file_writer.write(folder + ",")
        for file in list_of_all_files:
            count = 0
            file_reader = open(file, "r")
            file_contents = file_reader.read()
            file_contents_parts = file_contents.split('\n')
            DfC_min_boolean = False;
            DfV_min_boolean = False;
            DfP_min_boolean = False;
            DfM_min_boolean = False;
            DT_max_boolean = False;
            traffic_lights_max_boolean = False;
            for part in file_contents_parts:
                if part.__contains__("]:"):
                    part_without_date = part.split("[")[1]
                    feature_values = part_without_date.split("]:")[0]
                    fitness_values = part_without_date.split("]:")[1]
                    fitness_values_parts = fitness_values.split(",")
                    DfC_min = float(fitness_values_parts[0])
                    DfV_min = float(fitness_values_parts[1])
                    DfP_min = float(fitness_values_parts[2])
                    DfM_min = float(fitness_values_parts[3])
                    DT_max = float(fitness_values_parts[4])
                    traffic_lights_max = float(fitness_values_parts[5])
                    if not DfC_min_boolean:
                        if DfC_min <= 0:
                            count = count + 1
                            DfC_min_boolean = True
                    if not DfV_min_boolean:
                        if DfV_min <= 0:
                            count = count + 1
                            DfV_min_boolean = True
                    if not DfP_min_boolean:
                        if DfP_min <= 0:
                            count = count + 1
                            DfP_min_boolean = True
                    if not DfM_min_boolean:
                        if DfM_min <= 0:
                            count = count + 1
                            DfM_min_boolean = True
                    if not DT_max_boolean:
                        if DT_max <= 0.95:
                            count = count + 1
                            DT_max_boolean = True
                    if not traffic_lights_max_boolean:
                        if traffic_lights_max <= 0:
                            count = count + 1
                            traffic_lights_max_boolean = True
            file_writer.write(str(float(count)/6) + ",")
        file_writer.write("\n")
    print("File is saved with name: "+file_name)
if __name__ == "__main__":
    folder_names = ["SAMOTA-I"]
    get_data(folder_names,"output-RQ2.txt")


