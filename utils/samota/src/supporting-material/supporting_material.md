# Supporting Material

This file contains the supporting material including requirements, constraints, and variable definitions.

(NOTE: this markdown file is made using [atom](https://atom.io); if you do not have a proper markdown viewer, you can use [this online viewer](https://dillinger.io))

## Safety Requirements for Pylot

| Safety Requirement | Fitness Function | Threshold | Explanation
| -------------  | ------------- | -------------- | --------------
| follow the center of the lane  | 1 - (min(distance(center_of_lane, center_of_ego_vehicle), 1.15) / 1.15) | 0 | If the ego vehicle deviates from the center of the lane more than 1.15m, it is a safety violation.
| avoid collision with other vehicles  | min(distance(ego_vehicle, vehicle_in_front), 1) | 0 | If the distance between two vehicles is zero, it is a safety violation. We use 1m as the maximum distance to care for normalization purposes.
| avoid collision with pedestrians  | min(distance(ego_vehicle, nearest_pedestrian), 1) | 0 | If the distance between the ego vehicle and its nearest pedestrian is zero, it is a safety violation. We use 1m as the maximum distance to care for normalization purposes.
| avoid collision with static obstacles | min(distance(ego_vehicle, nearest_static_object), 1) | 0 | If the distance between the ego vehicle and its nearest static object is zero, it is a safety violation. We use 1m as the maximum distance to care for normalization purposes.
| abide by traffic rules (e.g., traffic lights) | 1 if all traffic rules are abided by; 0 otherwise | 0 | If any of the traffic rules art not properly abided by, it is a safety violation.
| reach the destination within a given time | distance_travelled / total_distance | 0.95 | The percentage of travelled distance should be more than 95%.

* Each fitness function returns a score ranging between 0 and 1.
* If the fitness score is less than or equal to the threshold, it represents a safety violation.
* The threshold value of 0.95 for the last requirement is because we found that the ego vehicle can stop in front of the destination point even if it drives without any issue.


## Attributes for Scenario Generation
| Attribute Name  | Possible Values | Explanation |
| -------------  | ------------- | ----------- |
| road type  | Straight, Left turn, Right Turn, Cross Road | Different types of available roads |
| road ID  | {0,1,2,3} | Different parts of maps (start/end points) |
| scenario length | {0}  | To reduce the complexity, we used fixed length for each road |
| vehicle_in_front | {T,F}  | True or False |
| vehicle_in_adjcent_lane  | {T,F}  | True or False |
| vehicle_in_opposite_lane  | {T,F}  | True or False |
| vehicle_in_front_two_wheeled  | {T,F}  | True or False |
| vehicle_in_adjacent_two_wheeled | {T,F}  | True or False |
| vehicle_in_opposite_two_wheeled | {T,F}  | True or False |
| time of day  | {Noon, Sunset, Night}  | Change by changing position of sun |
| weather  | {clear, cloudy, wet, wetcloudy, SoftRain, MidRain, HardRain} | Predefined names in CARLA |
| pedestrian density | {T,F}  | True or False |
| vehicle target speed | {20,30,40} | Speed in km/h |
| presence of trees | {T,F}  | True or False |
| presence of buildings | {T,F}  | True or False |
| driving task  | {follow_road, take 1st exit, take 2nd exit, take 3rd exit} | Tasks that ego vehicle should perform |


## Constraints in Scenario Generation

- We chose specific spawn points for the ego vehicle in the map to ensure the given road type is consistent with the spawned location; for example, if the specific road type is "curved", then the ego vehicle is spawned at the start of a curved road in a given map.
- The task of ego vehicle is, by default, to follow the given road. For a cross road, the task specifies where to exit (e.g., first, second, and third exit).
- The movement of pedestrian is controlled by Unreal Engine and is not deterministic. To overcome this issue, we have made pedestrians stationary.
