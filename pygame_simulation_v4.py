
import pygame
import numpy as np
import math
import sys
import matlab.engine
from contracts.ship_contract import ShipContract
from contracts.mpcs_contract import MPCSContract
from contracts.sitaw_contract import SITAWContract
from contracts.dp_contract import DPContract
from contracts.ta_contract import ThrustAllocationContract
from contracts.td_contract import ThrusterDynamicsContract

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
    'MPCS': [],
    'SITAW': [],
    'DP': [],
    'TA': [],
    'TD': []

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
    for system in ['SHIP', 'MPCS', 'SITAW', 'DP', 'TA', 'TD']:
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
    eta_t = eta_data[time_step]
    eta_sp_t = eta_sp_data[time_step] if time_step < len(eta_sp_data) else None
    dp_commands_received = True  # Placeholder

    disturbances = (
        wind_data[time_step],
        wind_speed_data[time_step],
        current_data[time_step],
        current_data[time_step],  # For simplicity, using same data
        Wave_height,         # Wave height (m)
        waves_data[time_step] 
    )
    # SHIP CONTRACT
    ship_contract = ShipContract(
        reference_trajectory=eta_sp_data[time_step],
        vessel_trajectory=eta_data[time_step],
        observer_trajectory = eta_obs_data[time_step],
        reference_velocity = nu_sp_data[time_step],
        observer_velocity = nu_obs_data[time_step],
        environment_conditions={
            'wind': np.linalg.norm(wind_speed_data[time_step][:2]),
            # 'wave': np.linalg.norm(waves_data[time_step]),
            'wave': Wave_height,
            'current': np.linalg.norm(current_data[time_step][:2]),
            # 'current': np.linalg.norm(current_speed)

        },
        mpcs_status=True,
        dp_status=True,
        sitaw_status=True,
        position_threshold=POSITION_THRESHOLD,
        velocity_threshold=VELOCITY_THRESHOLD
    )
    contract_logs['SHIP'].append({'time': eta_time[time_step], 'status': ship_contract.evaluate()})
    
    
    #MPCS CONTRACT
    mpcs_contract = MPCSContract(
        reference_path=eta_sp_data[time_step],
        vessel_state=eta_data[time_step],
        disturbance_data={
            'wind': np.linalg.norm(wind_data[time_step][:2]),
            'wave': np.linalg.norm(waves_data[time_step]),
            'current': np.linalg.norm(current_data[time_step][:2])
        },
        setpoints=eta_sp_data[time_step],
        dp_feedback_status=True,
        sitaw_data_accuracy=True,
        position_threshold=POSITION_THRESHOLD
    )
    contract_logs['MPCS'].append({'time': eta_time[time_step], 'status': mpcs_contract.evaluate()})
    
    #SITAW CONTRACT
    sitaw_contract = SITAWContract(
        vessel_state_estimate=eta_obs_data[time_step],
        disturbance_estimate=np.array([
            np.linalg.norm(wind_data[time_step]),
            np.linalg.norm(waves_data[time_step]),
            np.linalg.norm(current_data[time_step][:3])
        ]),
        true_vessel_state=eta_data[time_step],
        true_disturbances=np.array([
            np.linalg.norm(wind_data[time_step]),
            np.linalg.norm(waves_data[time_step]),
            np.linalg.norm(current_data[time_step][:3])
        ]),
        accuracy_thresholds={'state': 2, 'disturbance': 1000}
    )
    contract_logs['SITAW'].append({'time': eta_time[time_step], 'status': sitaw_contract.evaluate()})
    
    #DP CONTRACT
    dp_contract = DPContract(
        received_setpoint=eta_sp_data[time_step],
        actual_vessel_state=eta_obs_data[time_step],
        setpoint_valid=True,
        thruster_feedback_status=True,
        position_threshold=POSITION_THRESHOLD
    )
    contract_logs['DP'].append({'time': eta_time[time_step], 'status': dp_contract.evaluate()})


    #TA CONTRACT
    thrust_alloc_contract = ThrustAllocationContract(
        requested_force_vector=controller_force_data[time_step],
        thruster_config=[{'id': i} for i in range(5)],
        allocation_success=True,
        allocation_error=controller_force_data[time_step] - thrust_dynamic_force_data[time_step],
        allocation_threshold=20000000.0 #200
    )
    contract_logs['TA'].append({'time': eta_time[time_step], 'status': thrust_alloc_contract.evaluate()})

    # thrust_alloc_contract.evaluate()


    #TD CONTRACT
    thruster_dyn_contract = ThrusterDynamicsContract(
        commanded_thrust=controller_force_data[time_step],
        actual_thrust=thrust_dynamic_force_data[time_step],
        actuator_health_status=True,
        response_tolerance=25000000.0 #250
    )
    contract_logs['TD'].append({'time': eta_time[time_step], 'status': thruster_dyn_contract.evaluate()})

    # thruster_dyn_contract.evaluate()

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

