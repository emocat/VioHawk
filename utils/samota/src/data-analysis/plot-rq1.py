import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
import matplotlib

if __name__ == '__main__':
    plt.rcParams["font.family"] = "Times New Roman"
    fig, ax = plt.subplots(figsize=(6, 4))

    labels = []
    data = []
    with open('RQ-1-data.txt', 'r') as f:
        for line in f:
            tokens = line.strip().split(',')
            labels.append(tokens[0])
            print(labels)
            alg_data = [float(tokens[i]) for i in range(1, len(tokens)-1)]
            data.append(alg_data)

    ax.boxplot(data, labels=labels,showmeans=True)


    ax.set_ylabel('Size',fontsize=10)
    ax.set_xlabel('Size', fontsize=10)
    matplotlib.pyplot.yticks(fontsize=12)
    matplotlib.pyplot.xticks(fontsize=12)
    axes = plt.gca()

    ax.set_ylabel('LSE')
    ax.set_xlabel('LS Configuration')
    plt.show()
    fig.savefig('RQ1.pdf',bbox_inches='tight', dpi=300)
