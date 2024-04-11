import torch
import json
import numpy as np
import sys
def judge_generated(x,actions_index,actions_category):
  #print(x)
  x = x.numpy()
  flag = True
  index = 0
  for action_id in x:
    cur_action_index = actions_index[actions_category[index]]
    #print(cur_action_index)
    #print(action_id)
    if action_id >= cur_action_index[0] and action_id <= cur_action_index[1]:
      index = index + 1
      continue
    else:
      flag = False
      #print("FALSE")
      break
  #sys.exit(0)
  return flag
def sample2proxy(samples,redun_list,redun_dict,max_len,):
    generated = np.ones(shape=(len(samples),max_len))
    #print("samples")
    #print(samples)
    filled = []
    for redun in redun_list:
        index, action_id = redun_dict[redun]
        generated[:,index] = action_id
        filled.append(index)
    gflow_index = 0
   # print(samples.shape)
    for i in range(max_len):
        if i in filled:
            continue
        else:
            for l in range(len(generated)):
              generated[l:,i] = samples[l][gflow_index]
            gflow_index = gflow_index + 1
    return generated

def transform2json(samples, id2action):
    json_list = []
    index = 0
    for sample in samples:
        sample_dict = {}
        sample_dict["ScenarioName"] = "NO_"+str(index)
        sample_dict['actions'] = [id2action[int(action)] for action in sample]
        json_list.append(sample_dict)
        index = index + 1
    return json_list

def gflow2proxy(gflow, redun_list, redun_dict,batch_size,proxy_max_len):
  generated = torch.LongTensor(batch_size, proxy_max_len)
  generated.fill_(-1)
  filled = []
  for redun in redun_list:
    index, action_id = redun_dict[redun]
    generated[:,index] = action_id
    filled.append(index)
  gflow_index = 0
  for i in range(proxy_max_len):
    if i in filled:
      continue
    else:
      generated[:,i] = gflow[:,gflow_index]
      gflow_index = gflow_index + 1
  return generated

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self