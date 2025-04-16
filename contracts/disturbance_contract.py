
class DisturbanceContract:
    def __init__(self, eta, disturbance_sensor_available, spectra_valid):
        self.eta = eta
        self.disturbance_sensor_available = disturbance_sensor_available
        self.spectra_valid = spectra_valid

        self.contract_status = {
            'A1': None, 'A2': None,
            'G1': None
        }

        self.violation_log = []

    def log_violation(self, contract_id, message):
        self.violation_log.append({ "contract_id": contract_id, "message": message })

    def check_A1_position_available(self):
        result = self.eta is not None
        self.contract_status['A1'] = result
        if not result:
            self.log_violation("A1", "Position data (eta) unavailable for environmental modeling.")
        return result

    def check_A2_input_data_available(self):
        result = self.disturbance_sensor_available
        self.contract_status['A2'] = result
        if not result:
            self.log_violation("A2", "Environmental data (wind/wave/current) not available.")
        return result

    def check_G1_environment_spectra_valid(self):
        result = self.spectra_valid
        self.contract_status['G1'] = result
        if not result:
            self.log_violation("G1", "Environment model output is not realistic or valid.")
        return result

    def evaluate(self):
        self.check_A1_position_available()
        self.check_A2_input_data_available()
        self.check_G1_environment_spectra_valid()
        return self.contract_status, self.violation_log
