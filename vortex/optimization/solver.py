import casadi as ca
import numpy as np

class OptimalControlSolver:
    def __init__(self, config: dict, track):
        self.config = config
        self.track = track
        
        # Vehicle properties
        # Vehicle properties
        self.mass = config['vehicle']['mass']['prototype_kg'] + config['vehicle']['mass']['pilot_kg']
        self.mass_eff = self.mass * float(config['vehicle']['mass'].get('rotational_inertia_factor', 1.05))
        self.S = float(config['vehicle']['aerodynamics']['frontal_area_m2'])
        self.Cx = float(config['vehicle']['aerodynamics']['drag_coefficient_cx'])
        self.Crr = float(config['vehicle']['tires']['rolling_resistance_crr'])
        self.cornering_stiffness = float(config['vehicle']['tires'].get('cornering_stiffness_N_rad', 25000.0))
        self.optimal_throttle = float(config['vehicle'].get('engine', {}).get('optimal_throttle', 0.8))
        
        # Environmental
        self.g = float(config['environment']['gravity_mps2'])
        self.rho = float(config['environment']['air_density_kgpm3'])
        
        # Control Limits
        self.F_prop_max = 200.0  # N
        self.F_brake_max = 500.0  # N
        
        # Performance Constraints
        self.v_avg_min_kph = float(self.config['optimization']['target_average_speed_kph'])
        self.v_avg_min = self.v_avg_min_kph / 3.6
        self.v_min = 10.0 / 3.6  # Cannot go below this speed safely in simulation limits
        self.v_max = float(self.config['optimization']['max_start_speed_kph']) / 3.6
        
    def solve(self):
        s_nodes = self.track.s
        N = len(s_nodes) - 1  # Number of intervals
        
        opti = ca.Opti()
        
        # State variables
        v = opti.variable(N+1) # Velocity [m/s]
        t = opti.variable(N+1) # Time Elapsed [s]
        
        # Control variables (constant over each interval ds)
        u = opti.variable(N)    # Throttle Command [0, 1]
        beta = opti.variable(N) # Brake Command [0, 1]
        
        # Cost function base (Fuel Energy ~ Mechanical Energy output)
        cost = 0
        
        # Bounds on variables
        opti.subject_to(opti.bounded(self.v_min, v, self.v_max))
        opti.subject_to(opti.bounded(0, u, 1))
        opti.subject_to(opti.bounded(0, beta, 1))
        
        # Initial boundary conditions
        opti.subject_to(t[0] == 0)
        # Ensure a 'flying lap' periodic cycle velocity
        opti.subject_to(v[0] == v[N])
        
        # Direct multiple shooting / collocation formulation over distance instead of time
        for k in range(N):
            ds = s_nodes[k+1] - s_nodes[k]
            # Avoid division checks for stacked identical waypoints
            if ds < 1e-4:
                ds = 1e-4
            
            # Sub-states
            v_k = v[k]
            v_next = v[k+1]
            u_k = u[k]
            beta_k = beta[k]
            theta_k = self.track.theta[k]
            curvature_k = self.track.curvature[k]
            
            # Cornering drag (Tire Scrub from Pacejka lateral slip)
            F_y = self.mass * v_k**2 * curvature_k
            F_scrub = (F_y**2) / self.cornering_stiffness
            
            # Physics calculations
            F_drag = 0.5 * self.rho * self.Cx * self.S * v_k**2 + F_scrub
            F_roll = self.g * self.mass * (self.Crr / 1000.0)
            F_g = self.mass * self.g * ca.sin(theta_k)
            
            F_prop = u_k * self.F_prop_max
            F_brake = beta_k * self.F_brake_max
            
            F_net = F_prop - F_drag - F_roll - F_g - F_brake
            
            # Work-Energy Theorem: Delta Kinetic Energy = Work Done by Net Force
            # 1/2 * m_eff * v_{k+1}^2 - 1/2 * m_eff * v_{k}^2 = F_{net} * ds
            Ek = 0.5 * self.mass_eff * v_k**2
            Ek_next = 0.5 * self.mass_eff * v_next**2
            
            opti.subject_to(Ek_next == Ek + F_net * ds)
            
            # Time Integration (Trapezoidal Rule)
            # dt = 2 * ds / (v_k + v_next)
            opti.subject_to(t[k+1] == t[k] + 2 * ds / (v_k + v_next))
            
            # Accumulate equivalent fuel energy as cost surrogate
            # Engine BSFC penalty: base + quadratic penalty for deviating from optimal throttle
            penalty = 1.0 + 2.0 * (u_k - self.optimal_throttle)**2
            cost += u_k * self.F_prop_max * ds * penalty
            
        # Hard constraint on final time to enforce minimum average speed
        S_total = s_nodes[-1]
        T_max = S_total / self.v_avg_min
        opti.subject_to(t[N] <= T_max)
        
        # Set Objective Target
        opti.minimize(cost)
        
        # Solver Settings setup
        p_opts = {"expand": True, "print_time": False}
        s_opts = {"max_iter": 3000, "print_level": 5, "tol": 1e-5}
        
        opti.solver("ipopt", p_opts, s_opts)
        
        # Seeding Initial Guesses for the gradient paths
        opti.set_initial(v, self.v_avg_min * 1.1)  # start guess at 110% of min required speed
        opti.set_initial(u, 0.1)
        opti.set_initial(beta, 0.0)
        
        try:
            sol = opti.solve()
            v_opt = sol.value(v)
            u_opt = sol.value(u)
            beta_opt = sol.value(beta)
            t_opt = sol.value(t)
            cost_opt = sol.value(cost)
            status = opti.return_status()
            
            print(f"Solver Succeeded ({status}). Equivalent Energy Cost (including engine inefficiency metrics): {cost_opt:.2f} Units")
        except Exception as e:
            print("Solver Failed to Converge. Attempting to parse partial debug solution...")
            sol = opti.debug
            v_opt = sol.value(v)
            u_opt = sol.value(u)
            beta_opt = sol.value(beta)
            t_opt = sol.value(t)
            cost_opt = sol.value(cost)
            
        # Pad control profiles mapping N intervals efficiently to N+1 nodes for plotting
        u_padded = np.append(u_opt, u_opt[-1])
        beta_padded = np.append(beta_opt, beta_opt[-1])
        
        return {
            's': s_nodes,
            'v': v_opt,
            'u': u_padded,
            'beta': beta_padded,
            't': t_opt,
            'cost': cost_opt
        }
