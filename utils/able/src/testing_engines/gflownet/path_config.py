class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
# path_args = AttrDict(
#     {
#         # testing result data
#         "test_result_direct": "/home/xdzhang/data/apollo7/active+max/{}",
#         "debug_result_direct": "/home/xdzhang/data/apollo7/debug/{}",
#         "spec_path": "rawdata/specs/spec_data.json",
#         # data for training
#         "train_data_path": "generator/data/testset/a_testset_for_{}.json",
#         # template for generating scenarios quickly
#         "template_path": "generator/data/templates/template_for_{}.json",
#         # GFlownet model path
#         "ckpt": "generator/ckpt/{}_gfn.pkl",
#         # proxy path
#         "proxy_path": "generator/proxy/model/{}",
#         # result path from gfl model
#         "in_process_dataset_path": "generator/result/action_sequence_{}.json",
#         "new_batch_path": "generator/result/new_action_sequence_{}.json",
#         "space_path": "generator/data/action_space/space_for_{}.json"
#     }
# )
path_args = AttrDict(
    {
        # testing result data
        "test_result_direct": "/home/apollo/VioHawk/utils/able/src/active+max/{}",
        "debug_result_direct": "/home/apollo/VioHawk/utils/able/src/debug/{}",
        "spec_path": "/home/apollo/VioHawk/utils/able/src/testing_engines/gflownet/rawdata/specs/spec_data_test.json",
        # data for training
        "train_data_path": "/home/apollo/VioHawk/utils/able/src/testing_engines/gflownet/generator/data/testset/{}.json",
        # template for generating scenarios quickly
        "template_path": "/home/apollo/VioHawk/utils/able/src/testing_engines/gflownet/generator/data/templates/template_for_{}.json",
        "raw_template_path": "/home/apollo/VioHawk/utils/able/src/testing_engines/gflownet/generator/data/templates/raw_template_for_{}.json",
        # GFlownet model path
        "ckpt": "/home/apollo/VioHawk/utils/able/src/testing_engines/gflownet/generator/ckpt/{}_gfn.pkl",
        # proxy path
        "proxy_path": "/home/apollo/VioHawk/utils/able/src/testing_engines/gflownet/generator/proxy/model/{}",
        # result path from gfl model
        "in_process_dataset_path": "/home/apollo/VioHawk/utils/able/src/testing_engines/gflownet/generator/result/action_sequence_{}.json",
        "new_batch_path": "/home/apollo/VioHawk/utils/able/src/testing_engines/gflownet/generator/result/new_action_sequence_{}.json",
        "space_path": "/home/apollo/VioHawk/utils/able/src/testing_engines/gflownet/generator/data/action_space/space_for_{}.json"
    }
)