import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
from matplotlib.collections import LineCollection
import numpy as np
import os

def render_3d_animation(results: dict, track, save_path: str = 'optimal_race_3d.gif'):
    """
    Renders an isometric 3D overhead animation of the prototype on the circuit, 
    color-coded by speed, and saves it to a GIF.
    """
    print("Preparing 3D Isometric circuit animation... This might take a few seconds.")
    x = track.x
    y = track.y
    v_kph = results['v'] * 3.6
    
    # 1. Coordinate scaling for 3D visibility
    # Smooth raw altitude data to remove the 'stair-step' GPS look
    window = 15
    z_raw = track.z - np.min(track.z)
    z_smooth = np.convolve(z_raw, np.ones(window)/window, mode='valid')
    z_smooth = np.pad(z_smooth, (window//2, window - 1 - window//2), mode='edge')
    
    # Dramatically reduce distortion so it looks like a realistic circuit, not a roller coaster
    Z_EXAGGERATION = 4.0
    z = z_smooth * Z_EXAGGERATION
    
    fig = plt.figure(figsize=(14, 9))
    fig.patch.set_facecolor('#1a1a1a')
    
    # 2. Main 3D Axes
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#1a1a1a')
    
    # Set isometric viewing angle
    ax.view_init(elev=35, azim=55)
    
    # Colormap for velocity
    norm = mcolors.Normalize(vmin=v_kph.min(), vmax=v_kph.max())
    cmap = plt.get_cmap('spring') 
    
    # Plot the full 3D track colored by speed
    points = np.array([x, y, z]).T.reshape(-1, 1, 3)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    # Manual loop to draw colored 3D segments since Line3DCollection can be heavy
    for i in range(len(segments)):
        seg = segments[i]
        color = cmap(norm(v_kph[i]))
        ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], color=color, linewidth=3.5)
        
    # Draw a smooth, 'holographic' curtain dropping from the track to the ground
    for i in range(0, len(x), 2):
        ax.plot([x[i], x[i]], [y[i], y[i]], [0, z[i]], color='#00FFCC', linewidth=1, alpha=0.05)

    # Base grid outline (floor shadow)
    ax.plot(x, y, np.zeros_like(x), color='#00FFCC', linewidth=2, alpha=0.2)
    
    # Colorbar definition (using a dummy mappable)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, pad=0.02, shrink=0.7)
    cbar.set_label('Prototype Speed [km/h]', color='white', fontweight='bold', fontsize=12)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    # Plot cosmetics
    padding = (x.max() - x.min()) * 0.1
    ax.set_xlim(x.min() - padding, x.max() + padding)
    ax.set_ylim(y.min() - padding, y.max() + padding)
    ax.set_zlim(0, z.max() * 1.5)
    ax.set_title('3D Topographical Optimal Strategy', color='white', fontweight='bold', fontsize=18, pad=20)
    
    # Subdue axes
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    
    # 3. Add static highlight regions for Burn and Brake zones
    u_vals = results['u']
    beta_vals = results['beta']
    
    burn_indices = np.where(u_vals[:len(x)] > 0.1)[0]
    brake_indices = np.where(beta_vals[:len(x)] > 0.1)[0]
    
    if len(burn_indices) > 0:
        ax.scatter(x[burn_indices], y[burn_indices], z[burn_indices], color='#00FFCC', s=40, zorder=3, label='Burn Zones', alpha=0.6, edgecolors='none')
    if len(brake_indices) > 0:
        ax.scatter(x[brake_indices], y[brake_indices], z[brake_indices], color='#FF3333', s=40, zorder=3, label='Brake Zones', alpha=0.6, edgecolors='none')
        
    if len(burn_indices) > 0 or len(brake_indices) > 0:
        # Overlay a 2D legend
        leg = ax.legend(loc='lower right', facecolor='#2a2a2a', edgecolor='#444444', labelcolor='white', fontsize=12)
        
    # The prototype marker
    prototype, = ax.plot([], [], [], 'o', color='cyan', markersize=12, markeredgecolor='white', markeredgewidth=1, zorder=5)
    
    # 4. Telemetry Overlay (Requires a 2D axes on top of the 3D render)
    ax2d = fig.add_axes([0, 0, 1, 1])
    ax2d.axis('off')
    telemetry_box = dict(boxstyle='round,pad=0.5', facecolor='#2a2a2a', edgecolor='#444444', alpha=0.9)
    telemetry_text = ax2d.text(0.03, 0.05, '', transform=ax2d.transAxes, color='white', 
                             fontsize=14, fontfamily='monospace', verticalalignment='bottom', bbox=telemetry_box)
    
    def init():
        prototype.set_data_3d([], [], [])
        telemetry_text.set_text('INITIALIZING...')
        return prototype, telemetry_text
        
    def update(frame):
        # Update 3D marker position
        px, py, pz = x[frame], y[frame], z[frame]
        prototype.set_data_3d([px], [py], [pz])
        
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
        prototype.set_markersize(12)
        
        if throttle > 0.1:
            status = f"BURN [{throttle*100:0.0f}%]"
            prototype.set_markerfacecolor('#00FFCC')
            prototype.set_markersize(20)  # Pulse larger
        elif brakes > 0.1:
            status = f"BRAKE [{brakes*100:0.0f}%]"
            prototype.set_markerfacecolor('#FF3333')
            prototype.set_markersize(20)
            
        slope_indicator = "▼" if slope_pct < -0.5 else ("▲" if slope_pct > 0.5 else "-")
            
        telemetry_text.set_text(
            f"TIME   : {t_current:5.1f} s\n"
            f"SPEED  : {speed_current:>4.1f} km/h\n"
            f"ELEV   : {elevation:>4.1f} m\n"
            f"GRADE  : {slope_pct:>4.1f}% {slope_indicator}\n"
            f"ACTION : {status}"
        )
        return prototype, telemetry_text
        
    # Decimate frames
    N = len(x)
    step = max(1, N // 300)
    frames = list(range(0, N, step))
    if frames[-1] != N - 1:
        frames.append(N - 1)
        
    ani = animation.FuncAnimation(fig, update, frames=frames, init_func=init, blit=False, interval=40)
    
    ext = os.path.splitext(save_path)[1].lower()
    if ext == '.gif':
        ani.save(save_path, writer='pillow', fps=25, dpi=100)
    else:
        ani.save(save_path, fps=25, dpi=100)
        
    plt.close()
    print(f"Animation successfully rendered and saved to: {os.path.abspath(save_path)}")

def render_2d_animation(results: dict, track, save_path: str = 'optimal_race_2d.gif'):
    """
    Renders an overhead 2D animation of the prototype on the circuit, 
    color-coded by speed, and saves it to a GIF.
    """
    print("Preparing 2D overhead circuit animation... This might take a few seconds.")
    x = track.x
    y = track.y
    v_kph = results['v'] * 3.6
    
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#1a1a1a')
    
    # Colormap for velocity
    norm = mcolors.Normalize(vmin=v_kph.min(), vmax=v_kph.max())
    cmap = plt.get_cmap('spring') 
    
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
        
    u_vals = results['u']
    beta_vals = results['beta']
    
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
        
    # Decimate frames
    N = len(x)
    step = max(1, N // 300)
    frames = list(range(0, N, step))
    if frames[-1] != N - 1:
        frames.append(N - 1)
        
    ani = animation.FuncAnimation(fig, update, frames=frames, init_func=init, blit=False, interval=40)
    
    ext = os.path.splitext(save_path)[1].lower()
    if ext == '.gif':
        ani.save(save_path, writer='pillow', fps=25, dpi=100)
    else:
        # Wait for fallback
        ani.save(save_path, fps=25, dpi=100)
        
    plt.close()
    print(f"Animation successfully rendered and saved to: {os.path.abspath(save_path)}")
