import sys


from carla import Transform,Location

source_flags=None;
self_debug=0
import logging
logger = logging.getLogger()
from datetime import datetime
class FitnessExtractor:

    ego_vehicle_location=None;
    start_loc= None
    first= True;
    i = 0
    first_dist_negative = True
    def get_distance_from_center_lane(self,ego_vehicle, world):
        ego_vehicle_location = ego_vehicle.get_location()

        waypoint = world.get_map().get_waypoint(ego_vehicle_location, project_to_road=True)

        ego_vehicle_loc = Location(x=ego_vehicle_location.x, y=ego_vehicle_location.y, z=0.0)
        if self_debug==1:
            print("Distance From center of Lane: " + str(ego_vehicle_loc.distance(waypoint.transform.location)))
        return ego_vehicle_loc.distance(waypoint.transform.location)

    def get_min_distance_from_other_vehicle(self,ego_vehicle, world,vehicle_infront):
        if vehicle_infront == 0 :
            return 1000
        ego_vehicle_location = ego_vehicle.get_location()

        distances = [1000]
        target_vehicle=world.get_actor(vehicle_infront)
        # for target_vehicle in world.get_actors().filter('vehicle.*'):
        #     if target_vehicle.id == ego_vehicle.id:
        #         continue
        #     target_vehicle_waypoint = world.get_map().get_waypoint(target_vehicle.get_location())
        #     if target_vehicle_waypoint.road_id != ego_vehicle_waypoint.road_id or \
        #             target_vehicle_waypoint.lane_id != ego_vehicle_waypoint.lane_id:
        #         continue
        distance = ego_vehicle_location.distance(target_vehicle.get_location())
        distances.append(distance)
        if self_debug == 1:
            print("Minimum Distance from other Vehicle: " + str(min(distances)))
        return min(distances) - 3.32 # substracting distances from center of vehicle

    def get_min_distance_from_pedestrians(self, ego_vehicle, world):
        distances = [1000]
        ego_vehicle_location = ego_vehicle.get_location()

        for target_vehicle in world.get_actors().filter('walker.*'):
            distance = ego_vehicle_location.distance(target_vehicle.get_location())
            distances.append(distance)
        if self_debug == 1:
            print("Minimum Distance from Pedestrians: " + str(min(distances)))
        return (min(distances)) -1.2  # substracting distances from center of vehicle

    def get_min_distance_from_static_mesh(self, ego_vehicle, world):
        distances = [1000]
        ego_vehicle_location = ego_vehicle.get_location()
        # for actor in world.get_actors():
        #     print(actor)
        for target_vehicle in world.get_actors().filter('static.*'):
            distance = ego_vehicle_location.distance(target_vehicle.get_location())
            distances.append(distance)

        for target_vehicle in world.get_actors().filter('traffic.*.*'):
            distance = ego_vehicle_location.distance(target_vehicle.get_location())
            distances.append(distance)
        for target_vehicle in world.get_actors().filter('traffic.*'):
            distance = ego_vehicle_location.distance(target_vehicle.get_location())
            distances.append(distance)
        if self_debug == 1:
            print("Minimum Distance from static Mesh: " + str(min(distances)))
        return (min(distances))  # substracting distances from center of vehicle

    def get_distance_from_destination(self, ego_vehicle, flags):
        ego_vehicle_location = ego_vehicle.get_location()
        if (self.first):
            import os
            if os.path.exists(flags.log_fil_name):
                os.remove(flags.log_fil_name)
            self.first=False
            self.start_loc = ego_vehicle_location

            logger = logging.getLogger()
            logger.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s | %(message)s',
                                          '%m-%d-%Y %H:%M:%S')

            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(logging.DEBUG)
            stdout_handler.setFormatter(formatter)

            file_handler = logging.FileHandler(flags.log_fil_name)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            # logger.addHandler(stdout_handler)




        #
        self.final_destination = Location(x=float(flags.goal_location[0]), y=float(flags.goal_location[1]),
                                          z=float(flags.goal_location[2]))
        # dist = ego_vehicle_location.distance(self.start_loc);
        dist = ego_vehicle_location.distance(self.final_destination)-10.8; #9.8 for v1
        if self_debug == 1:
            print("Distance from Final Destination: " + str(dist))

        return dist
    def extract_from_world(self,ego_vehicle, world,flags,vehicle_infront):
        source_flags = flags


        dist_center_lane = self.get_distance_from_center_lane( ego_vehicle, world)
        dist_min_other_vehicle = self.get_min_distance_from_other_vehicle(ego_vehicle,world,vehicle_infront)
        dist_min_pedestrian= self.get_min_distance_from_pedestrians(ego_vehicle,world)
        dist_min_mesh=self.get_min_distance_from_static_mesh(ego_vehicle,world)
        dist_from_final_destnation=self.get_distance_from_destination(ego_vehicle,flags)

        to_log = str(ego_vehicle.get_location())+">DfC:" + str("{:.4f}".format(dist_center_lane)) + ",DfV:" + str("{:.2f}".format(dist_min_other_vehicle))+",DfP:" + str("{:.2f}".format(dist_min_pedestrian)) + ",DfM:" + str("{:.2f}".format(dist_min_mesh)) + ",DT:" + str("{:.2f}".format(dist_from_final_destnation))
        if dist_from_final_destnation <0 : #to avoid logging while system is being shutdown
             if self.first_dist_negative == True:
                self.first_dist_negative = False
                logging.info(to_log)
        if dist_from_final_destnation >= 0:
            logging.info(to_log)
        # logging.info("DfV:" + str(dist_min_other_vehicle))
        # logging.info("DfP:" + str(dist_min_pedestrian))
        # logging.info("DfM:" + str(dist_min_mesh))
        # logging.info("DfG:" + str(dist_from_final_destnation))



