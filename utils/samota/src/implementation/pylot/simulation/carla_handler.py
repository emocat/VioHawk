from carla import  Transform,Location, Rotation, VehicleLightState
import carla
import re
from numpy import random
import sys

class carla_handle():

    ego_location=None;
    map=None;
    flags=[]
    spawn_points=None
    controllers_ai=[]
    client=None
    world= None
    traffic_lights = None
    def turn_off_ai(self):
        for traffic_light in self.traffic_lights:
            traffic_light.set_state(carla.TrafficLightState.Green)
    def turn_lights_red(self):
        for traffic_light in self.traffic_lights:
            traffic_light.set_state(carla.TrafficLightState.Red)

    def turn_lights_yellow(self):
        for traffic_light in self.traffic_lights:
            traffic_light.set_state(carla.TrafficLightState.Yellow)

    def set_weather(self, world, weather: str,night_time):
        from carla import WeatherParameters
        names = [
            name for name in dir(WeatherParameters) if re.match('[A-Z].+', name)
        ]
        weathers = {x: getattr(WeatherParameters, x) for x in names}

        weather_to_set= weathers[weather]
        if night_time == 1:
            weather_to_set.sun_altitude_angle = -90
        world.set_weather(weather_to_set)
        return weathers
    def sp_vehicle(self, client, world,  logger,sp,two_wheeled):
        from carla import command
        spawn_point = self.spawn_points[sp]
        self.client=client

        v_blueprints = world.get_blueprint_library().filter('vehicle.*')
        # Construct a batch message that spawns the vehicles.
        batch = []
        blueprint = None
        if two_wheeled==1:
            for bluep in v_blueprints:
                if bluep.get_attribute('number_of_wheels').as_int() == 2:
                    blueprint = bluep
                    break
        else:
            blueprint = v_blueprints[1]
            # for bluep in v_blueprints:
            #     if not bluep.get_attribute('number_of_wheels').as_int() == 2:
            #         blueprint = bluep
            #         break

        if blueprint.has_attribute('color'):
            color = blueprint.get_attribute('color').recommended_values[0]
            blueprint.set_attribute('color', color)
        blueprint.set_attribute('role_name', 'autopilot')
        batch.append(
            command.SpawnActor(blueprint, spawn_point).then(
                command.SetAutopilot(command.FutureActor, True)))

    # Apply the batch and retrieve the identifiers.
        vehicle_ids = []
        for response in client.apply_batch_sync(batch, True):
            if response.error:
                logger.info(
                    'Received an error while spawning a vehicle: {}'.format(
                        response.error))
            else:
               return response.actor_id

    def handle_traffic_lights(self):

        traffic_lights = self.world.get_actors().filter('traffic.traffic_*');
        self.traffic_lights = traffic_lights

        # for traffic_light in traffic_lights:
        #     # actor.set_state(carla.TrafficLightState.Green)
        #     traffic_light.set_red_time(0.0001)
        #     traffic_light.set_yellow_time(1)
        #     traffic_light.set_green_time(3.5)
        #     print(actor.get_red_time())
        # import sys
        # sys.exit(0)
    def spawn_vehicles(self, client, world, num_vehicles: int, logger,flags):
        """ Spawns vehicles at random locations inside the world.

        Args:
            num_vehicles: The number of vehicles to spawn.
        """
        from carla import command

        # Get the spawn points and ensure that the number of vehicles
        # requested are less than the number of spawn points.
        self.map = world.get_map()
        self.flags=flags
        self.world = world
        vehicle_ids=[]
        vehicle_infront = 0
        self.spawn_points =self.map.get_spawn_points()
        if flags.vehicle_in_front == 1:
            veh_id = self.sp_vehicle(client, world, logger,flags.vehicle_in_front_spawn_point, flags.vehicle_in_front_two_wheeled)
            vehicle_infront = veh_id
            vehicle_ids.append(veh_id)
        if flags.vehicle_in_opposite_lane == 1:
            veh_id = self.sp_vehicle(client, world, logger,flags.vehicle_in_opposite_spawn_point, flags.vehicle_in_opposite_two_wheeled)
            vehicle_ids.append(veh_id)
        if flags.vehicle_in_adjacent_spawn_point > 0:
            if flags.vehicle_in_adjcent_lane == 1:
                veh_id = self.sp_vehicle(client, world, logger,flags.vehicle_in_adjacent_spawn_point, flags.vehicle_in_adjacent_two_wheeled)
                vehicle_ids.append(veh_id)

        v_actors = world.get_actors(vehicle_ids)
        # for v_actor in v_actors:
        #     v_actor.set_target_velocity(carla.Vector3D(8.33, 0, 0))
        #     v_actor.constant_velocity_enabled = True

        if flags.night_time == 1:
             v_actors=world.get_actors(vehicle_ids)
             for v_actor in v_actors:
                 # v_actor.set_light_state(VehicleLightState.Brake)
                 v_actor.set_light_state(VehicleLightState.HighBeam)
        # Get all the possible vehicle blueprints inside the world.

        return vehicle_ids, vehicle_infront
    def get_along_waypoint(self,waypoint):
        waypoint = waypoint.next(10)
        if len(waypoint)>0:
            waypoint = waypoint[0]
            waypoint = self.map.get_waypoint(waypoint.transform.location, lane_type=(carla.LaneType.Sidewalk))
        else:
            return -1
        return waypoint

    def get_locations(self,wp1,people_ids):
        transforms = []
        wp_ego = wp1
        wp_opposite = self.spawn_points[self.flags.vehicle_in_opposite_spawn_point]
        wp_opposite = self.map.get_waypoint(wp_opposite.location, lane_type=(carla.LaneType.Sidewalk))
        for i in range (0,len(people_ids)):
            if i % 2 == 0:
                if wp_ego != -1:
                    wp_ego = self.get_along_waypoint(wp_ego)
                    if wp_ego != -1:
                        loc = Location(wp_ego.transform.location.x, wp_ego.transform.location.y, (wp_ego.transform.location.z + 0.8000))
                        transform = Transform(loc, Rotation(0,-60,0))
                        transforms.append(transform)
            else:
                if wp_opposite != -1:
                    wp_opposite = self.get_along_waypoint(wp_opposite)
                    if wp_opposite != -1:
                        loc = Location(wp_opposite.transform.location.x, wp_opposite.transform.location.y,
                                       (wp_opposite.transform.location.z + 0.8000))
                        transform = Transform(loc, Rotation(0, 60, 0))

                        transforms.append(transform)


        return transforms


    def handle_pedestrian(self,world, people_ids,people_control_ids,client):
        SpawnActor = carla.command.SpawnActor
        people_actors = world.get_actors(people_ids)

        wp1 = self.map.get_waypoint(self.ego_location.location, lane_type=(carla.LaneType.Sidewalk))

        # ego_veh_way_point=self.map.get_waypoint(self.ego_location.location, project_to_road=True)
        ped_controller_bp = world.get_blueprint_library().find(
            'controller.ai.walker')
        print("moving pedestrians to correct location")
        batch=[]
        transforms= self.get_locations(wp1,people_ids);
        for i, ped_control_id in enumerate(people_ids):
            if i < len(transforms):
                people_actors[i].set_transform(transforms[i])
        # for ped_id in people_ids:
        #     batch.append(SpawnActor(ped_controller_bp,Transform(),
        #                                         ped_id))
        # ped_control_ids = []
        # for response in client.apply_batch_sync(batch, True):
        #         ped_control_ids.append(response.actor_id)
        # controler_AI=world.get_actors(ped_control_ids)
        # for c_ai in controler_AI:
        #     pedestrian_c_ai = world.get_actor(controler_AI[0].parent.id)
        #     pedestrian_way_point = self.map.get_waypoint(pedestrian_c_ai.get_location())
        #     target_location = world.get_random_location_from_navigation()
        #     ai_waypoint = self.map.get_waypoint(target_location)
        #     if ai_waypoint.section_id == pedestrian_way_point.section_id:
        #         c_ai.start()
        #         c_ai.go_to_location(
        #                     target_location
        #                 )


    def get_starting_position(self,world, start_pose):

        starting_location = self.map.get_waypoint(start_pose.location, project_to_road=True)
        transform = Transform(
            Location(x=starting_location.transform.location.x, y=starting_location.transform.location.y,
                     z=start_pose.location.z),
            Rotation(pitch=start_pose.rotation.pitch, yaw=start_pose.rotation.yaw, roll=start_pose.rotation.roll))
        self.ego_location=transform
        return transform