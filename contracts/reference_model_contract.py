
class ReferenceModelContract:
    def __init__(self, eta_sp, nu_sp, smoothed_sp, setpoints_valid):
        self.eta_sp = eta_sp
        self.nu_sp = nu_sp
        self.smoothed_sp = smoothed_sp
        self.setpoints_valid = setpoints_valid

        self.contract_status = {
            'A1': None,
            'G1': None, 'G2': None
        }

        self.violation_log = []

    def log_violation(self, contract_id, message):
        self.violation_log.append({ "contract_id": contract_id, "message": message })

    def check_A1_setpoints_available(self):
        result = self.eta_sp is not None and self.nu_sp is not None
        self.contract_status['A1'] = result
        if not result:
            self.log_violation("A1", "Setpoints eta_sp or nu_sp are missing.")
        return result

    def check_G1_trajectory_available(self):
        result = self.setpoints_valid
        self.contract_status['G1'] = result
        if not result:
            self.log_violation("G1", "Trajectory setpoints are not valid or contain anomalies.")
        return result

    def check_G2_smoothing_applied(self):
        result = self.smoothed_sp
        self.contract_status['G2'] = result
        if not result:
            self.log_violation("G2", "Setpoints are not smoothed properly.")
        return result

    def evaluate(self):
        self.check_A1_setpoints_available()
        self.check_G1_trajectory_available()
        self.check_G2_smoothing_applied()
        return self.contract_status, self.violation_log
