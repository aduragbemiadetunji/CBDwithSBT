class SITAWContract:
    def __init__(self, vessel_state_estimate, disturbance_estimate, true_vessel_state,
                 true_disturbances, accuracy_thresholds):
        """
        Parameters:
        - vessel_state_estimate: Estimated vessel state from observer (η, ν)
        - disturbance_estimate: Estimated environmental forces (wind, wave, current)
        - true_vessel_state: Ground truth vessel state for verification
        - true_disturbances: Ground truth environmental values for verification
        - accuracy_thresholds: Dict with acceptable error bounds {'state': x, 'disturbance': y}
        """
        self.vessel_state_estimate = vessel_state_estimate
        self.disturbance_estimate = disturbance_estimate
        self.true_vessel_state = true_vessel_state
        self.true_disturbances = true_disturbances
        self.accuracy_thresholds = accuracy_thresholds

        self.contract_status = {
            'A1': None,
            'G1': None,
            'G2': None
        }

    # --- Assumptions ---
    def check_A1_observable_conditions(self):
        # In simulation we assume visibility/observability holds if true values are known
        self.contract_status['A1'] = self.true_vessel_state is not None and self.true_disturbances is not None
        return self.contract_status['A1']

    # --- Guarantees ---
    def check_G1_disturbance_estimation_accuracy(self):
        import numpy as np
        if not self.contract_status['A1']:
            self.contract_status['G1'] = None
            return None

        error = np.linalg.norm(self.disturbance_estimate - self.true_disturbances)
        self.contract_status['G1'] = error <= self.accuracy_thresholds['disturbance']
        return self.contract_status['G1']

    def check_G2_vessel_state_estimation_accuracy(self):
        import numpy as np
        if not self.contract_status['A1']:
            self.contract_status['G2'] = None
            return None

        error = np.linalg.norm(self.vessel_state_estimate - self.true_vessel_state)
        self.contract_status['G2'] = error <= self.accuracy_thresholds['state']
        return self.contract_status['G2']

    # --- Evaluate ---
    def evaluate(self):
        self.check_A1_observable_conditions()
        self.check_G1_disturbance_estimation_accuracy()
        self.check_G2_vessel_state_estimation_accuracy()
        return self.contract_status
