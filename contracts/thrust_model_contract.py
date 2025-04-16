
class ThrustModelContract:
    def __init__(self, tau_d, thruster_working, thruster_force_valid, thrust_output_valid):
        self.tau_d = tau_d
        self.thruster_working = thruster_working
        self.thruster_force_valid = thruster_force_valid
        self.thrust_output_valid = thrust_output_valid

        self.contract_status = {
            'A1': None, 'A2': None, 'A3': None,
            'G1': None
        }

        self.violation_log = []

    def log_violation(self, contract_id, message):
        self.violation_log.append({ "contract_id": contract_id, "message": message })

    def check_A1_input_force_available(self):
        result = self.tau_d is not None
        self.contract_status['A1'] = result
        if not result:
            self.log_violation("A1", "Control input tau_d is missing.")
        return result

    def check_A2_thrusters_operational(self):
        result = self.thruster_working
        self.contract_status['A2'] = result
        if not result:
            self.log_violation("A2", "One or more thrusters are not working.")
        return result

    def check_A3_thruster_force_limits(self):
        result = self.thruster_force_valid
        self.contract_status['A3'] = result
        if not result:
            self.log_violation("A3", "Thruster forces exceed operational limits.")
        return result

    def check_G1_force_output_accurate(self):
        result = self.thrust_output_valid
        self.contract_status['G1'] = result
        if not result:
            self.log_violation("G1", "Thrust output does not match expected dynamics.")
        return result

    def evaluate(self):
        self.check_A1_input_force_available()
        self.check_A2_thrusters_operational()
        self.check_A3_thruster_force_limits()
        self.check_G1_force_output_accurate()
        return self.contract_status, self.violation_log
