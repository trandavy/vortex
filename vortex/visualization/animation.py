import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
from matplotlib.collections import LineCollection
import numpy as np
import os

def render_animation(results: dict, track, save_path: str = 'optimal_race.gif'):
    """
    Renders an overhead 2D animation of the prototype on the circuit, 
    color-coded by speed, and saves it to a GIF.
    """
    print("Preparing circuit animation... This might take a few seconds.")
    x = track.x
    y = track.y
    v_kph = results['v'] * 3.6
    
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#1a1a1a')
    
    # Colormap for velocity (using a premium vibrant map)
    norm = mcolors.Normalize(vmin=v_kph.min(), vmax=v_kph.max())
    cmap = plt.get_cmap('spring') # Vibrant pink/yellow for speed
    
    # Plot the full track colored by speed
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    lc = LineCollection(segments, cmap=cmap, norm=norm)
    lc.set_array(v_kph[:-1])
    lc.set_linewidth(4)
    line = ax.add_collection(lc)
    
    cbar = fig.colorbar(lc, ax=ax, pad=0.02)
    cbar.set_label('Prototype Speed [km/h]', color='white', fontweight='bold', fontsize=12)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    # Plot cosmetics
    padding = (x.max() - x.min()) * 0.1
    ax.set_xlim(x.min() - padding, x.max() + padding)
    ax.set_ylim(y.min() - padding, y.max() + padding)
    ax.set_aspect('equal')
    ax.set_title('Optimal Control Trajectory Simulation', color='white', fontweight='bold', fontsize=16)
    
    # Hide standard axes for a cleaner look
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color('#333333')
        
    # Add static highlight regions for Burn and Brake zones to make them constantly readable
    u_vals = results['u']
    beta_vals = results['beta']
    
    # Ensure dimensions match x
    burn_indices = np.where(u_vals[:len(x)] > 0.1)[0]
    brake_indices = np.where(beta_vals[:len(x)] > 0.1)[0]
    
    if len(burn_indices) > 0:
        ax.scatter(x[burn_indices], y[burn_indices], color='#00FFCC', s=80, zorder=3, label='Burn Zones', alpha=0.8, edgecolors='white', linewidths=0.5)
    if len(brake_indices) > 0:
        ax.scatter(x[brake_indices], y[brake_indices], color='#FF3333', s=80, zorder=3, label='Brake Zones', alpha=0.8, edgecolors='white', linewidths=0.5)
        
    if len(burn_indices) > 0 or len(brake_indices) > 0:
        ax.legend(loc='lower right', facecolor='#2a2a2a', edgecolor='#444444', labelcolor='white', fontsize=12)
        
    # The prototype marker
    prototype, = ax.plot([], [], 'o', color='cyan', markersize=14, markeredgecolor='white', markeredgewidth=2, zorder=5)
    
    # Telemetry overlay
    telemetry_box = dict(boxstyle='round,pad=0.5', facecolor='#2a2a2a', edgecolor='#444444', alpha=0.9)
    telemetry_text = ax.text(0.03, 0.05, '', transform=ax.transAxes, color='white', 
                             fontsize=14, fontfamily='monospace', verticalalignment='bottom', bbox=telemetry_box)
    
    def init():
        prototype.set_data([], [])
        telemetry_text.set_text('INITIALIZING...')
        return prototype, telemetry_text
        
    def update(frame):
        # Update marker position
        px, py = x[frame], y[frame]
        prototype.set_data([px], [py])
        
        # Update telemetry
        t_current = results['t'][frame]
        speed_current = v_kph[frame]
        throttle = results['u'][frame]
        brakes = results['beta'][frame]
        
        # Topography data
        elevation = track.z[frame]
        slope_pct = track.dz_ds[frame] * 100.0 # Grade percentage
        
        status = "COAST"
        prototype.set_markerfacecolor('cyan')
        prototype.set_markersize(14)
        
        if throttle > 0.1:
            status = f"BURN [{throttle*100:0.0f}%]"
            prototype.set_markerfacecolor('#00FFCC')
            prototype.set_markersize(24)  # Make marker pulse larger
        elif brakes > 0.1:
            status = f"BRAKE [{brakes*100:0.0f}%]"
            prototype.set_markerfacecolor('#FF3333')
            prototype.set_markersize(24)
            
        slope_indicator = "▼" if slope_pct < -0.5 else ("▲" if slope_pct > 0.5 else "-")
            
        telemetry_text.set_text(
            f"TIME   : {t_current:5.1f} s\n"
            f"SPEED  : {speed_current:>4.1f} km/h\n"
            f"ELEV   : {elevation:>4.1f} m\n"
            f"GRADE  : {slope_pct:>4.1f}% {slope_indicator}\n"
            f"ACTION : {status}"
        )
        return prototype, telemetry_text
        
    # Decimate frames to keep GIF generation fast and file size reasonable (max ~300 frames)
    N = len(x)
    step = max(1, N // 300)
    frames = list(range(0, N, step))
    if frames[-1] != N - 1:
        frames.append(N - 1)
        
    ani = animation.FuncAnimation(fig, update, frames=frames, init_func=init, blit=True, interval=40)
    
    # Save as GIF
    ext = os.path.splitext(save_path)[1].lower()
    if ext == '.gif':
        ani.save(save_path, writer='pillow', fps=25, dpi=100)
    else:
        # Wait for fallback
        ani.save(save_path, fps=25, dpi=100)
        
    plt.close()
    print(f"Animation successfully rendered and saved to: {os.path.abspath(save_path)}")
