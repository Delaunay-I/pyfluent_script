import numpy as np
import matplotlib.pyplot as plt

def read_resNorm(filename):
    # Read the data from the file
    with open(filename) as file:
        content = file.read()

    # Split the content into blocks (continuity, x-velocity, y-velocity)
    blocks = content.strip().split('\n\n')

    # Function to extract the values
    def extract_values(block):
        lines = block.split('\n')[1:-1]
        return [float(line.split('\t')[1]) for line in lines]

    # Extract the values
    continuity = extract_values(blocks[0])
    x_velocity = extract_values(blocks[1])
    y_velocity = extract_values(blocks[2])

    # Combine into a matrix
    residuals = np.column_stack((continuity, x_velocity, y_velocity))

    return residuals


def plot_residuals():
    res_regular = read_resNorm('./out/res/naca0012_res.plt')
    res_acc = read_resNorm('./out/res/naca_SIMPLE_res.plt')
    # res_acc1 = read_resNorm('./out/res/naca0012DMDi550_s100_m25_res.plt')
    # res2 = read_resNorm('./out/res/naca0012DMDi550_s25_m24_res.plt')


    figure = plt.figure(figsize=(8,6), dpi=120)

    # color = 'darkgreen'
    # style = 'dashdot'
    # opacity = .75
    # preLabel = "s25-m24"
    # plt.plot(res2[:, 0], color=color, linestyle=style, alpha=opacity, label=preLabel)
    # plt.plot(res2[:, 1], color=color, linestyle=style, alpha=opacity)
    # plt.plot(res2[:, 2], color=color, linestyle=style, alpha=opacity)

    color = 'magenta'
    style = ':'
    opacity = .75
    preLabel = "s100-m9"
    plt.plot(res_acc[:, 0], color=color, linestyle=style, alpha=opacity, label=preLabel)
    plt.plot(res_acc[:, 1], color=color, linestyle=style, alpha=opacity)
    plt.plot(res_acc[:, 2], color=color, linestyle=style, alpha=opacity)

    # preLabel = "s100-m25"
    # plt.plot(res_acc1[:, 0], color='darkblue', linestyle='-.')
    # plt.plot(res_acc1[:, 1], color='darkblue', linestyle='-.')
    # plt.plot(res_acc1[:, 2], color='darkblue', linestyle='-.', label=preLabel)

    plt.plot(res_regular[:, 0], label='continuity', color='peru')
    plt.plot(res_regular[:, 1], label='x-velocity', color='dodgerblue')
    plt.plot(res_regular[:, 2], label='y-velocity', color='k')

    plt.xlabel('Iteration')
    plt.ylabel("Residuals")
    plt.grid(True, alpha=0.5, linestyle='--')
    plt.legend()

    plt.yscale('log')
    # plt.ylim(10**-12, 10**0)

    plt.tight_layout()
    # plt.savefig("C:\\Users\\amirshah\OneDrive - ANSYS, Inc\\Pictures\\fig1.png", dpi=180)
    plt.show()


def plot_mode_progression():
    res = read_resNorm('./out/res/naca0012_res.plt')
    all_amps = np.loadtxt('naca_SIMPLEDMDi200_s25_m9_singularvalues_s25_m9.csv')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    color = 'k'
    style = '-'
    opacity = 1
    ax1.plot(res[1:, 0], label='continuity', color=color, linestyle=style, alpha=opacity)
    ax1.plot(res[1:, 1], label='x-velocity', color=color, linestyle=style, alpha=opacity)
    ax1.plot(res[1:, 2], label='y-velocity', color=color, linestyle=style, alpha=opacity)

    ax1.set_xlabel('Iteration')
    ax1.set_ylabel("Residuals")
    ax1.set_title('Convergence history')
    ax1.grid(True, alpha=0.5, linestyle='--')
    ax1.set_yscale('log')
    ax1.legend()
    
    
    for i in range(all_amps.shape[1]):
        ax2.plot(np.arange(25 + 1, 1501), all_amps[:, i], marker='o', markersize=2, lw=1, label=f"mode {i}")
    
    # ax2.axhline(y=1, color='k', linestyle='--', lw=.75)

    ax2.set_xlabel('Iteration')
    ax2.set_ylabel("Singular values (normalized)")
    ax2.set_title('Singular values at different iterations')
    ax2.grid(True, alpha=0.5, linestyle='--')
    ax2.set_ylim(1e-9, 1e3)
    ax2.legend(prop={'size': 6})
    ax2.set_yscale('log')

    plt.suptitle('snaps: 25    modes: 9')
    plt.tight_layout()
    plt.savefig("C:\\Users\\amirshah\\OneDrive - ANSYS, Inc\\Desktop\\results\\fig1.png", dpi=180)
    plt.show()

def plot_time_dynamics_and_eigs():
    fig, ((ax1, ax2) , (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))

    res_regular = read_resNorm('./out/res/naca0012_res.plt')
    res_acc = read_resNorm('./out/res/naca_SIMPLE_res.plt')

    color = 'magenta'
    style = ':'
    opacity = .75
    preLabel = "s100-m51"
    ax1.plot(res_acc[:, 0], color=color, linestyle=style, alpha=opacity, label=preLabel)
    ax1.plot(res_acc[:, 1], color=color, linestyle=style, alpha=opacity)
    ax1.plot(res_acc[:, 2], color=color, linestyle=style, alpha=opacity)

    ax1.plot(res_regular[:, 0], label='continuity', color='peru')
    ax1.plot(res_regular[:, 1], label='x-velocity', color='dodgerblue')
    ax1.plot(res_regular[:, 2], label='y-velocity', color='k')

    ax1.set_ylim(10**-12, 10**0)
    ax1.set_title("Convergence History")
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel("Residuals")
    ax1.grid(True, alpha=0.25, linestyle='--')
    ax1.legend(loc='lower left')
    ax1.set_yscale('log')

    nModes = 51
    singularvalues = np.loadtxt("solver_data/singularvalues.csv")
    x_valuse = np.arange(len(singularvalues[:nModes]))

    ax2.semilogy(singularvalues[:nModes]/singularvalues[0], marker='o', markersize=2, lw=0.5, label='ratios - normalized')
    ax2.scatter(x_valuse, singularvalues[:nModes], label="Values", s=1.2, c='k')
    ax2.set_xlabel("Number")
    ax2.set_ylabel("Magnitude")
    ax2.set_title("normalized Singular values")
    ax2.grid(True, alpha=0.25, linestyle='--')
    ax2.legend(fontsize=9)

    td = np.loadtxt("solver_data/time_dynamics2.csv")
    td =  np.absolute(td)

    for i in range(0, td.shape[-1], 2):
        if i <= 10:
            ax3.semilogy(td[:, i], label=f'Mode {i}')
        else:
            ax3.semilogy(td[:, i], label=f'Mode {i}', color='lightslategray', alpha=0.6)

    ax3.axhline(y=0.1, color='k', linestyle='--', lw=.75)
    ax3.set_xlabel("iterations")
    ax3.set_ylabel("error norm")
    ax3.set_title("convergence prediction of DMD modes")
    ax3.grid(True, alpha=0.25, linestyle='--')
    # ax3.legend(fontsize=6)


    theta = np.linspace(0, 2 * np.pi, 100)  # 100 points evenly spaced from 0 to 2*pi
    x = np.cos(theta)
    y = np.sin(theta)
    plt.plot(x, y, c='gray', lw=0.5)

    amps = np.loadtxt("solver_data/amps.csv", dtype=complex)
    amp_real = amps.real
    amp_img = amps.imag
    for i in range(0, amp_img.shape[0], 2):
        if i <= 10:
            ax4.scatter(x=amp_real[i:i+2], y=amp_img[i:i+2], label=f'Mode {i}', s=5)
        else:
            ax4.scatter(x=amp_real[i:i+2], y=amp_img[i:i+2], label=f'Mode {i}', s=5, color='dimgray', alpha=0.75)

    ax4.axis('equal')
    ax4.set_xlabel('Real')
    ax4.set_ylabel("imag")
    ax4.grid(True, alpha=0.25, linestyle='--')
    ax4.set_title("Amplification factors of dominant DMD modes")
    # ax4.legend(fontsize=6)

    plt.tight_layout()
    plt.savefig('solver_data/plots/DMD_mode_analysis.png', dpi=300)
    plt.show()

def plot_eigs():
    fig = plt.figure(figsize=(8, 5), dpi=180)
    theta = np.linspace(0, 2 * np.pi, 100)  # 100 points evenly spaced from 0 to 2*pi
    x = np.cos(theta)
    y = np.sin(theta)
    plt.plot(x, y, c='gray', lw=0.5)

    amps = np.loadtxt("error/eigs32.txt", dtype=complex)
    amp_real = amps.real
    amp_img = amps.imag
    for i in range(0, amp_img.shape[0], 2):
        plt.scatter(x=amp_real[i:i+2], y=amp_img[i:i+2], label=f'Mode {i}', s=5)

    plt.axis('equal')
    plt.xlabel('Real')
    plt.ylabel("imag")
    plt.grid(True, alpha=0.25, linestyle='--')
    plt.title("Amplification factors of dominant DMD modes")
    plt.legend()

    # plt.savefig('results/dmd time-dynamics predicted.png', dpi=300)
    plt.show()

# plot_residuals()
# plot_mode_progression()

plot_time_dynamics_and_eigs()
# plot_eigs()
