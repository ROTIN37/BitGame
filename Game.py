from Bit import *
from framebuf import FrameBuffer, RGB565

begin()

import math
import time
import random
import machine


machine.freq(240000000)

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 128
FOV = math.pi / 2  # 90 degrees (wider FOV)
HALF_FOV = FOV / 2
NUM_RAYS = SCREEN_WIDTH  # One ray per screen column
SCALE = 3  # Each ray corresponds to one pixel column
MAX_DEPTH = 6

FOVn = 100


c = 0



# Colors
GRAY = 0xAD55
WHITE = 0xFFFF
WALLS = 0xC020
BLACK = 0
RED = 0xF800
SKY = 0x6CDF
GREEN = Display.Color.Green
ORB = 1823  # Custom color for the orb

# Player position and angle
player_x, player_y = 2, 2
player_angle = 90

lvl1_x, lvl1_y = 14, 18




BLUE = 0x03DF
RED = 0xF041
PURPLE = 0xB81F
CENTER_X = 64  # Center of the display (assuming 128x128 display)
CENTER_Y = 12
RHOMBUS_WIDTH = 5  # Horizontal size of the rhombus
RHOMBUS_HEIGHT = 10  # Vertical size of the rhombus (makes it more needle-like)



import json

# Example multiplayer data, replace with actual JSON loading
multiplayer_players = [
    {"x": 2.5, "y": 2.5, "color": Display.Color.Green},
    {"x": 1, "y": 1, "color": Display.Color.Yellow},
]




# Scene (0 = empty, 1 = wall, 2 = exit)
scene = [
    [1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1],
    [1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1],
    [1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1],
]

# Orb positions (x, y) in world coordinates
orbs = [
    (2, 3),
    (5, 5),
]













# Function to adjust 16-bit RGB565 color brightness
def adjust_color_brightness(color, brightness):
    # Extract RGB components from 16-bit RGB565 color
    red = (color >> 11) & 0x1F  # 5 bits for red
    green = (color >> 5) & 0x3F  # 6 bits for green
    blue = color & 0x1F  # 5 bits for blue

    # Adjust brightness
    red = int(red * brightness)
    green = int(green * brightness)
    blue = int(blue * brightness)

    # Clamp values to valid ranges
    red = min(red, 0x1F)
    green = min(green, 0x3F)
    blue = min(blue, 0x1F)

    # Recombine into 16-bit RGB565 color
    return (red << 11) | (green << 5) | blue


















# Precompute angle lookup tables
angle_step = FOV / NUM_RAYS
angle_lookup = [player_angle - HALF_FOV + i * angle_step for i in range(NUM_RAYS)]
cos_lookup = [math.cos(angle) for angle in angle_lookup]
sin_lookup = [math.sin(angle) for angle in angle_lookup]




def find_and_update(array, lvl1_x, lvl1_y):
    # Get the dimensions of the array
    rows = len(array)
    cols = len(array[0]) if rows > 0 else 0

    # List to store valid candidates (cells with 1 and exactly one adjacent 0)
    candidates = []

    # Iterate through the array to find valid cells
    for i in range(rows):
        for j in range(cols):
            if array[i][j] == 1:
                # Check adjacent cells (up, down, left, right)
                adjacent_zeros = []
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    x, y = i + dx, j + dy
                    if 0 <= x < rows and 0 <= y < cols and array[x][y] == 0:
                        adjacent_zeros.append((x, y))

                # If there is exactly one adjacent 0, add to candidates
                if len(adjacent_zeros) == 1:
                    candidates.append((i, j, adjacent_zeros[0]))

    # If no valid candidates are found, return the original array and coordinates
    if not candidates:
        print("No valid cell found.")
        return array, lvl1_x, lvl1_y

    # Randomly select a candidate
    selected = random.choice(candidates)
    i, j, (zero_x, zero_y) = selected

    # Update the array and coordinates
    array[i][j] = 2
    lvl1_x, lvl1_y = zero_x, zero_y

    print(f"Updated cell ({i}, {j}) to 2 and set lvl1_x, lvl1_y to ({zero_x}, {zero_y})")
    return array, lvl1_x, lvl1_y




def find_empty_cells(maze):

    empty_cells = []
    for y in range(len(maze)):
        for x in range(len(maze[0])):
            if maze[y][x] == 0:
                empty_cells.append((x, y))
    return empty_cells

def place_orbs(num_orbs=5):

    global orbs
    empty_cells = find_empty_cells(scene)
    
    
    num_orbs = min(num_orbs, len(empty_cells))
    

    selected_positions = []
    for _ in range(num_orbs):
        if empty_cells:  # Check for empty cell
            # Pick a random empty cell
            index = random.randint(0, len(empty_cells) - 1)
            pos = empty_cells.pop(index)
            centered_pos = (pos[0] + 0.5, pos[1] + 0.5)
            selected_positions.append(centered_pos)
    
    # Update the global orbs list
    orbs = selected_positions
    print(f"Placed {len(orbs)} orbs at: {orbs}")


    
def print_maze(maze):

    for row in maze:
        print("".join("#" if cell == 1 else " " for cell in row))

# Not used
def shuffle(arr):
    for i in range(len(arr) - 1, 0, -1):
        j = random.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]

def generate_maze(rows, cols):
    #Prims algorithm generation

    # Ensure rows and cols are odd
    if rows % 2 == 0:
        rows += 1
    if cols % 2 == 0:
        cols += 1

    # Initialize the maze grid
    maze = [[1 for _ in range(cols)] for _ in range(rows)]

    # Start with a random cell
    start_row, start_col = random.randint(1, rows - 2), random.randint(1, cols - 2)
    maze[start_row][start_col] = 0

    # List of frontier cells
    frontier = []
    for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        new_row, new_col = start_row + dr, start_col + dc
        if 0 < new_row < rows and 0 < new_col < cols:
            frontier.append((new_row, new_col, start_row, start_col))

    # Prim's Algorithm
    while frontier:
        # Randomly select a cell
        index = random.randint(0, len(frontier) - 1)
        new_row, new_col, parent_row, parent_col = frontier.pop(index)

        if maze[new_row][new_col] == 1:
            # Carve a path to the new cell
            maze[new_row][new_col] = 0
            # Carve a path through the wall between the new cell and its parent
            maze[(new_row + parent_row) // 2][(new_col + parent_col) // 2] = 0

            # Add new cells
            for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                next_row, next_col = new_row + dr, new_col + dc
                if 0 < next_row < rows and 0 < next_col < cols and maze[next_row][next_col] == 1:
                    frontier.append((next_row, next_col, new_row, new_col))
    print_maze(maze)
    return maze


# Update angle lookup tables
def update_angle_lookup():
    global angle_lookup, cos_lookup, sin_lookup
    angle_step = FOV / (NUM_RAYS - 1)  # Distribute rays evenly across FOV
    angle_lookup = [(player_angle - HALF_FOV + i * angle_step) for i in range(NUM_RAYS)]
    cos_lookup = [math.cos(angle) for angle in angle_lookup]
    sin_lookup = [math.sin(angle) for angle in angle_lookup]

# Initialize angle lookup tables
update_angle_lookup()


def cast_ray(angle, ray_id):
    x, y = player_x, player_y
    dx, dy = math.cos(angle), math.sin(angle)

    # Delta distances for DDA
    delta_x = abs(1 / dx) if dx != 0 else 1e30
    delta_y = abs(1 / dy) if dy != 0 else 1e30

    # Step direction and initial side distances
    step_x = 1 if dx > 0 else -1
    step_y = 1 if dy > 0 else -1
    side_x = (x - int(x)) * delta_x if dx < 0 else (int(x) + 1 - x) * delta_x
    side_y = (y - int(y)) * delta_y if dy < 0 else (int(y) + 1 - y) * delta_y

    # DDA
    for _ in range(MAX_DEPTH):
        if side_x < side_y:
            side_x += delta_x
            x += step_x
            dist = side_x - delta_x
            side = 0
        else:
            side_y += delta_y
            y += step_y
            dist = side_y - delta_y
            side = 1

        # If wall
        if scene[int(y)][int(x)]:
            return dist, scene[int(y)][int(x)], None

    return MAX_DEPTH, 1, None


brightness_factor = 1.0  # Default brightness
brightness_decreasing = True  
brightness_min = 0.05  # Minimum brightness
brightness_max = 1.0
brightness_speed = 0.09  # Speed for brightness change

def handle_input():
    global player_x, player_y, player_angle, orbs, brightness_factor, brightness_decreasing, c
    move_speed = 0.1
    rot_speed = 0.175

    # Scan for button state changes
    buttons.scan()

    if buttons.state(Buttons.C):
        Reset()

    # Forward
    if buttons.state(Buttons.Up):
        new_x = player_x + math.cos(player_angle) * move_speed
        new_y = player_y + math.sin(player_angle) * move_speed

        # Check if the new position is within the maze boundaries
        if 0 <= new_x < len(scene[0]) and 0 <= new_y < len(scene):
            if not scene[int(new_y)][int(new_x)]:
                player_x, player_y = new_x, new_y

    # Backward
    if buttons.state(Buttons.Down):
        new_x = player_x - math.cos(player_angle) * move_speed
        new_y = player_y - math.sin(player_angle) * move_speed

        # Check if the new position is within the maze boundaries
        if 0 <= new_x < len(scene[0]) and 0 <= new_y < len(scene):
            if not scene[int(new_y)][int(new_x)]:
                player_x, player_y = new_x, new_y

    # Rotate left
    if buttons.state(Buttons.Left):
        player_angle -= rot_speed
        update_angle_lookup()  # Update angle lookup

    # Rotate right
    if buttons.state(Buttons.Right):
        player_angle += rot_speed
        update_angle_lookup()  # Update angle lookup

    # Check for orb collection
    for orb in orbs[:]:
        orb_x, orb_y = orb

        # Check if the player is near the orb
        if orb_x - 1 <= player_x < orb_x + 1 and orb_y - 1 <= player_y < orb_y + 1:
            orbs.remove(orb)
            print(f"Orb collected at position ({orb_x}, {orb_y})!")

    # Location DEBUG
    if buttons.state(Buttons.B):
        print(player_x, "  ", player_y)

    if buttons.state(Buttons.A):
        brightness_factor = brightness_max

    # Gradually decrease brightness
    if brightness_decreasing:
        brightness_factor -= brightness_speed
        if brightness_factor <= brightness_min:
            brightness_factor = brightness_min

    # Gradually increase brightness back to normal
    if not brightness_decreasing and brightness_factor < brightness_max and False:
        brightness_factor += brightness_speed
        if brightness_factor > 1.0:
            brightness_factor = 1.0




def render(display):
    global brightness_factor
    display.fill(0)

    # Draw sky
    sky_brightness = max(0, min(1, brightness_factor))
    sky_color = adjust_color_brightness(SKY, sky_brightness)
    display.rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2, sky_color, True)

    # Create a depth buffer to store wall distances
    depth_buffer = [MAX_DEPTH] * SCREEN_WIDTH

    # Draw walls and orbs in a single pass
    for ray in range(NUM_RAYS):
        depth, wall_type, orb_data = cast_ray(angle_lookup[ray], ray)

        # Draw wall
        if wall_type > 0:  # Normal wall
            wall_height = int(SCREEN_HEIGHT / (depth + 0.0001))
            
            # Wall color calculation
            if wall_type == 1:
                base_red = 0xD1A9
                brightness = max(0, 1 - depth / MAX_DEPTH) * brightness_factor
                red = int((base_red >> 11) * brightness)
                wall_color = (red << 11)
            elif wall_type == 2:
                wall_color = GREEN
            elif wall_type == 3:
                wall_color = GRAY

            # Draw wall column
            display.rect(
                ray,  # Each ray corresponds to one pixel column
                (SCREEN_HEIGHT - wall_height) // 2,
                1,  # Each wall column is 1 pixel wide
                wall_height,
                wall_color,
                True
            )

            # Store the wall distance in the depth buffer
            depth_buffer[ray] = depth

        # Draw orb if one was found on this ray
        if orb_data:
            orb_dist, orb_index = orb_data
            orb_size = max(5, int(20 / orb_dist))
            screen_y = SCREEN_HEIGHT // 2

            # Calculate the exact screen position for the orb
            angle_to_orb = angle_lookup[ray]
            screen_x = int((angle_to_orb + HALF_FOV) * (SCREEN_WIDTH / FOV))

            # Check if the orb is behind the wall at this screen position
            if orb_dist < depth_buffer[screen_x]:
                display.rect(
                    screen_x - orb_size // 2,
                    screen_y - orb_size // 2,
                    orb_size,
                    orb_size,
                    ORB,
                    True
                )

    # Render orbs
    epsilon = 0.0001  # Small value to prevent division by zero
    for orb in orbs:
        orb_x, orb_y = orb

        # Calculate relative position to the player
        rel_x = orb_x - player_x
        rel_y = orb_y - player_y

        # Calculate distance and angle to the orb
        dist = math.sqrt(rel_x**2 + rel_y**2) + epsilon  # Add epsilon to avoid division by zero
        angle_to_orb = math.atan2(rel_y, rel_x) - player_angle

        # Normalize angle
        while angle_to_orb < -math.pi:
            angle_to_orb += 2 * math.pi
        while angle_to_orb > math.pi:
            angle_to_orb -= 2 * math.pi

        # Check if the orb is within the field of view
        if -HALF_FOV < angle_to_orb < HALF_FOV:
            # Calculate screen position
            screen_x = int((angle_to_orb + HALF_FOV) * (SCREEN_WIDTH / FOV))
            orb_size = max(5, int(20 / dist))  # Scale size based on distance
            screen_y = SCREEN_HEIGHT // 2

            # Check if the orb is behind the wall at this screen position
            if dist < depth_buffer[screen_x]:
                # Draw the orb
                display.rect(
                    screen_x - orb_size // 2,
                    screen_y - orb_size // 2,
                    orb_size,
                    orb_size,
                    ORB,
                    True
                )

    # Render multiplayer players
    for player in multiplayer_players:
        px, py = player["x"], player["y"]
        color = player["color"]

        # Calculate relative position to the player
        rel_x = px - player_x
        rel_y = py - player_y

        # Calculate distance and angle to the player
        dist = math.sqrt(rel_x**2 + rel_y**2) + epsilon  # Add epsilon to avoid division by zero
        angle_to_player = math.atan2(rel_y, rel_x) - player_angle

        # Normalize angle
        while angle_to_player < -math.pi:
            angle_to_player += 2 * math.pi
        while angle_to_player > math.pi:
            angle_to_player -= 2 * math.pi

        # Check if the player is within the field of view
        if -HALF_FOV < angle_to_player < HALF_FOV:
            # Calculate screen position
            screen_x = int((angle_to_player + HALF_FOV) * (SCREEN_WIDTH / FOV))
            player_size = max(5, int(40 / dist))  # Scale size based on distance

            # Check if the player is behind the wall at this screen position
            if dist < depth_buffer[screen_x]:
                # Draw the player
                display.rect(
                    screen_x - player_size // 2,
                    (SCREEN_HEIGHT // 2) - player_size // 2,
                    player_size,
                    player_size * 2,
                    color,
                    True
                )

    display.commit()
    
        
def NextLevel():
    global scene, player_x, player_y, player_angle

    # Check if the player is near the green wall
    if lvl1_x - 1 <= player_x < lvl1_x and lvl1_y - 1 <= player_y < lvl1_y:
        display.text(str("Press B"), int(6), int(64), 0)
        display.text(str("For next LVL"), int(6), int(72), 0)

        # If the player presses B, load the next level
        if buttons.state(Buttons.B):
            print("LVL Complete")
            scene = scene2  # Switch to the new scene
            player_x, player_y = 2, 2  # Teleport the player to the start
            player_angle = 0  
            update_angle_lookup()


def Reset():
    
    # Resets the game with a new maze and ensures the player starting position is valid.
    # Also places new orbs in the maze.
    
    global scene, player_x, player_y, player_angle, lvl1_x, lvl1_y
    
    # Generate new maze
    new_maze = generate_maze(21, 21)
    
    # Ensure the starting area is clear
    start_x, start_y = 1, 1  # Starting position
    
    # Clear a small area around the starting position
    for dy in range(0, 2):
        for dx in range(0, 2):
            if 0 <= start_y + dy < len(new_maze) and 0 <= start_x + dx < len(new_maze[0]):
                new_maze[start_y + dy][start_x + dx] = 0
    
    # Update the scene
    scene = new_maze
    
    # Place player at the cleared starting position
    player_x = float(start_x + 0.5)
    player_y = float(start_y + 0.5)
    player_angle = 45
    
    # Update angle lookup tables
    update_angle_lookup()
    
    # Place new orbs in the maze
    place_orbs(10)  # Place 5 orbs by default, adjust number as needed

    scene, lvl1_x, lvl1_y = find_and_update(scene, lvl1_x, lvl1_y)

    
    print("RESET TRIGGERED - New maze generated with clear starting area")

scene = generate_maze(21, 21)
place_orbs(10)

Reset()

# Main loop
running = True
while running:
    try:
        handle_input()
        render(display)
        display.text((str(player_x)+"  "+str(player_y)), 10, 10, WHITE)
        time.sleep_ms(30)  # Control frame rate
    except IndexError:
        # Catch index errors sometimes happens at player x/y larger than 45 because raycast out of array bounds
        # Fixed, i think
        print("Index Error at : ", player_x, "  ", player_y)
