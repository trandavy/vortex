import numpy as np
import os

class Track:
    def __init__(self, filepath: str):
        """
        Loads the track definition from the legacy .data format.
        Expected format:
        X \t Y \t Dist \t Z
        """
        self.filepath = filepath
        self.s = []
        self.x = []
        self.y = []
        self.z = []
        
        self._load_data()
        self._compute_derivatives()
        
    def _load_data(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Track file not found: {self.filepath}")
            
        with open(self.filepath, 'r') as f:
            lines = f.readlines()
            
        cumulative_s = 0.0
        for line in lines:
            if line.startswith('#') or len(line.strip()) < 4:
                continue
            parts = line.strip().split('\t')
            
            # format: X, Y, Delta S, Z
            x_val = float(parts[0])
            y_val = float(parts[1])
            ds = float(parts[2])
            z_val = float(parts[3])
            
            cumulative_s += ds
            self.s.append(cumulative_s)
            self.x.append(x_val)
            self.y.append(y_val)
            self.z.append(z_val)
            
        self.s = np.array(self.s)
        self.x = np.array(self.x)
        self.y = np.array(self.y)
        self.z = np.array(self.z)
        
    def _compute_derivatives(self):
        """
        Computes slope (theta) and curvature along the track.
        """
        self.dz_ds = np.gradient(self.z, self.s)
        self.theta = np.arctan(self.dz_ds)
        
        # Compute curvature: k = |dx*d2y - dy*d2x| / (dx^2 + dy^2)^(3/2)
        dx_ds = np.gradient(self.x, self.s)
        dy_ds = np.gradient(self.y, self.s)
        d2x_ds2 = np.gradient(dx_ds, self.s)
        d2y_ds2 = np.gradient(dy_ds, self.s)
        
        numerator = np.abs(dx_ds * d2y_ds2 - dy_ds * d2x_ds2)
        denominator = (dx_ds**2 + dy_ds**2)**1.5 + 1e-8
        
        self.curvature = numerator / denominator
