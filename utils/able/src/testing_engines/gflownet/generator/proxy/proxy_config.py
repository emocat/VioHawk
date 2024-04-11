class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
  # vocab = ["0", "1", "2", "3", "4", "5", "6", "7", "8", '9', '.', ',']    
proxy_args = AttrDict(
    {
    "resume": False, 
    # batch_size大小,这个数字理论上越大越小
    "batch_size": 128,
    # stage_epoch 每到32,64等epoch,学习率就会衰减变为原本的lr_decay分之一
    "stage_epoch":[32,64,128,256],
    "lr_decay" : 10,
    "lr":0.01,
    # 训练epoch数量
    "max_epoch" : 64,
    # saved current weight path
    "current_w" :'current_w.pth',
    # saved best weight path
    "best_w" : 'best_w.pth',
    # 神经网络本身层数,这个数字理论上越大越好
    "num_layers":16,
    # hidden_layers的神经元数量,这个参数最好不要进行修改
    "num_hid":1024
}
)