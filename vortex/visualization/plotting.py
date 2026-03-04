import matplotlib.pyplot as plt
import numpy as np
import os

def plot_trajectory(results: dict, track, save_path: str = 'optimal_trajectory.pdf'):
    """
    Renders publication-quality multi-pane plots of the optimal route configuration.
    """
    s = results['s']
    v_kph = results['v'] * 3.6
    u = results['u']
    beta = results['beta']
    z = track.z
    
    fig, axs = plt.subplots(3, 1, figsize=(14, 10), sharex=True, gridspec_kw={'height_ratios': [1, 2, 1]})
    
    # Track Elevation context
    axs[0].plot(s, z, color='black', lw=2, label='Track Elevation')
    axs[0].set_ylabel('Elevation [m]', fontweight='bold')
    axs[0].grid(True, alpha=0.3)
    axs[0].legend(loc='upper right')
    axs[0].set_title('Optimal Control Trajectory Strategy', fontsize=16, fontweight='bold')
    
    # Velocity bounds and output
    axs[1].plot(s, v_kph, color='red', lw=2, label='Velocity Profile')
    axs[1].axhline(y=25.0, color='gray', linestyle='--', label='Min Average Speed (25 km/h)')
    axs[1].fill_between(s, 0, v_kph, color='red', alpha=0.1)
    axs[1].set_ylabel('Speed [km/h]', fontweight='bold')
    axs[1].grid(True, alpha=0.3)
    axs[1].legend(loc='upper right')
    
    # Actions (Throttle vs Braking)
    axs[2].plot(s, u, color='blue', label='Throttle Command (u)', lw=1.5)
    axs[2].fill_between(s, 0, u, color='blue', alpha=0.3)
    axs[2].plot(s, -beta, color='orange', label='Braking Command (beta)', lw=1.5)
    axs[2].fill_between(s, 0, -beta, color='orange', alpha=0.3)
    axs[2].set_xlabel('Track Distance [m]', fontweight='bold')
    axs[2].set_ylabel('Control Effort [-1, 1]', fontweight='bold')
    axs[2].grid(True, alpha=0.3)
    axs[2].legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Publication figure rendered to: {os.path.abspath(save_path)}")
