import json
import math
import os

from testing_engines.gflownet.path_config import path_args

DECIMAL = 1

def my_round(value, level):
    if level == 0:
        return round(value, 0)
    elif level == 1:
        if value == 0.0:
            return 0.0
        decimal, integer = math.modf(value)
        if decimal >= 0.0 and decimal < 0.25:
            decimal = 0.0
        elif decimal >= 0.25 and decimal < 0.7:
            decimal = 0.5
        else:
            decimal = 1.0
        return decimal + integer
    else:
        assert False and "Wrong Setting."


def make_env_actions(scenario, actionSeq):
    # Minute is not considered
    actionSeq.append('time+' + str(scenario['time']['hour']))
    actionSeq.append('weather+rain+' + str(round(scenario['weather']['rain'], 1)))
    actionSeq.append('weather+wetness+' + str(round(scenario['weather']['wetness'], 1)))
    actionSeq.append('weather+fog+' + str(round(scenario['weather']['fog'], 1)))

def make_env_actions_space(scenario, actionSpace):
    # Minute is not considered
    if 'time+' not in actionSpace:
        actionSpace['time+'] = set()
    actionSpace['time+'].add(round(scenario['time']['hour'], 1))
    if 'weather+rain+' not in actionSpace:
        actionSpace['weather+rain+'] = set()
    actionSpace['weather+rain+'].add(round(scenario['weather']['rain'], 1))
    if 'weather+wetness+' not in actionSpace:
        actionSpace['weather+wetness+'] = set()
    actionSpace['weather+wetness+'].add(round(scenario['weather']['wetness'], 1))
    if 'weather+fog+' not in actionSpace:
        actionSpace['weather+fog+'] = set()
    actionSpace['weather+fog+'].add(round(scenario['weather']['fog'], 1))

def make_ego_actions(scenario, actionSeq):
    pos = scenario['ego']['start']['lane_position']
    actionSeq.append('ego+start+lane_position+' + pos['lane'] + '+' + str(my_round(pos['offset'], DECIMAL)))
    actionSeq.append('ego+start+speed+' + str(my_round(scenario['ego']['start']['speed'], DECIMAL)))
    pos = scenario['ego']['destination']['lane_position']
    actionSeq.append('ego+destination+lane_position+' + pos['lane'] + '+' + str(my_round(pos['offset'], DECIMAL)))
    actionSeq.append('ego+destination+speed+' + str(my_round(scenario['ego']['destination']['speed'], DECIMAL)))


def make_ego_actions_space(scenario, actionSpace):
    poition = scenario['ego']['start']['lane_position']
    type_name = 'ego+start+lane_position+' + poition['lane'] + "+"
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(my_round(poition['offset'], DECIMAL))

    type_name = 'ego+start+speed+'
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(my_round(scenario['ego']['start']['speed'], DECIMAL))

    poition = scenario['ego']['destination']['lane_position']
    type_name = 'ego+destination+lane_position+' + poition['lane'] + "+"
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(my_round(poition['offset'], DECIMAL))

    type_name = 'ego+destination+speed+'
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(my_round(scenario['ego']['destination']['speed'], DECIMAL))


def make_npc_actions(scenario, actionSeq):
    for npc in scenario['npcList']:
        npcid = npc['ID']
        pos = npc['start']['lane_position']
        actionSeq.append(npcid + '+name+' + npc['name'])
        actionSeq.append(npcid + '+start+lane_position+' + pos['lane'] + '+' + str(my_round(pos['offset'], DECIMAL)))
        actionSeq.append(npcid + '+start+speed+' + str(my_round(npc['start']['speed'], DECIMAL)))
        for i, waypoint in enumerate(npc['motion']):
            pos = waypoint['lane_position']
            actionSeq.append(npcid + '+motion+' + str(i) + '+lane_position+' + pos['lane'] + '+' + str(my_round(pos['offset'], DECIMAL)))
            actionSeq.append(npcid + '+motion+' + str(i) + '+speed+' + str(my_round(waypoint['speed'], DECIMAL)))
        if npc['destination'] is None:
            continue
        pos = npc['destination']['lane_position']
        actionSeq.append(npcid + '+destination+lane_position+' + pos['lane'] + '+' + str(my_round(pos['offset'], DECIMAL)))
        actionSeq.append(npcid + '+destination+speed+' + str(my_round(npc['destination']['speed'], DECIMAL)))

def make_npc_actions_space(scenario, actionSpace):
    for npc in scenario['npcList']:
        npcid = npc['ID']
        type_name = npcid + '+name+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(npc['name'])

        lp = npc['start']['lane_position']
        type_name = npcid + '+start+lane_position+' + lp['lane'] + '+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(my_round(lp['offset'], DECIMAL))
        type_name = npcid + '+start+speed+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(my_round(npc['start']['speed'], DECIMAL))
        for i, waypoint in enumerate(npc['motion']):
            type_name = npcid + '+motion+' + str(i) + '+lane_position+' + waypoint['lane_position']['lane'] + '+'
            if type_name not in actionSpace:
                actionSpace[type_name] = set()
            actionSpace[type_name].add(my_round(waypoint['lane_position']['offset'], DECIMAL))
            type_name = npcid + '+motion+' + str(i) + '+speed+'
            if type_name not in actionSpace:
                actionSpace[type_name] = set()
            actionSpace[type_name].add(my_round(waypoint['speed'], DECIMAL))
        if npc['destination'] is None:
            continue
        lp = npc['destination']['lane_position']
        type_name = npcid + '+destination+lane_position+' + lp['lane'] + '+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(my_round(lp['offset'], DECIMAL))
        type_name = npcid + '+destination+speed+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(my_round(npc['destination']['speed'], DECIMAL))

def make_pedestrain_actions(scenario, actionSeq):
    pass

def make_obstacle_actions(scenario, actionSeq):
    pass

def generate_actions(path):
    action_sequences = []
    with open(path) as f:
        data = json.load(f)
        for scenario in data:
            print('Handling ' + scenario['ScenarioName'])
            action_sequences.append(encode(scenario))
    return action_sequences

"""
Testable Scenario --> Action Sequence
"""
def encode(scenario):
    for_one_scenario = {'ScenarioName': scenario['ScenarioName']}
    actions = []
    make_env_actions(scenario, actions)
    make_ego_actions(scenario, actions)
    make_npc_actions(scenario, actions)
    make_pedestrain_actions(scenario, actions)
    make_obstacle_actions(scenario, actions)
    for_one_scenario['actions'] = actions
    for_one_scenario['robustness'] = scenario['robustness']
    return for_one_scenario

"""
Action Sequence --> Testable Scenario
"""
def decode(action_sequence, session):
    template_path = path_args.template_path.format(session)
    # template_path = "../data/templates/template_for_{}.json".format(session)
    with open(template_path) as file:
        template = json.load(file)
        template["ScenarioName"] = action_sequence["ScenarioName"]
        for action in action_sequence["actions"]:
            if action.startswith("time+"):
                hour = action.replace("time+", "")
                template["time"]["hour"] = int(hour)
            elif action.startswith("weather+rain+"):
                rain = action.replace("weather+rain+", "")
                template["weather"]["rain"] = float(rain)
            elif action.startswith("weather+wetness+"):
                wetness = action.replace("weather+wetness+", "")
                template["weather"]["wetness"] = float(wetness)
            elif action.startswith("weather+fog+"):
                fog = action.replace("weather+fog+", "")
                template["weather"]["fog"] = float(fog)
            # For decoding without nonsense
            elif action.startswith("ego+start+lane_position"):
                new_lane_id = action.split("+")[3]
                old_lane_id = template["ego"]["start"]["lane_position"]["lane"]
                if new_lane_id != old_lane_id:
                    template["ego"]["start"]["lane_position"]["lane"] = new_lane_id
                start_offset = action.replace("ego+start+lane_position+" + new_lane_id + "+", "")
                template["ego"]["start"]["lane_position"]["offset"] = float(start_offset)
            elif action.startswith("ego+destination+lane_position"):
                new_lane_id = action.split("+")[3]
                old_lane_id = template["ego"]["destination"]["lane_position"]["lane"]
                if new_lane_id != old_lane_id:
                    template["ego"]["destination"]["lane_position"]["lane"] = new_lane_id
                dest_offset = action.replace("ego+destination+lane_position+" + new_lane_id + "+", "")
                template["ego"]["destination"]["lane_position"]["offset"] = float(dest_offset)
            elif "npc" in action and "lane_position" in action:
                for i in range(len(template["npcList"])):
                    if action.startswith("npc" + str(i+1) + "+start+lane_position"):
                        new_lane_id = action.split("+")[3]
                        old_lane_id = template["npcList"][i]["start"]["lane_position"]["lane"]
                        if new_lane_id != old_lane_id:
                            template["npcList"][i]["start"]["lane_position"]["lane"] = new_lane_id
                        npc1_start_offset = action.replace("npc" + str(i+1) + "+start+lane_position+" + new_lane_id + "+", "")
                        template["npcList"][i]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
                    elif action.startswith("npc" + str(i+1) + "+motion+0+lane_position"):
                        new_lane_id = action.split("+")[3]
                        old_lane_id = template["npcList"][i]["motion"][0]["lane_position"]["lane"]
                        if new_lane_id != old_lane_id:
                            template["npcList"][i]["motion"][0]["lane_position"]["lane"] = new_lane_id
                        npc1_motion_offset = action.replace("npc" + str(i+1) + "+motion+0+lane_position+" + new_lane_id + "+", "")
                        template["npcList"][i]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
                    elif action.startswith("npc" + str(i+1) + "+destination+lane_position"):
                        new_lane_id = action.split("+")[3]
                        old_lane_id = template["npcList"][i]["destination"]["lane_position"]["lane"]
                        if new_lane_id != old_lane_id:
                            template["npcList"][i]["destination"]["lane_position"]["lane"] = new_lane_id
                        npc1_dest_offset = action.replace("npc" + str(i+1) + "+destination+lane_position+" + new_lane_id + "+", "")
                        template["npcList"][i]["destination"]["lane_position"]["offset"] = float(npc1_dest_offset)
            

            # For double direction.
            elif action.startswith("ego+start+lane_position+lane_540+"):
                start_offset = action.replace("ego+start+lane_position+lane_540+", "")
                template["ego"]["start"]["lane_position"]["offset"] = float(start_offset)
            elif action.startswith("ego+start+speed+"):
                start_speed = action.replace("ego+start+speed+", "")
                template["ego"]["start"]["speed"] = float(start_speed)
            elif action.startswith("ego+destination+lane_position+lane_572+"):
                dest_offset = action.replace("ego+destination+lane_position+lane_572+", "")
                template["ego"]["destination"]["lane_position"]["offset"] = float(dest_offset)
            elif action.startswith("ego+destination+speed+"):
                dest_speed = action.replace("ego+destination+speed+", "")
                template["ego"]["destination"]["speed"] = float(dest_speed)
            #NPC Name or Type
            elif action.startswith("npc1+name+"):
                name = action.replace("npc1+name+", "")
                template["npcList"][0]["name"] = name
            elif action.startswith("npc2+name+"):
                name = action.replace("npc2+name+", "")
                template["npcList"][1]["name"] = name
            elif action.startswith("npc3+name+"):
                name = action.replace("npc3+name+", "")
                template["npcList"][2]["name"] = name
            elif action.startswith("npc4+name+"):
                name = action.replace("npc4+name+", "")
                template["npcList"][3]["name"] = name
            elif action.startswith("npc5+name+"):
                name = action.replace("npc5+name+", "")
                template["npcList"][4]["name"] = name
            elif action.startswith("npc6+name+"):
                name = action.replace("npc6+name+", "")
                template["npcList"][5]["name"] = name
            # NPC1
            elif action.startswith("npc1+start+lane_position+lane_574+"):
                npc1_start_offset = action.replace("npc1+start+lane_position+lane_574+", "")
                template["npcList"][0]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc1+start+speed+"):
                npc1_start_speed = action.replace("npc1+start+speed+", "")
                template["npcList"][0]["start"]["speed"] = float(npc1_start_speed)
            elif action.startswith("npc1+motion+0+lane_position+lane_569+"):
                npc1_motion_offset = action.replace("npc1+motion+0+lane_position+lane_569+", "")
                template["npcList"][0]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+0+speed+"):
                npc1_motion_speed = action.replace("npc1+motion+0+speed+", "")
                template["npcList"][0]["motion"][0]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc1+destination+lane_position+lane_569+"):
                npc1_dest_offset = action.replace("npc1+destination+lane_position+lane_569+", "")
                template["npcList"][0]["destination"]["lane_position"]["offset"] = float(npc1_dest_offset)
            elif action.startswith("npc1+destination+speed+"):
                npc1_dest_speed = action.replace("npc1+destination+speed+", "")
                template["npcList"][0]["destination"]["speed"] = float(npc1_dest_speed)
            # NPC2
            elif action.startswith("npc2+start+lane_position+lane_564+"):
                npc2_start_offset = action.replace("npc2+start+lane_position+lane_564+", "")
                template["npcList"][1]["start"]["lane_position"]["offset"] = float(npc2_start_offset)
            elif action.startswith("npc2+start+speed+"):
                npc2_start_speed = action.replace("npc2+start+speed+", "")
                template["npcList"][1]["start"]["speed"] = float(npc2_start_speed)
            elif action.startswith("npc2+motion+0+lane_position+lane_568+"):
                npc2_motion_offset = action.replace("npc2+motion+0+lane_position+lane_568+", "")
                template["npcList"][1]["motion"][0]["lane_position"]["offset"] = float(npc2_motion_offset)
            elif action.startswith("npc2+motion+0+speed+"):
                npc2_motion_speed = action.replace("npc2+motion+0+speed+", "")
                template["npcList"][1]["motion"][0]["speed"] = float(npc2_motion_speed)
            elif action.startswith("npc2+destination+lane_position+lane_568+"):
                npc2_dest_offset = action.replace("npc2+destination+lane_position+lane_568+", "")
                template["npcList"][1]["destination"]["lane_position"]["offset"] = float(npc2_dest_offset)
            elif action.startswith("npc2+destination+speed+"):
                npc2_dest_speed = action.replace("npc2+destination+speed+", "")
                template["npcList"][1]["destination"]["speed"] = float(npc2_dest_speed)
            # NPC3
            elif action.startswith("npc3+start+lane_position+lane_565+"):
                npc3_start_offset = action.replace("npc3+start+lane_position+lane_565+", "")
                template["npcList"][2]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            elif action.startswith("npc3+start+speed+"):
                npc3_start_speed = action.replace("npc3+start+speed+", "")
                template["npcList"][2]["start"]["speed"] = float(npc3_start_speed)
            elif action.startswith("npc3+motion+0+lane_position+lane_569+"):
                npc3_motion_offset = action.replace("npc3+motion+0+lane_position+lane_569+", "")
                template["npcList"][2]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            elif action.startswith("npc3+motion+0+speed+"):
                npc3_motion_speed = action.replace("npc3+motion+0+speed+", "")
                template["npcList"][2]["motion"][0]["speed"] = float(npc3_motion_speed)
            elif action.startswith("npc3+destination+lane_position+lane_569+"):
                npc3_dest_offset = action.replace("npc3+destination+lane_position+lane_569+", "")
                template["npcList"][2]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            elif action.startswith("npc3+destination+speed+"):
                npc3_dest_speed = action.replace("npc3+destination+speed+", "")
                template["npcList"][2]["destination"]["speed"] = float(npc3_dest_speed)
            # NPC4
            elif action.startswith("npc4+start+lane_position+lane_570+"):
                npc4_start_offset = action.replace("npc4+start+lane_position+lane_570+", "")
                template["npcList"][3]["start"]["lane_position"]["offset"] = float(npc4_start_offset)
            elif action.startswith("npc4+start+speed+"):
                npc4_start_speed = action.replace("npc4+start+speed+", "")
                template["npcList"][3]["start"]["speed"] = float(npc4_start_speed)
            elif action.startswith("npc4+motion+0+lane_position+lane_566+"):
                npc4_motion_offset = action.replace("npc4+motion+0+lane_position+lane_566+", "")
                template["npcList"][3]["motion"][0]["lane_position"]["offset"] = float(npc4_motion_offset)
            elif action.startswith("npc4+motion+0+speed+"):
                npc4_motion_speed = action.replace("npc4+motion+0+speed+", "")
                template["npcList"][3]["motion"][0]["speed"] = float(npc4_motion_speed)
            elif action.startswith("npc4+destination+lane_position+lane_566+"):
                npc4_dest_offset = action.replace("npc4+destination+lane_position+lane_566+", "")
                template["npcList"][3]["destination"]["lane_position"]["offset"] = float(npc4_dest_offset)
            elif action.startswith("npc4+destination+speed+"):
                npc4_dest_speed = action.replace("npc4+destination+speed+", "")
                template["npcList"][3]["destination"]["speed"] = float(npc4_dest_speed)
            # NPC5
            elif action.startswith("npc5+start+lane_position+lane_571+"):
                npc5_start_offset = action.replace("npc5+start+lane_position+lane_571+", "")
                template["npcList"][4]["start"]["lane_position"]["offset"] = float(npc5_start_offset)
            elif action.startswith("npc5+start+speed+"):
                npc5_start_speed = action.replace("npc5+start+speed+", "")
                template["npcList"][4]["start"]["speed"] = float(npc5_start_speed)
            elif action.startswith("npc5+motion+0+lane_position+lane_567+"):
                npc5_motion_offset = action.replace("npc5+motion+0+lane_position+lane_567+", "")
                template["npcList"][4]["motion"][0]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+0+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+0+speed+", "")
                template["npcList"][4]["motion"][0]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+destination+lane_position+lane_567+"):
                npc5_dest_offset = action.replace("npc5+destination+lane_position+lane_567+", "")
                template["npcList"][4]["destination"]["lane_position"]["offset"] = float(npc5_dest_offset)
            elif action.startswith("npc5+destination+speed+"):
                npc5_dest_speed = action.replace("npc5+destination+speed+", "")
                template["npcList"][4]["destination"]["speed"] = float(npc5_dest_speed)
            # For the entities in single direction
            elif action.startswith("ego+start+lane_position+lane_623+"):
                start_offset = action.replace("ego+start+lane_position+lane_623+", "")
                template["ego"]["start"]["lane_position"]["offset"] = float(start_offset)
            elif action.startswith("ego+destination+lane_position+lane_145+"):
                dest_offset = action.replace("ego+destination+lane_position+lane_145+", "")
                template["ego"]["destination"]["lane_position"]["offset"] = float(dest_offset)
            elif action.startswith("npc1+start+lane_position+lane_627+"):
                npc1_start_offset = action.replace("npc1+start+lane_position+lane_627+", "")
                template["npcList"][0]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc1+motion+0+lane_position+lane_627+"):
                npc1_motion_offset = action.replace("npc1+motion+0+lane_position+lane_627+", "")
                template["npcList"][0]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+1+lane_position+lane_627+"):
                npc5_motion_offset = action.replace("npc1+motion+1+lane_position+lane_627+", "")
                template["npcList"][0]["motion"][1]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc1+motion+1+speed+"):
                npc5_motion_speed = action.replace("npc1+motion+1+speed+", "")
                template["npcList"][0]["motion"][1]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc1+motion+2+lane_position+lane_627+"):
                npc5_motion_offset = action.replace("npc1+motion+2+lane_position+lane_627+", "")
                template["npcList"][0]["motion"][2]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc1+motion+2+speed+"):
                npc5_motion_speed = action.replace("npc1+motion+2+speed+", "")
                template["npcList"][0]["motion"][2]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc1+motion+3+lane_position+lane_899+"):
                npc5_motion_offset = action.replace("npc1+motion+3+lane_position+lane_899+", "")
                template["npcList"][0]["motion"][3]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc1+motion+3+speed+"):
                npc5_motion_speed = action.replace("npc1+motion+3+speed+", "")
                template["npcList"][0]["motion"][3]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc1+motion+4+lane_position+lane_145+"):
                npc5_motion_offset = action.replace("npc1+motion+4+lane_position+lane_145+", "")
                template["npcList"][0]["motion"][4]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc1+motion+4+speed+"):
                npc5_motion_speed = action.replace("npc1+motion+4+speed+", "")
                template["npcList"][0]["motion"][4]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc1+motion+5+lane_position+lane_145+"):
                npc5_motion_offset = action.replace("npc1+motion+5+lane_position+lane_145+", "")
                template["npcList"][0]["motion"][5]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc1+motion+5+speed+"):
                npc5_motion_speed = action.replace("npc1+motion+5+speed+", "")
                template["npcList"][0]["motion"][5]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc1+destination+lane_position+lane_145+"):
                npc1_start_offset = action.replace("npc1+destination+lane_position+lane_145+", "")
                template["npcList"][0]["destination"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc2+start+lane_position+lane_627+"):
                npc3_start_offset = action.replace("npc2+start+lane_position+lane_627+", "")
                template["npcList"][1]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            elif action.startswith("npc2+motion+0+lane_position+lane_151+"):
                npc3_motion_offset = action.replace("npc2+motion+0+lane_position+lane_151+", "")
                template["npcList"][1]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            elif action.startswith("npc2+destination+lane_position+lane_151+"):
                npc3_dest_offset = action.replace("npc2+destination+lane_position+lane_151+", "")
                template["npcList"][1]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            elif action.startswith("npc3+start+lane_position+lane_626+"):
                npc3_start_offset = action.replace("npc3+start+lane_position+lane_626+", "")
                template["npcList"][2]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            elif action.startswith("npc3+motion+0+lane_position+lane_150+"):
                npc3_motion_offset = action.replace("npc3+motion+0+lane_position+lane_150+", "")
                template["npcList"][2]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            elif action.startswith("npc3+destination+lane_position+lane_150+"):
                npc3_dest_offset = action.replace("npc3+destination+lane_position+lane_150+", "")
                template["npcList"][2]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            elif action.startswith("npc4+start+lane_position+lane_625+"):
                npc3_start_offset = action.replace("npc4+start+lane_position+lane_625+", "")
                template["npcList"][3]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            elif action.startswith("npc4+motion+0+lane_position+lane_149+"):
                npc3_motion_offset = action.replace("npc4+motion+0+lane_position+lane_149+", "")
                template["npcList"][3]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            elif action.startswith("npc4+destination+lane_position+lane_149+"):
                npc3_dest_offset = action.replace("npc4+destination+lane_position+lane_149+", "")
                template["npcList"][3]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            # For the entities in lane change
            elif action.startswith("ego+start+lane_position+lane_221+"):
                start_offset = action.replace("ego+start+lane_position+lane_221+", "")
                template["ego"]["start"]["lane_position"]["offset"] = float(start_offset)
            elif action.startswith("ego+destination+lane_position+lane_220+"):
                dest_offset = action.replace("ego+destination+lane_position+lane_220+", "")
                template["ego"]["destination"]["lane_position"]["offset"] = float(dest_offset)
            elif action.startswith("npc1+start+lane_position+lane_221+"):
                npc1_start_offset = action.replace("npc1+start+lane_position+lane_221+", "")
                template["npcList"][0]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc2+start+lane_position+lane_221+"):
                npc2_start_offset = action.replace("npc2+start+lane_position+lane_221+", "")
                template["npcList"][1]["start"]["lane_position"]["offset"] = float(npc2_start_offset)
            elif action.startswith("npc3+start+lane_position+lane_220+"):
                npc3_start_offset = action.replace("npc3+start+lane_position+lane_220+", "")
                template["npcList"][2]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            elif action.startswith("npc3+motion+0+lane_position+lane_231+"):
                npc3_motion_offset = action.replace("npc3+motion+0+lane_position+lane_231+", "")
                template["npcList"][2]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            elif action.startswith("npc3+destination+lane_position+lane_231+"):
                npc3_dest_offset = action.replace("npc3+destination+lane_position+lane_231+", "")
                template["npcList"][2]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            elif action.startswith("npc4+start+lane_position+lane_220+"):
                npc4_start_offset = action.replace("npc4+start+lane_position+lane_220+", "")
                template["npcList"][3]["start"]["lane_position"]["offset"] = float(npc4_start_offset)
            elif action.startswith("npc5+start+lane_position+lane_220+"):
                npc5_start_offset = action.replace("npc5+start+lane_position+lane_220+", "")
                template["npcList"][4]["start"]["lane_position"]["offset"] = float(npc5_start_offset)
            elif action.startswith("npc5+motion+0+lane_position+lane_220+"):
                npc5_motion_offset = action.replace("npc5+motion+0+lane_position+lane_220+", "")
                template["npcList"][4]["motion"][0]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+1+lane_position+lane_220+"):
                npc5_motion_offset = action.replace("npc5+motion+1+lane_position+lane_220+", "")
                template["npcList"][4]["motion"][1]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+1+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+1+speed+", "")
                template["npcList"][4]["motion"][1]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+motion+2+lane_position+lane_1037+"):
                npc5_motion_offset = action.replace("npc5+motion+2+lane_position+lane_1037+", "")
                template["npcList"][4]["motion"][2]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+2+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+2+speed+", "")
                template["npcList"][4]["motion"][2]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+motion+3+lane_position+lane_1037+"):
                npc5_motion_offset = action.replace("npc5+motion+3+lane_position+lane_1037+", "")
                template["npcList"][4]["motion"][3]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+3+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+3+speed+", "")
                template["npcList"][4]["motion"][3]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+motion+4+lane_position+lane_253+"):
                npc5_motion_offset = action.replace("npc5+motion+4+lane_position+lane_253+", "")
                template["npcList"][4]["motion"][4]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+4+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+4+speed+", "")
                template["npcList"][4]["motion"][4]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+motion+5+lane_position+lane_253+"):
                npc5_motion_offset = action.replace("npc5+motion+5+lane_position+lane_253+", "")
                template["npcList"][4]["motion"][5]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+5+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+5+speed+", "")
                template["npcList"][4]["motion"][5]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+destination+lane_position+lane_253+"):
                npc1_start_offset = action.replace("npc5+destination+lane_position+lane_253+", "")
                template["npcList"][4]["destination"]["lane_position"]["offset"] = float(npc1_start_offset)
            # For the entities in t-junction
            elif action.startswith("ego+start+lane_position+lane_317+"):
                start_offset = action.replace("ego+start+lane_position+lane_317+", "")
                template["ego"]["start"]["lane_position"]["offset"] = float(start_offset)
            elif action.startswith("ego+destination+lane_position+lane_321+"):
                dest_offset = action.replace("ego+destination+lane_position+lane_321+", "")
                template["ego"]["destination"]["lane_position"]["offset"] = float(dest_offset)
            # NPC1
            elif action.startswith("npc1+start+lane_position+lane_328+"):
                npc1_start_offset = action.replace("npc1+start+lane_position+lane_328+", "")
                template["npcList"][0]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc1+motion+0+lane_position+lane_328+"):
                npc1_motion_offset = action.replace("npc1+motion+0+lane_position+lane_328+", "")
                template["npcList"][0]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+1+lane_position+lane_328+"):
                npc1_motion_offset = action.replace("npc1+motion+1+lane_position+lane_328+", "")
                template["npcList"][0]["motion"][1]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+2+lane_position+lane_328+"):
                npc1_motion_offset = action.replace("npc1+motion+2+lane_position+lane_328+", "")
                template["npcList"][0]["motion"][2]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+3+lane_position+lane_1158+"):
                npc1_motion_offset = action.replace("npc1+motion+3+lane_position+lane_1158+", "")
                template["npcList"][0]["motion"][3]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+4+lane_position+lane_1158+"):
                npc1_motion_offset = action.replace("npc1+motion+4+lane_position+lane_1158+", "")
                template["npcList"][0]["motion"][4]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+5+lane_position+lane_320+"):
                npc1_motion_offset = action.replace("npc1+motion+5+lane_position+lane_320+", "")
                template["npcList"][0]["motion"][5]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+5+lane_position+lane_320+"):
                npc1_motion_offset = action.replace("npc1+motion+5+lane_position+lane_320+", "")
                template["npcList"][0]["motion"][5]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+6+lane_position+lane_1206+"):
                npc1_motion_offset = action.replace("npc1+motion+6+lane_position+lane_1206+", "")
                template["npcList"][0]["motion"][6]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+6+speed+"):
                npc1_motion_speed = action.replace("npc1+motion+6+speed+", "")
                template["npcList"][0]["motion"][6]["speed"] = float(npc1_motion_speed)
            # NPC2
            elif action.startswith("npc2+start+lane_position+lane_331+"):
                npc1_start_offset = action.replace("npc2+start+lane_position+lane_331+", "")
                template["npcList"][1]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc2+motion+0+lane_position+lane_331+"):
                npc1_motion_offset = action.replace("npc2+motion+0+lane_position+lane_331+", "")
                template["npcList"][1]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+1+lane_position+lane_331+"):
                npc1_motion_offset = action.replace("npc2+motion+1+lane_position+lane_331+", "")
                template["npcList"][1]["motion"][1]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+1+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+1+speed+", "")
                template["npcList"][1]["motion"][1]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+motion+2+lane_position+lane_1160+"):
                npc1_motion_offset = action.replace("npc2+motion+2+lane_position+lane_1160+", "")
                template["npcList"][1]["motion"][2]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+2+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+2+speed+", "")
                template["npcList"][1]["motion"][2]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+motion+3+lane_position+lane_1158+"):
                npc1_motion_offset = action.replace("npc2+motion+3+lane_position+lane_1158+", "")
                template["npcList"][1]["motion"][3]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+3+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+3+speed+", "")
                template["npcList"][1]["motion"][3]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+motion+4+lane_position+lane_321+"):
                npc1_motion_offset = action.replace("npc2+motion+4+lane_position+lane_321+", "")
                template["npcList"][1]["motion"][4]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+4+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+4+speed+", "")
                template["npcList"][1]["motion"][4]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+motion+5+lane_position+lane_321+"):
                npc1_motion_offset = action.replace("npc2+motion+5+lane_position+lane_321+", "")
                template["npcList"][1]["motion"][5]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+5+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+5+speed+", "")
                template["npcList"][1]["motion"][5]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+motion+6+lane_position+lane_321+"):
                npc1_motion_offset = action.replace("npc2+motion+6+lane_position+lane_321+", "")
                template["npcList"][1]["motion"][6]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+6+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+6+speed+", "")
                template["npcList"][1]["motion"][6]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+destination+lane_position+lane_321+"):
                npc2_dest_offset = action.replace("npc2+destination+lane_position+lane_321+", "")
                template["npcList"][1]["destination"]["lane_position"]["offset"] = float(npc2_dest_offset)
            # NPC3
            elif action.startswith("npc3+start+lane_position+lane_330+"):
                npc1_start_offset = action.replace("npc3+start+lane_position+lane_330+", "")
                template["npcList"][2]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc3+motion+0+lane_position+lane_330+"):
                npc1_motion_offset = action.replace("npc3+motion+0+lane_position+lane_330+", "")
                template["npcList"][2]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+1+lane_position+lane_330+"):
                npc1_motion_offset = action.replace("npc3+motion+1+lane_position+lane_330+", "")
                template["npcList"][2]["motion"][1]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+1+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+1+speed+", "")
                template["npcList"][2]["motion"][1]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+motion+2+lane_position+lane_1161+"):
                npc1_motion_offset = action.replace("npc3+motion+2+lane_position+lane_1161+", "")
                template["npcList"][2]["motion"][2]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+2+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+2+speed+", "")
                template["npcList"][2]["motion"][2]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+motion+3+lane_position+lane_1157+"):
                npc1_motion_offset = action.replace("npc3+motion+3+lane_position+lane_1157+", "")
                template["npcList"][2]["motion"][3]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+3+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+3+speed+", "")
                template["npcList"][2]["motion"][3]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+motion+4+lane_position+lane_322+"):
                npc1_motion_offset = action.replace("npc3+motion+4+lane_position+lane_322+", "")
                template["npcList"][2]["motion"][4]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+4+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+4+speed+", "")
                template["npcList"][2]["motion"][4]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+motion+5+lane_position+lane_322+"):
                npc1_motion_offset = action.replace("npc3+motion+5+lane_position+lane_322+", "")
                template["npcList"][2]["motion"][5]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+5+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+5+speed+", "")
                template["npcList"][2]["motion"][5]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+motion+6+lane_position+lane_322+"):
                npc1_motion_offset = action.replace("npc3+motion+6+lane_position+lane_322+", "")
                template["npcList"][2]["motion"][6]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+6+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+6+speed+", "")
                template["npcList"][2]["motion"][6]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+destination+lane_position+lane_322+"):
                npc2_dest_offset = action.replace("npc3+destination+lane_position+lane_322+", "")
                template["npcList"][2]["destination"]["lane_position"]["offset"] = float(npc2_dest_offset)
            # NPC4
            elif action.startswith("npc4+start+lane_position+lane_329+"):
                npc1_start_offset = action.replace("npc4+start+lane_position+lane_329+", "")
                template["npcList"][3]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc4+motion+0+lane_position+lane_329+"):
                npc1_motion_offset = action.replace("npc4+motion+0+lane_position+lane_329+", "")
                template["npcList"][3]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+1+lane_position+lane_329+"):
                npc1_motion_offset = action.replace("npc4+motion+1+lane_position+lane_329+", "")
                template["npcList"][3]["motion"][1]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+1+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+1+speed+", "")
                template["npcList"][3]["motion"][1]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+motion+2+lane_position+lane_1162+"):
                npc1_motion_offset = action.replace("npc4+motion+2+lane_position+lane_1162+", "")
                template["npcList"][3]["motion"][2]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+2+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+2+speed+", "")
                template["npcList"][3]["motion"][2]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+motion+3+lane_position+lane_1157+"):
                npc1_motion_offset = action.replace("npc4+motion+3+lane_position+lane_1157+", "")
                template["npcList"][3]["motion"][3]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+3+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+3+speed+", "")
                template["npcList"][3]["motion"][3]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+motion+4+lane_position+lane_323+"):
                npc1_motion_offset = action.replace("npc4+motion+4+lane_position+lane_323+", "")
                template["npcList"][3]["motion"][4]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+4+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+4+speed+", "")
                template["npcList"][3]["motion"][4]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+motion+5+lane_position+lane_323+"):
                npc1_motion_offset = action.replace("npc4+motion+5+lane_position+lane_323+", "")
                template["npcList"][3]["motion"][5]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+5+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+5+speed+", "")
                template["npcList"][3]["motion"][5]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+motion+6+lane_position+lane_323+"):
                npc1_motion_offset = action.replace("npc4+motion+6+lane_position+lane_323+", "")
                template["npcList"][3]["motion"][6]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+6+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+6+speed+", "")
                template["npcList"][3]["motion"][6]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+destination+lane_position+lane_323+"):
                npc2_dest_offset = action.replace("npc4+destination+lane_position+lane_323+", "")
                template["npcList"][3]["destination"]["lane_position"]["offset"] = float(npc2_dest_offset)
            else:
                assert False, "No matching for action: " + action
    return template

def generate_actions_space(path):
    action_space = {}
    with open(path) as f:
        data = json.load(f)
        for scenario in data:
            print('Handling ' + scenario['ScenarioName'])
            make_env_actions_space(scenario, action_space)
            make_ego_actions_space(scenario, action_space)
            make_npc_actions_space(scenario, action_space)
    return action_space

def gen_dataset_from_rawdata(session):
    raw_data_path = '../../rawdata/one_scenario/testset_for_' + session + '.json'
    action_dataset_path = '../data/testset_2/a_testset_for_' + session + '.json'
    action_space_path = '../data/action_space_2/space_for_' + session + '.json'

    action_seqs = generate_actions(raw_data_path)
    action_space = generate_actions_space(raw_data_path)
    # For Debugging
    with open(action_dataset_path, 'w', encoding='utf-8') as f:
        json.dump(action_seqs, f, ensure_ascii=False, indent=4)
    with open(action_space_path, 'w', encoding='utf-8') as f:
        for key, value in action_space.items():
            action_space[key] = sorted(list(value))
        json.dump(action_space, f, ensure_ascii=False, indent=4)
    return action_seqs


def generate_scenarios_batch(session):
    test_cases_batch = []
    # data_path = '../data/a_testset_for_{}.json'.format(session)
    data_path = "/home/xdzhang/work/shortgun/testing_engines/gflownet/generator/data/testset/a_testset_for_{}.json".format(session)
    with open(data_path) as file:
        dataset = json.load(file)
        for item in dataset:
            test_cases_batch.append(decode(item, session))
    result_path = '../data/Scenarios_{}.json'.format(session)
    with open(result_path, 'w') as wf:
        json.dump(test_cases_batch, wf, indent=4)
    return test_cases_batch


if __name__ == '__main__':
    # sessions = ['single_direction', 'double_direction', 'lane_change', 't_junction']
    sessions = ['lane_change']
    for session in sessions:
        print("Handling {}".format(session))
        # gen_dataset_from_rawdata(session)
        generate_scenarios_batch(session)