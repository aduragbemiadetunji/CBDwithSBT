
# === CONTRACT DASHBOARD (Clean Horizontal Report Layout) ===
def draw_contract_dashboard(screen, font, contract_logs, t, eta_time):
    pygame.draw.rect(screen, (240, 240, 240), (WIDTH - 430, 10, 410, 480), border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), (WIDTH - 430, 10, 410, 480), 2, border_radius=10)

    screen.blit(font.render(f"Time: {eta_time[t].item():.2f}s", True, (0, 0, 0)), (WIDTH - 420, 20))
    status = {sys: contract_logs[sys][-1]['status'] if contract_logs[sys] else {} for sys in contract_logs}

    def draw_node(label, keys, x, y, width=95, color=(0, 0, 0)):
        height = 20 + 20 * len(keys)
        pygame.draw.rect(screen, (255, 255, 255), (x, y, width, height))
        pygame.draw.rect(screen, color, (x, y, width, height), 2)
        screen.blit(font.render(label, True, color), (x + 5, y + 3))
        for i, key in enumerate(keys):
            val = status[label].get(key, True)
            circle_color = (0, 180, 0) if val else (220, 0, 0)
            pygame.draw.circle(screen, circle_color, (x + 15, y + 25 + i * 20), 5)
            screen.blit(font.render(key, True, (0, 0, 0)), (x + 25, y + 20 + i * 20))

    def draw_arrow(from_x, from_y, to_x, to_y):
        pygame.draw.line(screen, (0, 0, 0), (from_x, from_y), (to_x, to_y), 2)
        pygame.draw.polygon(screen, (0, 0, 0), [(to_x, to_y), (to_x - 6, to_y - 4), (to_x - 6, to_y + 4)])

    # Layout
    base_x = WIDTH - 420
    col1_x = base_x + 10
    col2_x = base_x + 130
    col3_x = base_x + 250
    center_y = 250

    # Draw nodes
    draw_node("DISTURBANCE", ["A1", "A2", "G1"], col1_x, 70)
    draw_node("REFERENCE", ["A1", "G1", "G2"], col1_x, 200)
    draw_node("OBSERVER", ["A1", "A2", "A3", "G1", "G2"], col2_x, 135)
    draw_node("DP", ["A1", "A2", "A3", "G1"], col3_x, 135)
    draw_node("THRUST", ["A1", "A2", "A3", "G1"], col3_x, 270)
    draw_node("SHIP", ["A1", "A2", "A3", "A4", "A5", "G1", "G2"], col2_x, 310)

    # Arrows
    draw_arrow(col1_x + 95, 85, col2_x, 150)       # DISTURBANCE → OBSERVER
    draw_arrow(col1_x + 95, 220, col2_x, 170)      # REFERENCE → OBSERVER
    draw_arrow(col2_x + 95, 170, col3_x, 150)      # OBSERVER → DP
    draw_arrow(col3_x + 45, 220, col3_x + 45, 270) # DP → THRUST
    draw_arrow(col2_x + 10, 310 + 90, col3_x + 5, 135 + 80)  # SHIP → DP
