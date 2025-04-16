class ThrustAllocationContract:
    def __init__(self, requested_force_vector, thruster_config, allocation_success,
                 allocation_error, allocation_threshold):
        """
        Parameters:
        - requested_force_vector: Desired global force/moment (from DP system)
        - thruster_config: Current thruster configuration (layout, availability)
        - allocation_success: Boolean flag indicating if allocation succeeded
        - allocation_error: Error between requested and actual allocated force
        - allocation_threshold: Maximum allowable allocation error
        """
        self.requested_force_vector = requested_force_vector
        self.thruster_config = thruster_config
        self.allocation_success = allocation_success
        self.allocation_error = allocation_error
        self.allocation_threshold = allocation_threshold

        self.contract_status = {
            'A1': None,
            'A2': None,
            'G1': None
        }

    # --- Assumptions ---
    def check_A1_thruster_model_available(self):
        self.contract_status['A1'] = self.thruster_config is not None and len(self.thruster_config) > 0
        return self.contract_status['A1']

    def check_A2_stable_allocation_method(self):
        self.contract_status['A2'] = self.allocation_success
        return self.contract_status['A2']

    # --- Guarantee ---
    def check_G1_force_allocation_accuracy(self):
        import numpy as np

        if not all([self.contract_status['A1'], self.contract_status['A2']]):
            self.contract_status['G1'] = None
            return None

        error_magnitude = np.linalg.norm(self.allocation_error)
        # print(error_magnitude)
        self.contract_status['G1'] = error_magnitude <= self.allocation_threshold
        return self.contract_status['G1']

    # --- Evaluate ---
    def evaluate(self):
        self.check_A1_thruster_model_available()
        self.check_A2_stable_allocation_method()
        self.check_G1_force_allocation_accuracy()
        return self.contract_status
