import pygame
import numpy as np
import math
import sys
import matlab.engine

# === MATLAB SETUP ===
eng = matlab.engine.connect_matlab()

def convert_to_numpy_array(dataseries):
    time_values = np.asarray(eng.getfield(dataseries, 'Time'))
    data_values = np.asarray(eng.getfield(dataseries, 'Data'))
    return time_values, data_values

# Extract timeseries data from MATLAB workspace
eta = eng.workspace['Eta']
eta_sp = eng.workspace['Eta_sp']
eta_obs = eng.workspace['Eta_obs']
wind_in_body_frame = eng.workspace['Wind_body_frame']
wind_direction = eng.workspace['wind_direction']
wind_velocity = eng.workspace['wind_velocity']
current = eng.workspace['Current_in_body_frame']
waves = eng.workspace['Waves_in_body_frame']



eta_time, eta_data = convert_to_numpy_array(eta)
_, eta_sp_data = convert_to_numpy_array(eta_sp)
_, eta_obs_data = convert_to_numpy_array(eta_obs)
_, wind_data = convert_to_numpy_array(wind_in_body_frame)
_, wind_speed_data = convert_to_numpy_array(wind_velocity)
_, wind_direction_data = convert_to_numpy_array(wind_direction)
_, current_data = convert_to_numpy_array(current)
_, waves_data = convert_to_numpy_array(waves)

# === PYGAME SETUP ===
pygame.init()
WIDTH, HEIGHT = 800, 800
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
    origin_x, origin_y = WIDTH // 2 - 25 * scale, HEIGHT // 2  -25 * scale
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


# Draw current vector
def draw_current_vector(x, y, vector):
    screen_x, screen_y = world_to_screen(x, y)
    cx, cy = vector[0] * 2, -vector[1] * 2
    pygame.draw.line(screen, ORANGE, (screen_x, screen_y), (screen_x + cx, screen_y + cy), 3)
    pygame.draw.circle(screen, ORANGE, (int(screen_x + cx), int(screen_y + cy)), 5)

# Draw wave effect (animated pulse)
def draw_wave_effect(x, y, frame):
    screen_x, screen_y = world_to_screen(x, y)
    radius = 15 + 8 * math.sin(frame / 10.0)
    pygame.draw.circle(screen, CYAN, (screen_x, screen_y), int(radius), 2)


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
    # Legend
    pygame.draw.line(screen, GREEN, (30, HEIGHT - 60), (60, HEIGHT - 60), 3)
    screen.blit(font.render("Wind", True, BLACK), (65, HEIGHT - 65))
    pygame.draw.line(screen, ORANGE, (30, HEIGHT - 40), (60, HEIGHT - 40), 3)
    screen.blit(font.render("Current", True, BLACK), (65, HEIGHT - 45))
    pygame.draw.circle(screen, CYAN, (45, HEIGHT - 20), 6, 1)
    screen.blit(font.render("Waves", True, BLACK), (65, HEIGHT - 25))

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


        if time_step < len(current_data):
            current_vec = current_data[time_step, 0:2]  # x and y only
            draw_current_vector(x, y, current_vec)

        if time_step < len(waves_data):
            draw_wave_effect(x, y, frame_count)

        pygame.display.flip()

    time_step += 1

pygame.quit()
sys.exit()
