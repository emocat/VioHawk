import os


# to extact fitness values
def get_values(fv):
    file_name = 'Results/'+str(fv)
    file_handler = open(file_name, "r")
    DfC_min = 1
    DfV_min = 1
    DfP_min = 1
    DfM_min = 1
    DT_max = -1
    traffic_lights_max = 1
    first = True
    distance_Max = -1
    file_name_ex = file_name+'_ex.log'

    if os.path.exists(file_name_ex):
        file_handler_ex = open(file_name_ex, "r")
        for line_ex in file_handler_ex: #using sensors to get the data
            if "red_light" in line_ex:
                print("Red_light invasion")
                traffic_lights_max = 0
            if "lane" in line_ex:
                print("lane invasion")
                DfC_min = 0
            if "vehicle" in line_ex:
                print("vehicle collision")
                DfV_min = 0

    for line in file_handler:
        line_parts = line.split('>')
        clean_line_parts = line_parts[1].replace('DfC:','').replace('DfV:','').replace('DfP:','').replace('DfM:','').replace('DT:','')
        double_parts= clean_line_parts.split(',')
        DfC = float(double_parts[0])
        DfV = float(double_parts[1])
        DfP = float(double_parts[2])
        DfM = float(double_parts[3])
        DT  = float(double_parts[4])

        if DT < 0:
            DT_max = 1
            break

        if first:
            first = False
            distance_Max = DT

        DfC = 1 - (DfC / 1.15) #normalising
        if DfV > 1:
            DfV = 1
        if DfP > 1:
            DfP = 1
        if DfM > 1:
            DfM = 1

        distance_travelled = distance_Max - DT
        normalised_distance_travelled = distance_travelled/distance_Max
        if DfC < DfC_min:
            DfC_min = DfC
        if DfV < DfV_min:
            DfV_min = DfV
        if DfM < DfM_min:
            DfM_min = DfM
        if DfP < DfP_min:
            DfP_min = DfP
        if normalised_distance_travelled > DT_max:
            DT_max = normalised_distance_travelled




    return  DfC_min, DfV_min, DfP_min, DfM_min, DT_max, traffic_lights_max

