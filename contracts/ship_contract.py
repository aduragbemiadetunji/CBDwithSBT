class ShipContract:

    def __init__(self, reference_trajectory, vessel_trajectory, observer_trajectory, reference_velocity, observer_velocity, environment_conditions,
                 mpcs_status, dp_status, sitaw_status, position_threshold, velocity_threshold):
        """
        Parameters:
        - reference_trajectory: The planned route or setpoints
        - vessel_trajectory: Actual ship trajectory from simulation
        - environment_conditions: Dict with wind, wave, current magnitudes
        - mpcs_status: Boolean or object indicating MPCS is functioning correctly
        - dp_status: Boolean or object indicating DP system is functioning correctly
        - sitaw_status: Boolean or object indicating SITAW system is functioning correctly
        - position_threshold: Acceptable deviation from reference (δ_max)
        """
        self.reference_trajectory = reference_trajectory
        self.vessel_trajectory = vessel_trajectory
        self.observer_trajectory = observer_trajectory
        self.reference_velocity = reference_velocity
        self.observer_velocity = observer_velocity
        self.environment_conditions = environment_conditions
        self.mpcs_status = mpcs_status
        self.dp_status = dp_status
        self.sitaw_status = sitaw_status
        self.position_threshold = position_threshold
        self.velocity_threshold = velocity_threshold
        self.contract_status = {
            'A1': None, 'A2': None, 'A3': None, 'A4': None,
            'G1': None, 'G2': None
        }

    # --- Assumptions ---
    def check_A1_reference_available(self):
        self.contract_status['A1'] = self.reference_trajectory is not None
        return self.contract_status['A1']

    def check_A2_environment_within_limits(self):
        # Placeholder thresholds (can be replaced with actual values)
        wind_limit = 20  # m/s
        wave_limit = 2.5   # m
        current_limit = 0.8  # m/s

        wind_ok = self.environment_conditions['wind'] <= wind_limit
        wave_ok = self.environment_conditions['wave'] <= wave_limit
        current_ok = self.environment_conditions['current'] <= current_limit
        self.contract_status['A2'] = wind_ok and wave_ok and current_ok
        return self.contract_status['A2']

    def check_A3_subsystems_operational(self):
        self.contract_status['A3'] = self.mpcs_status and self.dp_status
        return self.contract_status['A3']

    def check_A4_state_estimation_valid(self):
        import numpy as np
        self.contract_status['A4'] = self.sitaw_status

        deviation = np.linalg.norm(
            self.vessel_trajectory - self.observer_trajectory
        )
        self.contract_status['A4'] = deviation <= self.position_threshold
    
        return self.contract_status['A4']

    # --- Guarantee ---
    # def check_G1_track_trajectory(self):
    #     import numpy as np

    #     if not all([self.contract_status[a] for a in ['A1', 'A2', 'A3', 'A4']]):
    #         self.contract_status['G1'] = False  # Cannot guarantee if assumptions not met
    #         return None
        

    #     # Compute deviation (you can use more accurate method based on trajectory format)
    #     deviation = np.linalg.norm(
    #         self.vessel_trajectory - self.reference_trajectory
    #     )
    #     self.contract_status['G1'] = deviation <= self.position_threshold
    #     return self.contract_status['G1']


    def check_G1_track_trajectory(self):
        import numpy as np
        # Compute deviation (you can use more accurate method based on trajectory format)
        deviation = np.linalg.norm(
            self.vessel_trajectory - self.reference_trajectory
        )
        velocity_deviation = np.linalg.norm(
            self.observer_velocity - self.reference_velocity
        )
        # print(deviation, velocity_deviation)
        self.contract_status['G1'] = deviation <= self.position_threshold and velocity_deviation <= self.velocity_threshold
        # self.contract_status['G1'] = velocity_deviation <= self.velocity_threshold
        return self.contract_status['G1']
    

    def check_G2_track_trajectory(self):
        self.contract_status['G2'] = all([self.contract_status[a] for a in ['A1', 'A2', 'A3', 'A4']])
        
        return self.contract_status['G2']


    #     # # Compute deviation (you can use more accurate method based on trajectory format)
    #     # deviation = np.linalg.norm(
    #     #     self.vessel_trajectory - self.reference_trajectory
    #     # )
    #     # self.contract_status['G1'] = deviation <= self.position_threshold
    #     # return self.contract_status['G1']
    




    # --- Evaluate All ---
    def evaluate(self):
        """Evaluate all assumptions and guarantees."""
        self.check_A1_reference_available()
        self.check_A2_environment_within_limits()
        self.check_A3_subsystems_operational()
        self.check_A4_state_estimation_valid()
        self.check_G1_track_trajectory()
        self.check_G2_track_trajectory()
        return self.contract_status
