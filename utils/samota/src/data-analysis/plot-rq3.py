import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
import matplotlib
if __name__ == '__main__':
    fig, ax1 = plt.subplots(figsize=(9, 5))

    y = [i*20 for i in range(7)]
    labels = []
    data = []

    y_max = 0
    patterns =  [ 'o','.','D','x','s','go-']
    i = 0
    with open('RQ-3-data.txt', 'r') as f:
        for line in f:
            tokens = line.strip().split(',')
            alg_data = [float(tokens[i]) for i in range(1, len(tokens)-1)]
            if y_max < max(alg_data):
                y_max=max(alg_data)
            ax1.plot(y,alg_data,  marker = patterns[i],label=tokens[0])
            i = i+1
    plt.xlim([0, 120])
    plt.legend(loc='best',bbox_to_anchor=(1.0, 1),prop={'size': 14})
    plt.ylim([0, y_max+0.05])
    ax1.set_ylabel('Average TE',size = 14)
    ax1.set_xlabel('Time(min)',size = 14)

    matplotlib.pyplot.yticks(fontsize=16)
    matplotlib.pyplot.xticks(fontsize=16)

    fig.savefig('RQ3.pdf',bbox_inches='tight', dpi=1000)
