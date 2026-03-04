import numpy as np

class VehiclePhysics:
    def __init__(self, config: dict):
        self.mass = config['vehicle']['mass']['prototype_kg'] + config['vehicle']['mass']['pilot_kg']
        self.S = config['vehicle']['aerodynamics']['frontal_area_m2']
        self.Cx = config['vehicle']['aerodynamics']['drag_coefficient_cx']
        self.Crr = config['vehicle']['tires']['rolling_resistance_crr']
        
        self.g = config['environment']['gravity_mps2']
        self.rho = config['environment']['air_density_kgpm3']
        
    def dyn_equations(self, v, u, beta, theta, curvature):
        """
        Compute the derivative of velocity w.r.t distance (s)
        dv/ds = 1 / (m * v) * [ F_prop - F_drag - F_roll - F_g - F_brake ]
        """
        # Aerodynamic drag
        F_drag = 0.5 * self.rho * self.Cx * self.S * v**2
        
        # Rolling resistance
        F_roll = self.g * self.mass * (self.Crr / 1000.0)
        
        # Gravitational force due to slope (theta)
        F_g = self.mass * self.g * np.sin(theta)
        
        # Simplified propulsive force proportional to throttle input u
        # Assume a constant max propulsion force for this prototype phase
        F_prop_max = 200.0
        F_prop = u * F_prop_max
        
        # Braking force proportional to beta
        F_brake_max = 500.0
        F_brake = beta * F_brake_max
        
        force_net = F_prop - F_drag - F_roll - F_g - F_brake
        
        # Safe division
        v_safe = np.maximum(v, 0.1)
        dv_ds = (1.0 / (self.mass * v_safe)) * force_net
        
        # Time derivative
        dt_ds = 1.0 / v_safe
        
        # Fuel consumption (working proxy for now)
        dE_ds = (F_prop * v_safe) / v_safe 
        
        return dv_ds, dt_ds, dE_ds
