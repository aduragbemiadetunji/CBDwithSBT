class MPCSContract:
    def __init__(self, reference_path, vessel_state, disturbance_data, setpoints,
                 dp_feedback_status, sitaw_data_accuracy, position_threshold):
        """
        Parameters:
        - reference_path: Desired route or setpoints from mission planner
        - vessel_state: Current estimated state of the vessel (from SITAW)
        - disturbance_data: Environmental input estimates (wind, wave, current)
        - setpoints: MPCS-generated setpoints for position/heading
        - dp_feedback_status: Whether DP system successfully executes commands
        - sitaw_data_accuracy: Whether SITAW data is accurate (boolean)
        - position_threshold: Maximum allowed deviation from trajectory
        """
        self.reference_path = reference_path
        self.vessel_state = vessel_state
        self.disturbance_data = disturbance_data
        self.setpoints = setpoints
        self.dp_feedback_status = dp_feedback_status
        self.sitaw_data_accuracy = sitaw_data_accuracy
        self.position_threshold = position_threshold

        self.contract_status = {
            'A1': None, 'A2': None, 'A3': None,
            'G1': None, 'G2': None
        }

    # --- Assumptions ---
    def check_A1_reference_configured(self):
        self.contract_status['A1'] = self.reference_path is not None
        return self.contract_status['A1']

    def check_A2_data_accuracy_from_SITAW(self):
        self.contract_status['A2'] = self.sitaw_data_accuracy
        return self.contract_status['A2']

    def check_A3_dp_executes_commands(self):
        self.contract_status['A3'] = self.dp_feedback_status
        return self.contract_status['A3']

    # --- Guarantees ---
    def check_G1_setpoints_follow_path(self):
        import numpy as np

        if not all([self.contract_status[a] for a in ['A1', 'A2', 'A3']]):
            self.contract_status['G1'] = None
            return None

        deviation = np.linalg.norm(self.setpoints - self.reference_path)
        self.contract_status['G1'] = deviation <= self.position_threshold
        return self.contract_status['G1']

    def check_G2_compensates_for_disturbance(self):
        import numpy as np

        if not self.contract_status['A2']:
            self.contract_status['G2'] = None
            return None

        disturbance_magnitude = np.linalg.norm([
            self.disturbance_data.get('wind', 0),
            self.disturbance_data.get('wave', 0),
            self.disturbance_data.get('current', 0)
        ])

        self.contract_status['G2'] = disturbance_magnitude > 0 and self.setpoints is not None
        return self.contract_status['G2']

    # --- Evaluate ---
    def evaluate(self):
        self.check_A1_reference_configured()
        self.check_A2_data_accuracy_from_SITAW()
        self.check_A3_dp_executes_commands()
        self.check_G1_setpoints_follow_path()
        self.check_G2_compensates_for_disturbance()
        return self.contract_status
