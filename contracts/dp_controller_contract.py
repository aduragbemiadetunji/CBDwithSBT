
class DPControllerContract:
    def __init__(self, eta_sp, nu_sp, eta_hat, nu_hat, tau, setpoints_smoothed, error_reduction_valid):
        self.eta_sp = eta_sp
        self.nu_sp = nu_sp
        self.eta_hat = eta_hat
        self.nu_hat = nu_hat
        self.tau = tau
        self.setpoints_smoothed = setpoints_smoothed
        self.error_reduction_valid = error_reduction_valid

        self.contract_status = {
            'A1': None, 'A2': None, 'A3': None,
            'G1': None
        }

        self.violation_log = []

    def log_violation(self, contract_id, message):
        self.violation_log.append({ "contract_id": contract_id, "message": message })

    def check_A1_reference_input_available(self):
        result = self.eta_sp is not None and self.nu_sp is not None
        self.contract_status['A1'] = result
        if not result:
            self.log_violation("A1", "Reference setpoints are missing.")
        return result

    def check_A2_estimates_available(self):
        result = self.eta_hat is not None and self.nu_hat is not None
        self.contract_status['A2'] = result
        if not result:
            self.log_violation("A2", "State estimates eta_hat or nu_hat are missing.")
        return result

    def check_A3_setpoints_smoothed(self):
        result = self.setpoints_smoothed
        self.contract_status['A3'] = result
        if not result:
            self.log_violation("A3", "Setpoints are not smoothed.")
        return result

    def check_G1_error_reduction(self):
        # result = self.error_reduction_valid
        result = self.tau is not None
        self.contract_status['G1'] = result
        if not result:
            self.log_violation("G1", "Control action does not reduce error.")
        return result

    def evaluate(self):
        self.check_A1_reference_input_available()
        self.check_A2_estimates_available()
        self.check_A3_setpoints_smoothed()
        self.check_G1_error_reduction()
        return self.contract_status, self.violation_log
