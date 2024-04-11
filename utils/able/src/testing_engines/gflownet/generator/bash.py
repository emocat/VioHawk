import os 
import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", type=str, help="the path of train_data")
    command_args = parser.parse_args()
    os.system("python3 proxy/train.py --data_path %s" %(command_args.data_path))
    os.system("python3 main.py --data_path %s" %(command_args.data_path))
