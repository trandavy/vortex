import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
from vortex.core.track import Track
from vortex.utils.config import load_config
from vortex.optimization.solver import OptimalControlSolver
from vortex.visualization.plotting import plot_trajectory
from vortex.visualization.animation import render_2d_animation, render_3d_animation

def main():
    print("Welcome to VORTEX Optimal Control Engine\n")
    
    # Load Declarative Configuration
    config_path = os.path.join(project_root, 'configs', 'vehicle_v1.yaml')
    print(f"Loading vehicle specifications from: {config_path}")
    config = load_config(config_path)
    
    # Parse the Track topography
    track_path = os.path.join(project_root, 'data', 'raw', 'NOGARO.data')
    print(f"Parsing Track topology and computing gradients for: {track_path}")
    track = Track(track_path)
    
    # Formulate and solve the Non-Linear Program
    print("\n[OPTIMIZER] Assembling CasADi Optimal Control Matrix (PMP via Direct Collocation)...")
    solver = OptimalControlSolver(config, track)
    
    # Execute the solver
    results = solver.solve()
    
    # Generate visual validation
    results_dir = os.path.join(project_root, 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    plot_path = os.path.join(results_dir, 'optimal_trajectory.png')
    print("\n[VISUALIZATION] Rendering Strategy...")
    plot_trajectory(results, track, save_path=plot_path)
    
    ani_2d_path = os.path.join(results_dir, 'optimal_race_2d.gif')
    print("\n[VISUALIZATION] Rendering 2D Circuit Animation (GIF)...")
    render_2d_animation(results, track, save_path=ani_2d_path)
    
    ani_3d_path = os.path.join(results_dir, 'optimal_race_3d.gif')
    print("\n[VISUALIZATION] Rendering 3D Isometric Circuit Animation (GIF)...")
    render_3d_animation(results, track, save_path=ani_3d_path)
    
    print("\nExperiment Workflow Completed Successfully.")

if __name__ == '__main__':
    main()
