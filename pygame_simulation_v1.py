import pygame
import numpy as np
import matlab.engine

# Initialize MATLAB engine
eng = matlab.engine.connect_matlab()

def convert_to_numpy_array(dataseries):
    time_values = np.asarray(eng.getfield(dataseries, 'Time'))
    data_values = np.asarray(eng.getfield(dataseries, 'Data'))
    return time_values, data_values

# Retrieve MATLAB data
times, eta_data = convert_to_numpy_array(eng.workspace['Eta'])
_, eta_sp_data = convert_to_numpy_array(eng.workspace['Eta_sp'])
_, wind_data = convert_to_numpy_array(eng.workspace['Wind_body_frame'])
_, wind_speed_data = convert_to_numpy_array(eng.workspace['wind_velocity'])

# Pygame setup
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ship Simulation")
clock = pygame.time.Clock()

# Ship parameters
SHIP_LENGTH, SHIP_WIDTH = 30, 10
SCALE = 5  # Scale for real-world to screen conversion
FRAME_RATE = 60  # Faster frame rate for smoother animation
TIME_STEP_INCREMENT = 3  # Increase time step for faster playback

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# Simulation loop
running = True
time_step = 0
while running and time_step < len(times):
    screen.fill(WHITE)  # White background

    # Extract ship position and heading
    x, y, yaw = eta_data[time_step, 0], eta_data[time_step, 1], eta_data[time_step, 2]
    ship_pos = (int(WIDTH / 2 + x * SCALE), int(HEIGHT / 2 - y * SCALE))

    # Extract wind data
    wind_x, wind_y = wind_data[time_step, 0], wind_data[time_step, 1]
    wind_speed = wind_speed_data[time_step]  # Wind speed magnitude

    # Validate wind values
    if not np.isnan(wind_x) and not np.isnan(wind_y) and wind_speed > 0:
        wind_length = min(wind_speed * 10, 50)  # Scale wind effect but limit max size
        wind_end = (ship_pos[0] + wind_x * wind_length, ship_pos[1] - wind_y * wind_length)
        pygame.draw.line(screen, RED, ship_pos, wind_end, 3)
        pygame.draw.polygon(screen, RED, [(wind_end[0], wind_end[1]),
                                           (wind_end[0] - 5, wind_end[1] - 5),
                                           (wind_end[0] + 5, wind_end[1] - 5)])  # Arrowhead

    # Draw predefined route
    for i in range(len(eta_sp_data) - 1):
        x1, y1 = int(WIDTH / 2 + eta_sp_data[i, 0] * SCALE), int(HEIGHT / 2 - eta_sp_data[i, 1] * SCALE)
        x2, y2 = int(WIDTH / 2 + eta_sp_data[i + 1, 0] * SCALE), int(HEIGHT / 2 - eta_sp_data[i + 1, 1] * SCALE)
        pygame.draw.line(screen, BLUE, (x1, y1), (x2, y2), 2)

    # Draw ship (arrow shape)
    front = (ship_pos[0] + SHIP_LENGTH * np.cos(yaw), ship_pos[1] + SHIP_LENGTH * np.sin(yaw))
    back_left = (ship_pos[0] - SHIP_LENGTH * np.cos(yaw) - SHIP_WIDTH * np.sin(yaw),
                 ship_pos[1] - SHIP_LENGTH * np.sin(yaw) + SHIP_WIDTH * np.cos(yaw))
    back_right = (ship_pos[0] - SHIP_LENGTH * np.cos(yaw) + SHIP_WIDTH * np.sin(yaw),
                  ship_pos[1] - SHIP_LENGTH * np.sin(yaw) - SHIP_WIDTH * np.cos(yaw))
    pygame.draw.polygon(screen, BLACK, [front, back_left, back_right])

    # Update display
    pygame.display.flip()
    clock.tick(FRAME_RATE)  # Faster animation
    time_step += TIME_STEP_INCREMENT  # Increase time step to speed up playback

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
