
import pygame
import numpy as np
import math
import sys
import matlab.engine
# from contracts.sov_contract import ShipContract
# from contracts.mpcs_contract import MPCSContract
# from contracts.sitaw_contract import SITAWContract
# from contracts.dp_contract import DPContract
# from contracts.ta_contract import ThrustAllocationContract
# from contracts.td_contract import ThrusterDynamicsContract


from contracts.observer_contract import ObserverContract
from contracts.reference_model_contract import ReferenceModelContract
from contracts.dp_controller_contract import DPControllerContract
from contracts.thrust_model_contract import ThrustModelContract
from contracts.disturbance_contract import DisturbanceContract
from contracts.sov_contract import ShipContract


# === MATLAB + DATA EXTRACTION ===
eng = matlab.engine.connect_matlab()

def convert_to_numpy_array(dataseries):
    time_values = np.asarray(eng.getfield(dataseries, 'Time'))
    data_values = np.asarray(eng.getfield(dataseries, 'Data'))
    return time_values, data_values

# Extract timeseries data from MATLAB workspace
eta = eng.workspace['Eta']
eta_sp = eng.workspace['Eta_sp']
eta_obs = eng.workspace['Eta_obs']
nu = eng.workspace['nu']
nu_sp = eng.workspace['nu_sp']
nu_obs = eng.workspace['nu_obs']
wind_in_body_frame = eng.workspace['Wind_body_frame']
wind_direction = eng.workspace['wind_direction']
wind_velocity = eng.workspace['wind_velocity']
current = eng.workspace['Current_in_body_frame']
waves = eng.workspace['Waves_in_body_frame']

Wave_height = eng.workspace['Hs']
controller_force = eng.workspace['Controller_force']
thruster_force = eng.workspace['Thruster_force']
thrust_dynamic_force = eng.workspace['Thrust_dynamic_force']
_, controller_force_data = convert_to_numpy_array(controller_force)
_, thruster_force_data = convert_to_numpy_array(thruster_force)
_, thrust_dynamic_force_data = convert_to_numpy_array(thrust_dynamic_force)



eta_time, eta_data = convert_to_numpy_array(eta)
_, eta_sp_data = convert_to_numpy_array(eta_sp)
_, eta_obs_data = convert_to_numpy_array(eta_obs)
_, nu_data = convert_to_numpy_array(nu)
_, nu_sp_data = convert_to_numpy_array(nu_sp)
_, nu_obs_data = convert_to_numpy_array(nu_obs)
_, wind_data = convert_to_numpy_array(wind_in_body_frame)
_, wind_speed_data = convert_to_numpy_array(wind_velocity)
_, wind_direction_data = convert_to_numpy_array(wind_direction)
_, current_data = convert_to_numpy_array(current)
_, waves_data = convert_to_numpy_array(waves)

# === CONTRACT LOGGING SETUP ===
contract_logs = {
    'SHIP': [],
    'OBSERVER': [],
    'REFERENCE': [],
    'DP': [],
    'THRUST': [],
    'DISTURBANCE': []

}

####### THRESHOLDS
WIND_SPEED_THRESHOLD = 20 #20-25m/s
# WIND_MAG_THRESHOLD = 500000
# CURRENT_MAG_THRESHOLD = 300 
CURRENT_SPEED_THRESHOLD = 0.8 #0.5-0.77m/s
WAVE_HEIGHT_THRESHOLD = 2.5 #2.5m
# WAVE_MAG_THRESHOLD = 5000000000
POSITION_THRESHOLD = 1 #1-2m for DP 2/3
VELOCITY_THRESHOLD = 0.4 #0.3-0.5m/s
REFERENCE_SPIKE_THRESHOLD = 10.0

# === PYGAME SETUP ===

pygame.init()
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Autonomous Ship Simulation")
font = pygame.font.SysFont(None, 18)

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 102, 204)
RED = (255, 0, 0)
GREY = (200, 200, 200)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)


# Coordinate mapping (real-world meters -> screen)
def world_to_screen(x, y, scale=10):
    # Center the map around the test area midpoint (~25, -25)
    origin_x, origin_y = WIDTH // 2 - 45 * scale, HEIGHT // 2  -25 * scale
    return int(origin_x + x * scale), int(origin_y - y * scale)

# Draw ship as arrow
def draw_ship(x, y, yaw, color=BLUE):
    ship_shape = np.array([
        [30, 0],    # Tip
        [-20, -15], # Back left
        [-15, 0],   # Notch
        [-20, 15]   # Back right
    ])
    yaw_rad = -yaw  # pygame y-axis is flipped
    rotation_matrix = np.array([
        [math.cos(yaw_rad), -math.sin(yaw_rad)],
        [math.sin(yaw_rad), math.cos(yaw_rad)]
    ])
    rotated_shape = ship_shape @ rotation_matrix.T
    screen_x, screen_y = world_to_screen(x, y)
    translated_shape = [(screen_x + point[0], screen_y + point[1]) for point in rotated_shape]
    pygame.draw.polygon(screen, color, translated_shape)

# Draw setpoint trail
def draw_setpoint_path(path_data):
    points = [world_to_screen(x, y) for x, y in path_data[:, :2]]
    if len(points) > 1:
        pygame.draw.lines(screen, GREY, False, points, 2)

# Draw trail of actual path
def draw_trail(history):
    if len(history) > 1:
        points = [world_to_screen(x, y) for x, y in history]
        pygame.draw.lines(screen, BLUE, False, points, 2)

# # Draw wind vector
# def draw_wind_vector(x, y, wind_vector):
#     screen_x, screen_y = world_to_screen(x, y)
#     wx, wy = wind_vector[0] * 0.05, -wind_vector[1] * 0.05  # scale down and flip y
#     pygame.draw.line(screen, GREEN, (screen_x, screen_y), (screen_x + wx, screen_y + wy), 2)
#     pygame.draw.circle(screen, GREEN, (int(screen_x + wx), int(screen_y + wy)), 3)

# Draw wind vector using speed and direction on ship
def draw_wind_vector(x, y, speed, direction):
    screen_x, screen_y = world_to_screen(x, y)
    wx = speed * math.cos(direction) * 2  # scale down for visibility
    wy = -speed * math.sin(direction) * 2  # flip y for pygame
    pygame.draw.line(screen, GREEN, (screen_x, screen_y), (screen_x + wx, screen_y + wy), 3)
    pygame.draw.circle(screen, GREEN, (int(screen_x + wx), int(screen_y + wy)), 5)


# Draw large wind indicator at top
def draw_wind_indicator(speed, direction):
    center_x, center_y = WIDTH - 100, 100
    wx = speed * math.cos(direction)
    wy = -speed * math.sin(direction)
    end_x = int(center_x + wx * 2)
    end_y = int(center_y + wy * 2)
    pygame.draw.line(screen, GREEN, (center_x, center_y), (end_x, end_y), 6)
    pygame.draw.circle(screen, GREEN, (end_x, end_y), 8)
    label = font.render("Wind", True, BLACK)
    screen.blit(label, (center_x - 20, center_y - 20))


# # Draw current vector
# def draw_current_vector(x, y, vector):
#     screen_x, screen_y = world_to_screen(x, y)
#     cx, cy = vector[0] * 2, -vector[1] * 2
#     pygame.draw.line(screen, ORANGE, (screen_x, screen_y), (screen_x + cx, screen_y + cy), 3)
#     pygame.draw.circle(screen, ORANGE, (int(screen_x + cx), int(screen_y + cy)), 5)

# # Draw wave effect (animated pulse)
# def draw_wave_effect(x, y, frame):
#     screen_x, screen_y = world_to_screen(x, y)
#     radius = 15 + 8 * math.sin(frame / 10.0)
#     pygame.draw.circle(screen, CYAN, (screen_x, screen_y), int(radius), 2)


# Draw axis scales and legend
def draw_scale():
    scale = 10
    for x in range(0, 60, 10):
        sx, sy = world_to_screen(x, 0, scale)
        pygame.draw.line(screen, BLACK, (sx, sy - 5), (sx, sy + 5), 1)
        label = font.render(f"{x}m", True, BLACK)
        screen.blit(label, (sx - 10, sy + 8))
    for y in range(-50, 10, 10):
        sx, sy = world_to_screen(0, y, scale)
        pygame.draw.line(screen, BLACK, (sx - 5, sy), (sx + 5, sy), 1)
        label = font.render(f"{y}m", True, BLACK)
        screen.blit(label, (sx + 8, sy - 8))
    # # Legend
    # pygame.draw.line(screen, GREEN, (30, HEIGHT - 60), (60, HEIGHT - 60), 3)
    # screen.blit(font.render("Wind", True, BLACK), (65, HEIGHT - 65))
    # pygame.draw.line(screen, ORANGE, (30, HEIGHT - 40), (60, HEIGHT - 40), 3)
    # screen.blit(font.render("Current", True, BLACK), (65, HEIGHT - 45))
    # pygame.draw.circle(screen, CYAN, (45, HEIGHT - 20), 6, 1)
    # screen.blit(font.render("Waves", True, BLACK), (65, HEIGHT - 25))



# === CONTRACT DASHBOARD (Expanded A/G view) ===
def draw_contract_dashboard(screen, font, contract_logs, t, eta_time):
    x_offset = WIDTH - 400
    y_offset = 300
    box_width = 350
    line_height = 20
    line_spacing = 6

    pygame.draw.rect(screen, (240, 240, 240), (x_offset - 10, y_offset - 10, box_width + 20, 350), border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), (x_offset - 10, y_offset - 10, box_width + 20, 350), 2, border_radius=8)

    screen.blit(font.render(f"Time: {eta_time[t].item():.2f}s", True, (0, 0, 0)), (x_offset, y_offset))

    y_cursor = y_offset + 30
    for system in ['SHIP', 'OBSERVER', 'REFERENCE', 'DP', 'THRUST', 'DISTURBANCE']:
        screen.blit(font.render(system, True, (0, 0, 0)), (x_offset, y_cursor))
        y_cursor += line_height

        if contract_logs[system]:
            status_dict = contract_logs[system][-1]['status']
            col_x = x_offset
            for key, value in status_dict.items():
                color = (0, 180, 0) if value else (220, 0, 0)
                pygame.draw.circle(screen, color, (col_x + 10, y_cursor + 8), 6)
                screen.blit(font.render(key, True, (0, 0, 0)), (col_x + 20, y_cursor))
                col_x += 60
        y_cursor += line_height + line_spacing


# Simulation loop
path_history = []
time_step = 0
skip_step = 100  # only draw every 10th frame
running = True
frame_count = 0

while running and time_step < len(eta_data):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

    # Update position

    # === CONTRACT CHECKS ===

    # Example time loop structure:
    t = time_step
    # Extract relevant time-step data
    eta_t = eta_data[t]
    eta_sp_t = eta_sp_data[t]
    eta_obs_t = eta_obs_data[t]
    nu_t = nu_data[t]
    nu_sp_t = nu_sp_data[t]
    nu_obs_t = nu_obs_data[t]
    tau_est = controller_force_data[t]
    thruster_forces = thruster_force_data[t]
    thrust_dyn = thrust_dynamic_force_data[t]
    wind_t = wind_speed_data[t][0]
    current_t = current_data[t][:2]
    waves_t = waves_data[t]
    wave_height_t = Wave_height#Wave_height[t][0] if isinstance(Wave_height[t], (list, np.ndarray)) else Wave_height[t]

    # === COMPUTATION BLOCKS ===
    # Observer
    wma_position_valid = np.all(np.abs(eta_obs_t - eta_t) < POSITION_THRESHOLD)
    filter_quality = np.all(np.abs(nu_obs_t - nu_data[t]) < VELOCITY_THRESHOLD)

    observer_contract = ObserverContract(
        eta=eta_t,
        sensors_available=True,
        tau_est=tau_est,
        eta_hat=eta_obs_t,
        nu_hat=nu_obs_t,
        filter_quality=filter_quality,
        wma_position_valid=wma_position_valid
    )
    observer_status, observer_logs = observer_contract.evaluate()

    # Reference Model
    is_smoothed = np.all(np.abs(np.gradient(eta_sp_t)) < REFERENCE_SPIKE_THRESHOLD)
    ref_model_contract = ReferenceModelContract(
        eta_sp=eta_sp_t,
        nu_sp=nu_sp_t,
        smoothed_sp=is_smoothed,
        setpoints_valid=True #Depends on if human provides setpoint
    )
    ref_status, ref_logs = ref_model_contract.evaluate()

    # DP Controller
    # error_reduction_valid = np.linalg.norm(eta_obs_t - eta_sp_t) < POSITION_THRESHOLD

    dp_contract = DPControllerContract(
        eta_sp=eta_sp_t,
        nu_sp=nu_sp_t,
        eta_hat=eta_obs_t,
        nu_hat=nu_obs_t,
        tau=tau_est,
        setpoints_smoothed=is_smoothed,
        error_reduction_valid=None
    )
    dp_status, dp_logs = dp_contract.evaluate()

    # Thrust Model
    # Max limits [kN] as per your image
    max_thrusts = [125000, 150000, 125000, 300000, 300000]
    thrust_error = tau_est - thrust_dyn
    thrust_model_contract = ThrustModelContract(
        tau_d=tau_est,
        thruster_working=all(not (np.isnan(force) or np.abs(force) < 1e-3) for force in thruster_forces),
        # thruster_force_valid=np.all(np.abs(thruster_force_data[t]) < 1e8),
        thruster_force_valid = all(abs(thruster_forces[i]) <= max_thrusts[i] for i in range(5)),
        thrust_output_valid=thrust_dyn is not None and not np.any(np.isnan(thrust_dyn))
    )
    thrust_status, thrust_logs = thrust_model_contract.evaluate()

    # Disturbance Model
    wind_available = wind_speed_data[t][0] is not None and not np.isnan(wind_speed_data[t][0])
    wave_available = Wave_height[t][0] if isinstance(Wave_height, (list, np.ndarray)) else Wave_height
    wave_available = wave_available is not None and not np.isnan(wave_available)
    current_available = not np.any(np.isnan(current_data[t][:2]))

    spectra_valid = wind_available and wave_available and current_available
    disturbance_model_contract = DisturbanceContract(
        eta=eta_t,
        disturbance_sensor_available=True,
        spectra_valid=spectra_valid
    )
    disturbance_status, disturbance_logs = disturbance_model_contract.evaluate()

    # Ship Contract
    ship_pos_error_valid = np.linalg.norm(eta_t - eta_sp_t) < POSITION_THRESHOLD
    ship_vel_error_valid = np.linalg.norm(nu_t - nu_sp_t) < VELOCITY_THRESHOLD
    ship_contract = ShipContract(
        disturbance_data={
            'wind': wind_t,
            'wave': wave_height_t,
            'current': np.linalg.norm(current_t)
        },
        disturbance_limit_data={
            'wind': WIND_SPEED_THRESHOLD,
            'wave': WAVE_HEIGHT_THRESHOLD,
            'current': CURRENT_SPEED_THRESHOLD
        },
        subsystem_outputs_valid=all([
            observer_status['G1'], observer_status['G2'],
            ref_status['G1'], ref_status['G2'], dp_status['G1'],
            thrust_status['G1'], disturbance_status['G1']
        ]),
        estimation_accuracy=observer_status['G1'],
        system_health_ok=True,
        position_error_valid=ship_pos_error_valid,
        velocity_error_valid=ship_vel_error_valid
    )
    ship_status, ship_logs = ship_contract.evaluate()

    # === LOGGING ===
    contract_logs['SHIP'].append({'time': eta_time[t], 'status': ship_status})
    contract_logs['OBSERVER'].append({'time': eta_time[t], 'status': observer_status})
    contract_logs['REFERENCE'].append({'time': eta_time[t], 'status': ref_status})
    contract_logs['DP'].append({'time': eta_time[t], 'status': dp_status})
    contract_logs['THRUST'].append({'time': eta_time[t], 'status': thrust_status})
    contract_logs['DISTURBANCE'].append({'time': eta_time[t], 'status': disturbance_status})
     
    # print(contract_logs)

    x, y, yaw = eta_obs_data[time_step]
    path_history.append((x, y))

    if time_step % skip_step == 0:
        screen.fill(WHITE)
        draw_setpoint_path(eta_sp_data)
        draw_trail(path_history)
        draw_ship(x, y, yaw)
        draw_scale()

        if time_step < len(wind_speed_data) and time_step < len(wind_direction_data):
            wind_speed = wind_speed_data[time_step][0]
            wind_dir = wind_direction_data[time_step][0]
            draw_wind_vector(x, y, wind_speed, wind_dir)
            draw_wind_indicator(wind_speed, wind_dir)
            # wind_vector = wind_data[time_step, 1:3]  # Fx, Fy
            # draw_wind_vector(x, y, wind_vector)


        # if time_step < len(current_data):
        #     current_vec = current_data[time_step, 0:2]  # x and y only
        #     draw_current_vector(x, y, current_vec)

        # if time_step < len(waves_data):
        #     draw_wave_effect(x, y, frame_count)

        #     draw_contract_dashboard(screen, font, contract_logs, time_step, eta_time)

        if time_step < len(eta_data):
            draw_contract_dashboard(screen, font, contract_logs, time_step, eta_time)
        pygame.display.flip()

    time_step += 1

waiting = True
while waiting:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            waiting = False
pygame.quit()
sys.exit()




