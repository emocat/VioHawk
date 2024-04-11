
#spawn points for different types of roads
def get_road(fv, file_contents):
    no_of_signals = 0
    if fv[0] == 0:  # straight Road
        if fv[1] == 0:  # Road ID
            file_contents = file_contents + "--simulator_town=1"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=29"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=31"
                file_contents = file_contents + "\n--goal_location=182.202, 330.639991, 0.300000"
            elif (fv[2] == 1):
                file_contents = file_contents + "\n--simulator_spawn_point_index=31"
                file_contents = file_contents + "\n--goal_location=234.0, 330.639991, 0.300000"
            elif (fv[2] == 2):
                file_contents = file_contents + "\n--simulator_spawn_point_index=31"
                file_contents = file_contents + "\n--goal_location=284.0, 330.639991, 0.300000"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=35"
        
        if fv[1] == 1:  # Road ID
            file_contents = file_contents + "--simulator_town=1"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=163"
                file_contents = file_contents + "\n--goal_location=396.310547, 190.713867, 0.300000"
            elif (fv[2] == 1):
                file_contents = file_contents + "\n--simulator_spawn_point_index=64"
                file_contents = file_contents + "\n--goal_location=395.959991,204.169998, 0.300000"
            elif (fv[2] == 2):
                file_contents = file_contents + "\n--simulator_spawn_point_index=64"
                file_contents = file_contents + "\n--goal_location=395.959991,254.169998, 0.300000"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=65"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=130"
        if fv[1] == 2:  # Road ID
            file_contents = file_contents + "--simulator_town=3"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=227"
                file_contents = file_contents + "\n--goal_location=245.583176, 1.595174, 0.300000"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=117"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=216"
            file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=119"
        if fv[1] == 3:  # Road ID
            file_contents = file_contents + "--simulator_town=3"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=1"
                file_contents = file_contents + "\n--goal_location=126.690155, 8.264045, 0.275307"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=147"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=104"
            file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=148"
        
    if fv[0] == 1:  # left turn Road
        if fv[1] == 0:
            file_contents = file_contents + "--simulator_town=1"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=125"
                file_contents = file_contents + "\n--goal_location=396.349457, 300.406677, 0.300000"
            if (fv[2] == 1):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=125"
                file_contents = file_contents + "\n--goal_location=396.449991, 230.409991, 0.300000"

            if (fv[2] == 2):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=125"
                file_contents = file_contents + "\n--goal_location=396.449991, 180.409991, 0.300000"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=47"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=126"
        
        if fv[1] == 1:
            file_contents = file_contents + "--simulator_town=1"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=108"
                file_contents = file_contents + "\n--goal_location=22.179979, 330.459991, 0.300000"
            if (fv[2] == 1):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=108"
                file_contents = file_contents + "\n--goal_location=22.179979, 380.459991, 0.300000"

            if (fv[2] == 2):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=108"
                file_contents = file_contents + "\n--goal_location=22.179979, 330.459991, 0.300000"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=123"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=54"
        if fv[1] == 2:
            no_of_signals = 1
            file_contents = file_contents + "--simulator_town=3"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=71"
                file_contents = file_contents + "\n--goal_location=-84.70,-158.58,0.275307"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=130"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=50"
            file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=133"
        if fv[1] == 3:
            no_of_signals = 1
            file_contents = file_contents + "--simulator_town=3"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=70"
                file_contents = file_contents + "\n--goal_location=-88.20,-158.58,0.275307"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=133"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=50"
            file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=130"
        
    if fv[0] == 2:  # right turn Road
        
        if fv[1] == 0:
            file_contents = file_contents + "--simulator_town=1"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=187"
                file_contents = file_contents + "\n--goal_location=392.470001, 19.920038, 0.300000"
            if (fv[2] == 1):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=187"
                file_contents = file_contents + "\n--goal_location=392.470001, 59.920038, 0.300000"
            if (fv[2] == 2):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=187"
                file_contents = file_contents + "\n--goal_location=392.470001, 109.920038, 0.300000"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=181"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=184"  # check me
        if fv[1] == 1:
            file_contents = file_contents + "--simulator_town=1"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=57"
                file_contents = file_contents + "\n--goal_location=2.009914, 295.863309, 0.300000"
            if (fv[2] == 1):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=57"
                file_contents = file_contents + "\n--goal_location=55.009914, 295.863309, 0.300000"
            if (fv[2] == 2):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=57"
                file_contents = file_contents + "\n--goal_location=108.009914, 295.863309, 0.300000"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=67"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=108"
        
        if fv[1] == 2:
            file_contents = file_contents + "--simulator_town=5"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=244"
                file_contents = file_contents + "\n--goal_location=-230.40, -84.75, 0.300000"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=301"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=282"
            file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=293"
        if fv[1] == 3:
            file_contents = file_contents + "--simulator_town=3"
            if (fv[2] == 0):  # road length
                file_contents = file_contents + "\n--simulator_spawn_point_index=57"
                file_contents = file_contents + "\n--goal_location=-36.630997, -194.923615, 0.275307"
            file_contents = file_contents + "\n--vehicle_in_front_spawn_point=127"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=264"
            file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=128"
   
    if fv[0] == 3:  # road id
      
        if fv[1] == 0:
            no_of_signals = 1
            file_contents = file_contents + "--simulator_town=5"
            if fv[15] == 0:  # Follow Road
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=-220.048904, -3.915073, 0.300000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=137"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=59"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=60"
            if fv[15] == 1:  # 1st exit
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=-184.585892, -53.541496, 0.600000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=137"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=59"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=60"
            if fv[15] == 2:  # 2nd exit
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=-191.561127, 36.201321, 0.600000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=138"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=60"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=59"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=127"
        # -----
        if fv[1] == 1:
            no_of_signals = 1
            file_contents = file_contents + "--simulator_town=5"
            if fv[15] == 0:  # Follow Road
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=-188.079239, -29.370184, 0.600000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=38"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=34"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=33"

            if fv[15] == 1:  # 1st exit
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=-159.701355, 6.438059, 0.300000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=37"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=33"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=34"
            if fv[15] == 2:  # 2nd exit
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=-220.040390, -0.415084, 0.600000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=38"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=34"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=33"
            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=131"
       
        if fv[1] == 2:
            no_of_signals = 1
            file_contents = file_contents + "--simulator_town=5"
            if fv[15] == 0:  # Follow Road
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=-44.200703, -41.710579, 0.450000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=44"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=275"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=274"
            if fv[15] == 1:  # 1st exit
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=0.556072, 6.047980, 0.300000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=44"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=275"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=274"
            if fv[15] == 2:  # 2nd exit
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=-81.402634, -0.752534, 0.300000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=43"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=274"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=275"

            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=206"
        if fv[1] == 3:
            no_of_signals = 1
            file_contents = file_contents + "--simulator_town=5"
            if fv[15] == 0:  # Follow Road
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=24.741877, -52.334110, 0.300000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=75"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=77"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=78"
            if fv[15] == 1:  # 1st exit
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=1.051966, -94.892189, 0.300000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=75"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=77"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=78"
            if fv[15] == 2:  # 2nd exit
                if (fv[2] == 0):  # road length
                    file_contents = file_contents + "\n--goal_location=52.13, -87.77, 0.300000"
                file_contents = file_contents + "\n--simulator_spawn_point_index=76"
                file_contents = file_contents + "\n--vehicle_in_front_spawn_point=78"
                file_contents = file_contents + "\n--vehicle_in_adjacent_spawn_point=77"

            file_contents = file_contents + "\n--vehicle_in_opposite_spawn_point=218"
    

    return file_contents
