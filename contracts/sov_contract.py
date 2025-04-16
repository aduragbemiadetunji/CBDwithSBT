
class ShipContract:
    def __init__(self, disturbance_data, disturbance_limit_data, subsystem_outputs_valid, estimation_accuracy, system_health_ok, position_error_valid, velocity_error_valid):
        """
        Parameters:
        - disturbance_data: Dictionary with wind, wave, current
        - subsystem_outputs_valid: Boolean indicating if all other subsystem outputs are within normal performance
        - estimation_accuracy: Boolean indicating if state estimation (eta_hat, nu_hat) is accurate
        - system_health_ok: Boolean indicating all physical components (engine, fuel, battery) are okay
        - position_error_valid: Boolean indicating vessel stays within allowed deviation from trajectory
        """
        self.disturbance_data = disturbance_data
        self.disturbance_limit_data = disturbance_limit_data
        self.subsystem_outputs_valid = subsystem_outputs_valid
        self.estimation_accuracy = estimation_accuracy
        self.system_health_ok = system_health_ok
        self.position_error_valid = position_error_valid
        self.velocity_error_valid = velocity_error_valid

        self.contract_status = {
            'A1': None, 'A2': None, 'A3': None, 'A4': None, #'A5': None,
            'G1': None, 'G2': None
        }

        self.violation_log = []

    def log_violation(self, contract_id, message):
        self.violation_log.append({ "contract_id": contract_id, "message": message })

    # --- Assumptions ---
    def check_A1_disturbance_data_available(self):
        result = self.disturbance_data is not None and all(k in self.disturbance_data for k in ['wind', 'wave', 'current'])
        self.contract_status['A1'] = result
        if not result:
            self.log_violation("A1", "Disturbance data is missing or incomplete.")
        return result

    def check_A2_disturbances_within_limits(self):
        # result = all(abs(self.disturbance_data[k]) < 100 for k in ['wind', 'wave', 'current'])  # Placeholder threshold

        # Placeholder thresholds (can be replaced with actual values)
        wind_limit = self.disturbance_limit_data['wind']
        wave_limit = self.disturbance_limit_data['wave']
        current_limit = self.disturbance_limit_data['current']

        wind_ok = self.disturbance_data['wind'] <= wind_limit
        wave_ok = self.disturbance_data['wave'] <= wave_limit
        current_ok = self.disturbance_data['current'] <= current_limit
        result = wind_ok and wave_ok and current_ok

        self.contract_status['A2'] = result
        if not result:
            self.log_violation("A2", "Disturbance exceeds operational limits.")
        return result

    def check_A3_subsystem_performance_ok(self):
        result = self.subsystem_outputs_valid
        self.contract_status['A3'] = result
        if not result:
            self.log_violation("A3", "Subsystem outputs are abnormal.")
        return result

    def check_A4_estimation_accuracy(self):
        result = self.estimation_accuracy
        self.contract_status['A4'] = result
        if not result:
            self.log_violation("A4", "State estimation is inaccurate.")
        return result

    # def check_A5_health_ok(self):
    #     result = self.system_health_ok
    #     self.contract_status['A5'] = result
    #     if not result:
    #         self.log_violation("A5", "System health check failed.")
    #     return result

    # --- Guarantees ---
    def check_G1_trajectory_within_error(self):
        result = self.position_error_valid and self.velocity_error_valid
        self.contract_status['G1'] = result
        if not result:
            self.log_violation("G1", "Vessel deviates from trajectory.")
        return result

    def check_G2_ship_assumptions_hold(self):
        result = all([
            self.contract_status['A1'],
            self.contract_status['A2'],
            self.contract_status['A3'],
            self.contract_status['A4'],
            # self.contract_status['A5']
        ])
        self.contract_status['G2'] = result
        if not result:
            self.log_violation("G2", "One or more ship assumptions are invalid.")
        return result

    def evaluate(self):
        self.check_A1_disturbance_data_available()
        self.check_A2_disturbances_within_limits()
        self.check_A3_subsystem_performance_ok()
        self.check_A4_estimation_accuracy()
        # self.check_A5_health_ok()
        self.check_G1_trajectory_within_error()
        self.check_G2_ship_assumptions_hold()
        return self.contract_status, self.violation_log
