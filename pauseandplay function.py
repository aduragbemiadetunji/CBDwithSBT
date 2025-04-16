
# === Enhanced Simulation Controls & Contract Log Display ===

import pygame
import numpy as np
import math
import sys

pygame.init()
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Autonomous Ship Simulation - Rewind & Logs")
font = pygame.font.SysFont(None, 18)

WHITE = (255, 255, 255)
GREY = (200, 200, 200)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Dummy data setup
time_series = np.linspace(0, 100, 1000)
eta_data = np.random.rand(1000, 3) * 50  # Dummy positions
contract_logs = {
    'SHIP': [{'time': t, 'status': {'G1': True, 'G2': False}} if t % 50 == 0 else {'time': t, 'status': {'G1': True, 'G2': True}} for t in range(1000)]
}

# Rewind & Pause
paused = False
time_step = 0
max_time_step = len(eta_data) - 1

# Log display
def draw_log_box(logs, t):
    x, y = 10, HEIGHT - 150
    pygame.draw.rect(screen, (250, 250, 250), (x, y, 980, 140))
    pygame.draw.rect(screen, BLACK, (x, y, 980, 140), 2)
    log_y = y + 10
    screen.blit(font.render("Contract Violations at t = {:.2f}s".format(time_series[t]), True, BLACK), (x + 10, log_y))
    log_y += 20
    for system, entries in logs.items():
        if t < len(entries):
            status = entries[t]['status']
            for k, v in status.items():
                if not v:
                    msg = f"[{system}] {k} violated"
                    screen.blit(font.render(msg, True, RED), (x + 10, log_y))
                    log_y += 18

# Main loop
clock = pygame.time.Clock()
running = True
while running:
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                time_step = max(0, time_step - 1)
            elif event.key == pygame.K_RIGHT:
                time_step = min(max_time_step, time_step + 1)
            elif event.key == pygame.K_SPACE:
                paused = not paused

    if not paused:
        time_step = (time_step + 1) % max_time_step

    # Draw current ship position (dot only for now)
    x, y, _ = eta_data[time_step]
    pygame.draw.circle(screen, GREY, (int(WIDTH // 2 + x), int(HEIGHT // 2 - y)), 6)

    draw_log_box(contract_logs, time_step)
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
