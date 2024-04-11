import json
import os

from testing_engines.gflownet.lib.AssertionExtraction import SingleAssertion
from testing_engines.gflownet.lib.EXtraction import ExtractAll
from testing_engines.gflownet.lib.monitor import Monitor

if __name__ == "__main__":
    # laws = ['law38', 'law44', 'law45', 'law46', 'law47', 'law50', 'law51', 'law52', 'law53', 'law57', 'law58', 'law59', 'law62']
    laws = ['law51_sub3', 'law51_sub4', 'law51_sub5', 'law51_sub6', 'law51_sub7']
    law_table = dict()
    for law in laws:
        input_file = 'laws/{}.txt'.format(law)
        isGroundTruth = True
        extracted_script = ExtractAll(input_file, isGroundTruth)
        scenario_spec = extracted_script.Get_Specifications()
        single_spec = SingleAssertion(scenario_spec["scenario0"][0], "san_francisco")
        law_table[law] = single_spec.sub_violations
        print(law)
        print(scenario_spec["scenario0"][0])
        print(single_spec.sub_violations)

    with open('law51-table.json', 'w', encoding='utf-8') as f:
        json.dump(law_table, f, ensure_ascii=False, indent=4)