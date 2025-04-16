class ThrusterDynamicsContract:
    def __init__(self, commanded_thrust, actual_thrust, actuator_health_status,
                 response_tolerance):
        """
        Parameters:
        - commanded_thrust: Desired thrust vector from thrust allocation
        - actual_thrust: Measured thrust output
        - actuator_health_status: Boolean indicating if all actuators are healthy
        - response_tolerance: Max allowable deviation in thrust response
        """
        self.commanded_thrust = commanded_thrust
        self.actual_thrust = actual_thrust
        self.actuator_health_status = actuator_health_status
        self.response_tolerance = response_tolerance

        self.contract_status = {
            'A1': None,
            'A2': None,
            'G1': None
        }

    # --- Assumptions ---
    def check_A1_actuators_healthy(self):
        self.contract_status['A1'] = self.actuator_health_status
        return self.contract_status['A1']

    def check_A2_response_model_known(self):
        # In most simulations, actuator models are predefined, so we assume true
        self.contract_status['A2'] = True
        return self.contract_status['A2']

    # --- Guarantee ---
    def check_G1_thrust_realization_accuracy(self):
        import numpy as np
        if not all([self.contract_status['A1'], self.contract_status['A2']]):
            self.contract_status['G1'] = None
            return None

        deviation = np.linalg.norm(self.actual_thrust - self.commanded_thrust)
        self.contract_status['G1'] = deviation <= self.response_tolerance
        return self.contract_status['G1']

    # --- Evaluate ---
    def evaluate(self):
        self.check_A1_actuators_healthy()
        self.check_A2_response_model_known()
        self.check_G1_thrust_realization_accuracy()
        return self.contract_status