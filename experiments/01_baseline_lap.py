import sys
import os

# Add the project root to the python path to allow direct execution
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Internal module imports
from vortex.core.track import Track
from vortex.utils.config import load_config
from vortex.optimization.solver import OptimalControlSolver
from vortex.visualization.plotting import plot_trajectory
from vortex.visualization.animation import render_animation

def main():
    print("Welcome to VORTEX Optimal Control Engine\n")
    
    # 1. Load Declarative Configuration
    config_path = os.path.join(project_root, 'configs', 'vehicle_v1.yaml')
    print(f"Loading vehicle specifications from: {config_path}")
    config = load_config(config_path)
    
    # 2. Parse the Track topography
    track_path = os.path.join(project_root, 'data', 'raw', 'NOGARO.data')
    print(f"Parsing Track topology and computing gradients for: {track_path}")
    track = Track(track_path)
    
    # 3. Formulate and solve the Non-Linear Program
    print("\n[OPTIMIZER] Assembling CasADi Optimal Control Matrix (PMP via Direct Collocation)...")
    solver = OptimalControlSolver(config, track)
    
    # Execute the solver
    results = solver.solve()
    
    # 4. Generate visual validation
    results_dir = os.path.join(project_root, 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    plot_path = os.path.join(results_dir, 'optimal_trajectory.png')
    print("\n[VISUALIZATION] Rendering Strategy...")
    plot_trajectory(results, track, save_path=plot_path)
    
    ani_path = os.path.join(results_dir, 'optimal_race.gif')
    print("\n[VISUALIZATION] Rendering Circuit Animation (GIF)...")
    render_animation(results, track, save_path=ani_path)
    
    print("\nExperiment Workflow Completed Successfully.")

if __name__ == '__main__':
    main()
