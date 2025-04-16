class DPContract:
    def __init__(self, received_setpoint, actual_vessel_state, setpoint_valid,
                 thruster_feedback_status, position_threshold):
        """
        Parameters:
        - received_setpoint: Desired vessel state (position, heading) from MPCS
        - actual_vessel_state: Actual state of the vessel (η, ν)
        - setpoint_valid: Boolean indicating if received setpoint is complete and well-formed
        - thruster_feedback_status: Whether thruster system successfully executes allocation
        - position_threshold: Acceptable error margin for deviation
        """
        self.received_setpoint = received_setpoint
        self.actual_vessel_state = actual_vessel_state
        self.setpoint_valid = setpoint_valid
        self.thruster_feedback_status = thruster_feedback_status
        self.position_threshold = position_threshold

        self.contract_status = {
            'A1': None,
            'A2': None,
            'G1': None
        }

    # --- Assumptions ---
    def check_A1_receives_valid_setpoint(self):
        self.contract_status['A1'] = self.setpoint_valid and self.received_setpoint is not None
        return self.contract_status['A1']

    def check_A2_thrusters_functional(self):
        self.contract_status['A2'] = self.thruster_feedback_status
        return self.contract_status['A2']

    # --- Guarantee ---
    def check_G1_follow_setpoint(self):
        import numpy as np

        if not all([self.contract_status['A1'], self.contract_status['A2']]):
            self.contract_status['G1'] = None
            return None

        deviation = np.linalg.norm(self.actual_vessel_state - self.received_setpoint)
        self.contract_status['G1'] = deviation <= self.position_threshold
        return self.contract_status['G1']

    # --- Evaluate ---
    def evaluate(self):
        self.check_A1_receives_valid_setpoint()
        self.check_A2_thrusters_functional()
        self.check_G1_follow_setpoint()
        return self.contract_status
