"""Сборка железнодорожных путей из рельсов и шпал."""
from rail import draw_rail_path
from sleeper import draw_sleepers

POLYGON_TRACK_COUNT = 5
POLYGON_TRACK_SPACING = 320
POLYGON_TRACK_LENGTH = 5200
POLYGON_START_X = -400
POLYGON_BRANCH_RADIUS = 900
POLYGON_BRANCH_ANGLE = 24
POLYGON_BRANCH_LENGTH = 1350
POLYGON_BRANCH_STARTS = [900, 1850, 2850, 3900]
CURVE_SAMPLE_STEP = 18

def create_tracks():
    """Создаёт линии путей и список шпал с расстоянием пропуска в начале ветки."""
    track_lines = []
    track_sleepers = []
    for lane in range(POLYGON_TRACK_COUNT):
        lane_y = (lane - (POLYGON_TRACK_COUNT - 1) / 2) * POLYGON_TRACK_SPACING
        straight_line = [
            (float(POLYGON_START_X), float(lane_y), 0.0),
            (float(POLYGON_START_X + POLYGON_TRACK_LENGTH), float(lane_y), 0.0),
        ]
        track_lines.append(straight_line)
        track_sleepers.append((straight_line, 0.0))
        if lane in (0, 1, 3, 4):
            side = -1 if lane < 2 else 1
            start_x = POLYGON_BRANCH_STARTS[lane if lane < 2 else lane - 1]
            import math
            angle_max = math.radians(POLYGON_BRANCH_ANGLE)
            radius = float(POLYGON_BRANCH_RADIUS)
            arc_len = radius * angle_max
            arc_count = max(3, math.ceil(arc_len / CURVE_SAMPLE_STEP))
            branch = []
            for i in range(arc_count + 1):
                a = angle_max * i / arc_count
                branch.append((start_x + radius * math.sin(a),
                               lane_y + side * radius * (1.0 - math.cos(a)), side * a))
            ex, ey, ea = branch[-1]
            straight_count = max(2, math.ceil(POLYGON_BRANCH_LENGTH / CURVE_SAMPLE_STEP))
            for i in range(1, straight_count + 1):
                d = POLYGON_BRANCH_LENGTH * i / straight_count
                branch.append((ex + d * math.cos(ea), ey + d * math.sin(ea), ea))
            track_lines.append(branch)
            track_sleepers.append((branch, 0.0))
    return track_lines, track_sleepers

def draw_tracks(screen, track_lines, track_sleepers, camera_x, camera_y, zoom):
    """Рисует шпалы снизу, затем рельсы поверх них."""
    for centerline, skip_distance in track_sleepers:
        draw_sleepers(screen, centerline, camera_x, camera_y, zoom,
                      skip_start_distance=skip_distance)
    for centerline in track_lines:
        draw_rail_path(screen, centerline, camera_x, camera_y, zoom)
