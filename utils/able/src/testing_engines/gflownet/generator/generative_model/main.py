from setuptools import find_packages
import tqdm
import numpy as np
import torch.nn.functional as F

from testing_engines.gflownet.generator.generative_model.model import TransformerModel, make_mlp
from testing_engines.gflownet.generator.generative_model.proxy_model import proxy
from testing_engines.gflownet.generator.generative_model.utils import *
from testing_engines.gflownet.generator.generative_model.dataset import GFNSet
from testing_engines.gflownet.generator.generative_model.gfn_config import args
from testing_engines.gflownet.path_config import path_args


def get_proxy_model(proxy_path,num_tokens,max_len,num_layers,num_hid):
    proxy_model =  proxy(num_tokens=num_tokens,
                                num_outputs=1,
                                num_hid=num_hid,
                                num_layers=num_layers, # TODO: add these as hyperparameters?
                                dropout=0.1,
                                max_len=max_len)
    proxy_model.load_state_dict(torch.load(proxy_path,map_location='cpu')['state_dict'])
    return proxy_model


def generate_samples_with_gfn(dataset, session):
    # dataset_path = dataset_path_form.format(session)
    gflownet_set = GFNSet(dataset, train=False)
    proxy_path = path_args.proxy_path.format(session) + "/best_w.pth"
    save_ckpt_path = path_args.ckpt.format(session)
    params = AttrDict({
        "n_words": len(gflownet_set.proxy_actions_list), 
        "pad_index" : gflownet_set.pad_index, 
        "eos_index" : gflownet_set.bos_index, 
        "bos_index" : gflownet_set.bos_index,
        'max_length': gflownet_set.proxy_max_len,
        'actions_index':gflownet_set.proxy_actions_indexes,
        'actions_list': gflownet_set.proxy_actions_list,
        "actions_category":gflownet_set.proxy_actions_category,
        "emb_dim" : args.emb_dim, 
        "batch_size": args.batch_size

    })
    x = gflownet_set[0]
    # print(len(params.actions_category))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logZ = torch.zeros((1,)).to(device)
    n_hid = args.n_hid
    n_layers = args.n_layers
    mlp = make_mlp([params.emb_dim] + [n_hid] * n_layers + [params.n_words]).to(device)
    model = TransformerModel(params, mlp).to(device)
    P_B = 1 # DAG & sequence generation => tree 
    optim = torch.optim.Adam([ {'params':model .parameters(), 'lr':0.0001}, {'params':[logZ], 'lr':0.01} ])
    logZ.requires_grad_()
    losses_TB = []
    zs_TB = []
    rewards_TB = []
    l1log_TB = []
    cur_model = model
    proxy_model = get_proxy_model(proxy_path,gflownet_set.num_tokens,gflownet_set.proxy_max_len,args.proxy_num_layers,args.proxy_num_hid)
    proxy_model.eval()
    batch_size = params.batch_size
    max_len = params.max_length + 1
    actions_list = params.actions_list
    actions_index = params.actions_index
    actions_category = params.actions_category
    # proxy_actions_category = params.proxy_actions_category
    #n_train_steps = 1000
    n_train_steps = args.n_train_steps
    # print(x[1].shape)
    # print(judge_generated(x[0],actions_category=params.proxy_actions_category,actions_index=params.proxy_actions_index))
    # sys.exit(0)
    for it in tqdm.trange(n_train_steps):
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

        # Z_test = model(generated[:,:cur_len].to(device), lengths=gen_len.to(device))
        # #Z_test = Z_test[:,0].squeeze(1).exp().to(device)
        # Z_test = Z_test.sum(dim=1).squeeze(1).exp().to(device)
        # print(Z_test)

        Z = logZ.exp()

        flag = True
        if flag :
            # detached form  of TB
            ll_diff = torch.zeros((batch_size,)).to(device)
            ll_diff += logZ
        else :
            # non-detached form of TB ojective, where we multiply everything before doing the logarithm
            in_probs = torch.ones(batch_size, dtype=torch.float, requires_grad=True).to(device)

        while cur_len < max_len:
            state = generated[:,:cur_len] + 0 # (bs, cur_len)
            tensor = model(state.to(device), lengths=gen_len.to(device)) # (bs, cur_len, vocab_size)
            # print(tensor)
            #scores = tensor[:,0] # (bs, vocab_size) : use last word for prediction
            scores = tensor.sum(dim=1) # (bs, vocab_size)
            
            # fixed length generation
            cur_action_index = actions_index[actions_category[cur_len-1]]
            
            scores = scores.log_softmax(1)
            
            sample_temperature = 100
            
            # scores = softmax_norm(scores,batch_size,params.n_words)
            # break
            probs = F.softmax(scores / sample_temperature, dim=1)
            # print(cur_action_index)
            for index in range(0,cur_action_index[0]):
                probs[:,index] = 0
            for index in range(cur_action_index[1],len(actions_list)):
                probs[:,index] = 0
            # probs = torch.where(torch.isnan(probs),torch.full_like(probs,1e-8),probs)
            try:
                next_words = torch.multinomial(probs, 1).squeeze(1)
                #print(next_words)
            except:
                nan_flag = True
                break      
            
            # update generations / lengths / finished sentences / current length
            generated[:,cur_len] = next_words.cpu() * unfinished_sents + params.pad_index * (1 - unfinished_sents)
            gen_len.add_(unfinished_sents) # add 1 to the length of the unfinished sentences
            unfinished_sents.mul_(next_words.cpu().ne(params.eos_index).long()) # as soon as we generate <EOS>, set unfinished_sents to 0
            cur_len = cur_len + 1

            # loss
            if flag :
                #sample_in_probs = probs.gather(1, next_words.unsqueeze(-1)).squeeze(1)
                #sample_in_probs[unfinished_sents == 0] = 1.
                #ll_diff += sample_in_probs.log()
                
                ll_diff += scores.gather(1, next_words.unsqueeze(-1)).squeeze(1)
            else :
                sample_in_probs = probs.gather(1, next_words.unsqueeze(-1)).squeeze(1)
                sample_in_probs[unfinished_sents == 0] = 1.
                in_probs = in_probs * sample_in_probs
        
            # stop when there is a <EOS> in each sentence, or if we exceed the maximul length
            if unfinished_sents.max() == 0:
                break
        if nan_flag == True:
            torch.save(model, save_ckpt_path)
            nan_flag = False
            continue

        generated = generated.apply_(lambda index : 0 if index == params.pad_index or index == params.eos_index else index)
        #R = reward_function(generated, reward_coef, lambda_, beta).to(device)
        # generated =  [float("".join([str(s_i) for s_i in s])) for s in generated.tolist()]
        # R = reward_function22(generated, reward_coef, lambda_, beta).to(device) 
        flag_list = []
        
        
        generated = generated[:,1:]
        for single in generated:
            flag_list.append(judge_generated(single,actions_category=actions_category,actions_index=actions_index))
        flag_index = 0
        
            
        R = proxy_model(generated)
        for r in R:
            # print(flag_index)
            if flag_list[flag_index] == True:
                flag_index = flag_index + 1
                continue
            else:
                R[flag_index] = 1e-8
                flag_index = flag_index + 1
                continue
        optim.zero_grad()
        if flag :
            ll_diff -= R.log().to(device)
            loss = (ll_diff**2).sum()/batch_size
        else :
            Z = Z.to(device)
            in_probs = in_probs.to(device)
            R = R.to(device)
            loss = ((Z*in_probs / R).log()**2).sum()/batch_size
        R = R.detach()
        loss.backward()
        optim.step()

        losses_TB.append(loss.item())
        zs_TB.append(Z.item())
        rewards_TB.append(R.mean().cpu())
        
        it = it + batch_size

        if it%100==0: 
            torch.save(model, save_ckpt_path)
            print('\nloss =', np.array(losses_TB[-100:]).mean(), 'Z =', Z.item(), "R =", np.array(rewards_TB[-100:]).mean() )


    # generating process
    samples = []
    samples.append(list(x[1].numpy()))
    model = torch.load(save_ckpt_path)
    model.eval()
    # 100 means you want to generate 100 batch_size new test data
    # since the batch_size here is 2
    # means 200 generated data
    for it in tqdm.trange(args.generated_number):
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
            # fixed length generation
            cur_action_index = actions_index[actions_category[cur_len-1]]
            scores = scores.log_softmax(1)
            sample_temperature = 1
            probs = F.softmax(scores / sample_temperature, dim=1)
            for index in range(0,cur_action_index[0]):
                probs[:,index] = 0
            for index in range(cur_action_index[1],len(actions_list)):
                probs[:,index] = 0
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
        # print(generated)
        for single in generated:
            if judge_generated(single[1:],actions_category=actions_category,actions_index=actions_index):
                samples.append(list(single[1:].numpy()))
    result = transform2json(samples, gflownet_set.proxy_actions_list)
    print("New samples {}".format(len(result)))
    # For debug
    generated_path = path_args.new_batch_path.format(session)
    with open(generated_path,'w') as wf:
        json.dump(result, wf, indent=4)
    return result

if __name__ == '__main__':
    generate_samples_with_gfn("t_junction")