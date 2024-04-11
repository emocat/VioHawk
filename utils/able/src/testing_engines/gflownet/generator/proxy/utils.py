from sklearn.metrics import mean_absolute_error
import torch
import os
import shutil
import time
import numpy as np
from .proxy_config import proxy_args

def save_ckpt(state, is_best, model_save_dir):
    current_w = os.path.join(model_save_dir, proxy_args.current_w)
    best_w = os.path.join(model_save_dir, proxy_args.best_w)
    torch.save(state, current_w)
    if is_best: shutil.copyfile(current_w, best_w)

def cal_mean_error(y_true,y_pred):
    y_true = y_true.view(-1).cpu().detach().numpy().astype(float)
    y_pred = y_pred.view(-1).cpu().detach().numpy().astype(float)
    return mean_absolute_error(y_true, y_pred)

def mkdirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

# adjust learning rate 
def adjust_learning_rate(optimizer, lr):
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr
    return lr

def print_time_cost(since):
    time_elapsed = time.time() - since
    return '{:.0f}m{:.0f}s\n'.format(time_elapsed // 60, time_elapsed % 60)