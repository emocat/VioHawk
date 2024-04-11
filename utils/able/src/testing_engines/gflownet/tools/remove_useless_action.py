import json

from testing_engines.gflownet.path_config import path_args


def remove_useless_action(dataset, session):
    space_path = path_args.space_path.format(session)
    with open(space_path) as file:
        action_space = json.load(file)
    remove_action_type = []
    for key, value in action_space.items():
        if len(value) == 1:
            remove_action_type.append(key)

    for action_seq in dataset:
        for action in action_seq["actions"]:
            for type in remove_action_type:
                if action.startswith(type):
                    action_seq["actions"].remove(action)
                    # print("delete {}".format(action))


if __name__ == '__main__':
    sessions = ['double_direction', 'single_direction', 'lane_change', 't_junction']
    for session in sessions:
        print("Current session {}".format(session))
        space_path = "../generator/data/action_space/space_for_{}.json".format(session)
        with open(space_path) as file:
            action_space = json.load(file)
        remove_action_type = []
        for key, value in action_space.items():
            if len(value) == 1:
                remove_action_type.append(key)

        action_set_path = "../generator/data/testset_2/a_testset_for_{}.json".format(session)
        with open(action_set_path) as file:
            action_sequences = json.load(file)
        for action_seq in action_sequences:
            for action in action_seq["actions"]:
                for type in remove_action_type:
                    if action.startswith(type):
                        action_seq["actions"].remove(action)
                        print("delete {}".format(action))

        action_set_path = "../generator/data/testset_2/a_testset_for_{}_remove.json".format(session)
        with open(action_set_path, 'w', encoding='utf-8') as f:
            json.dump(action_sequences, f, indent=4)
