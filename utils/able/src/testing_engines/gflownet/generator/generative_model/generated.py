from model import TransformerModel, make_mlp
from proxy import proxy
from utils import *
from dataset import GFNSet
import tqdm
import numpy as np
import torch.nn.functional as F

def get_proxy_model(proxy_path):
    proxy_model =  proxy(num_tokens=154,
                                num_outputs=1,
                                num_hid=1024,
                                num_layers=4, # TODO: add these as hyperparameters?
                                dropout=0.1,
                                max_len=38)
    proxy_model.load_state_dict(torch.load(proxy_path,map_location='cpu')['state_dict'])




if __name__ == '__main__':
    gflownet_set = GFNSet("../data/dataset/a_testset_for_double_direction.json", train=False)
    gflownet_path = 'ckpt/gflownet.pth'

    params = AttrDict({
        "n_words": len(gflownet_set.actions_list), 
        "pad_index" : gflownet_set.pad_index, 
        "eos_index" : gflownet_set.bos_index, 
        "bos_index" : gflownet_set.bos_index,
        'max_length': gflownet_set.max_len,
        'actions_index':gflownet_set.actions_indexes,
        'actions_list': gflownet_set.actions_list,
        "actions_category":gflownet_set.actions_category,
        "proxy_actions_list":gflownet_set.proxy_actions_list,
        "emb_dim" : 256, 
        "batch_size": 2

    })
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logZ = torch.zeros((1,)).to(device)
    n_hid = 256
    n_layers = 32
    mlp = make_mlp([params.emb_dim] + [n_hid] * n_layers + [params.n_words]).to(device)
    model = TransformerModel(params, mlp).to(device)
    print(model)
    P_B = 1 # DAG & sequence generation => tree 
    model = torch.load(gflownet_path)
    batch_size = params.batch_size
    max_len = params.max_length + 0
    samples = []

    for it in tqdm.trange(100):
        nan_flag = False
        generated = torch.LongTensor(batch_size, max_len)  # upcoming output
        generated.fill_(params.pad_index)                  # fill upcoming ouput with <PAD>
        generated[:,0].fill_(params.bos_index)             # <BOS> (start token), initial state

        # Length of already generated sequences : 1 because of <BOS>
        #gen_len = (generated != params.pad_index).long().sum(dim=1)
        gen_len = torch.LongTensor(batch_size,).fill_(1) # (batch_size,)
        # 1 (True) if the generation of the sequence is not yet finished, 0 (False) otherwise
        unfinished_sents = gen_len.clone().fill_(1) # (batch_size,)
        # Length of already generated sequences : 1 because of <BOS>
        cur_len = 1 

        while cur_len < max_len:
            state = generated[:,:cur_len] + 0 # (bs, cur_len)
            with torch.no_grad():
                tensor = model(state.to(device), lengths=gen_len.to(device)) # (bs, cur_len, vocab_size)
            #scores = tensor[:,0] # (bs, vocab_size) : use last word for prediction
            scores = tensor.sum(dim=1) # (bs, vocab_size) 
            # fixed length generation
            
            scores = scores.log_softmax(1)
            sample_temperature = 1
            probs = F.softmax(scores / sample_temperature, dim=1)
            #next_words = torch.distributions.categorical.Categorical(probs=probs).sample()
            try:
                next_words = torch.multinomial(probs, 1).squeeze(1)
            except:
                nan_flag = True
                break
            # update generations / lengths / finished sentences / current length

            generated[:,cur_len] = next_words.cpu() * unfinished_sents + params.pad_index * (1 - unfinished_sents)
            gen_len.add_(unfinished_sents) # add 1 to the length of the unfinished sentences
            unfinished_sents.mul_(next_words.cpu().ne(params.eos_index).long()) # as soon as we generate <EOS>, set unfinished_sents to 0
            cur_len = cur_len + 1
        
            # stop when there is a <EOS> in each sentence, or if we exceed the maximul length
            if unfinished_sents.max() == 0:
                break

        #R = reward_function(generated, reward_coef, lambda_, beta).to(device)
        if nan_flag == True:
            nan_flag = False
            continue

        samples.extend(generated)  
    samples = sample2proxy(samples,gflownet_set.redun_list,gflownet_set.redun_dict,38)
    transform2json(samples,gflownet_set.proxy_actions_list,"result.json")
    print(len(samples))