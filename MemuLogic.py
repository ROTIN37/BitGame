from Bit import *
import time
import math
import network
import socket
import json

from framebuf import FrameBuffer, RGB565

# Initialize
begin()

SCREEN_WIDTH = 150
SCREEN_HEIGHT = 130
SCREEN_WIDTHR = 130

buttonWidth = 100
buttonWidthT = 80
buttonHeight = 15

difficulty = 0




n = 3
raySel = 3
FOV = math.pi / n 

menuButtons = ["Solo", "Multiplayer", "Settings"]
selectedButton = 0
current_menu = 0  # 0 = main_menu, 1 = solo_menu, 2 = multiplayer_menu, 3 = settings_menu

sfxToggle = False
musicToggle = True

WHITE = 0xFFFF
GRAY = 0xAD55
LGRAY = 0xEF7D
LAVANDER = 0x625B
CLIENT_COLOR = 0xF660  # Color for connected clients

# Network and client-related variables
INVISIBLE_SSID = False  # Set to True to make the SSID invisible
MAX_CLIENTS = 6
IP_BASE = "192.168.4."
IP_RANGE = range(2, 2 + MAX_CLIENTS)  # IPs from 192.168.4.2 to 192.168.4.8

# Player positions (to be synced across network)
player_positions = {
    # Format: 'player_id': [x, y]
    # Will be populated as clients connect
}

# Sockets for communication
server_socket = None
client_socket = None
connected_clients = set()  # Set of connected client addresses
is_host = False  # Flag to track if we are host or client

# Buffer for network communication
buffer_size = 1024


def zfill(s, width):
    """Pad a string with leading zeros to the specified width."""
    return ('0' * (width - len(s))) + s


# Define menu hierarchy
menu_hierarchy = {
    0: {"name": "Main Menu", "submenus": [1, 2, 3]},  # Main menu has submenus Solo, Multiplayer, Settings
    1: {"name": "Solo Menu", "submenus": [12, 11]},  # Solo menu has Start and Difficulty submenu
    2: {"name": "Multiplayer Menu", "submenus": [4, 5]},  # Multiplayer menu has submenus Host, Connect
    3: {"name": "Settings Menu", "submenus": [6, 7]},  # Settings menu has submenus Graphics, Sound
    4: {"name": "Host Menu", "submenus": [10]},  # Host menu now has a submenu for Lobby
    5: {"name": "Connect Menu", "submenus": [10]},  # Connect menu now has a submenu for Lobby
    6: {"name": "Graphics Menu", "submenus": [8, 9]},  # Graphics menu has submenus Ray Count, FOV
    7: {"name": "Sound Menu", "submenus": []},  # Sound menu has no submenus
    8: {"name": "Ray Count Menu", "submenus": []},  # Ray Count menu has no submenus
    9: {"name": "FOV Menu", "submenus": []},  # FOV menu has no submenus
    10: {"name": "Lobby Menu", "submenus": []},  # New Lobby menu
}


def buttonScroll(lista):
    global selectedButton, current_menu

    buttons.scan()
    if buttons.state(Buttons.A):
        if selectedButton == len(lista) - 1:  # "Back" button
            current_menu = 0  # Return to main menu
            selectedButton = 0  # Reset selected button
        else:
            # Navigate to the selected submenu
            submenus = menu_hierarchy[current_menu]["submenus"]
            if selectedButton < len(submenus):
                current_menu = submenus[selectedButton]
                selectedButton = 0

    if buttons.state(Buttons.Up):
        selectedButton -= 1
    
    if buttons.state(Buttons.Down):
        selectedButton += 1

    # Wrap around selectedButton
    if selectedButton < 0:
        selectedButton = len(lista) - 1
    if selectedButton >= len(lista):
        selectedButton = 0

    time.sleep(0.2)


def buttonSpace(buttonList):
    global selectedButton

    # Calculate spacing between buttons
    totalButtonHeight = len(buttonList) * buttonHeight
    spacing = (SCREEN_HEIGHT - totalButtonHeight) // (len(buttonList) + 1)

    for index in range(len(buttonList)):
        yButton = (spacing + buttonHeight) * index + spacing
        xButton = (SCREEN_WIDTHR - buttonWidth) // 2

        yText = yButton + (buttonHeight // 4) + 1
        xText = xButton + 2

        if index == selectedButton:
            display.rect(xButton, yButton, buttonWidth, buttonHeight, LAVANDER, True)
            display.text(buttonList[index], xText, yText, 0)
        else:
            display.rect(xButton, yButton, buttonWidth, buttonHeight, GRAY, True)
            display.text(buttonList[index], xText, yText, 0)


def buttonSpaceToggles(buttonList, tg1, tg2):
    global selectedButton

    # Calculate spacing between buttons
    totalButtonHeight = len(buttonList) * buttonHeight
    spacing = (SCREEN_HEIGHT - totalButtonHeight) // (len(buttonList) + 1)

    for index in range(len(buttonList)):
        yButton = (spacing + buttonHeight) * index + spacing
        xButton = (SCREEN_WIDTHR - buttonWidthT) // 2

        yText = yButton + (buttonHeight // 4) + 1
        xText = xButton + 2

        if index == selectedButton:
            display.rect(xButton, yButton, buttonWidthT, buttonHeight, LAVANDER, True)
            display.text(buttonList[index], xText, yText, 0)

        else:
            display.rect(xButton, yButton, buttonWidthT, buttonHeight, GRAY, True)
            display.text(buttonList[index], xText, yText, 0)

        if tg1 and index == 0:
            display.rect(xButton+buttonWidthT+5, yButton, 15, buttonHeight, GRAY, True)
        elif index == 0:
            display.rect(xButton+buttonWidthT+5, yButton, 15, buttonHeight, GRAY, False)

        if tg2 and index == 1:
            display.rect(xButton+buttonWidthT+5, yButton, 15, buttonHeight, GRAY, True)
        elif index == 1:
            display.rect(xButton+buttonWidthT+5, yButton, 15, buttonHeight, GRAY, False)


def main_menu():
    global selectedButton

    

    display.fill(0)
    buttonSpace(menuButtons)

    display.commit()


def solo_menu():
    global selectedButton

    display.fill(0)
    display.text("SOLO", (SCREEN_WIDTHR // 2) - 14, 10, WHITE)

    multiplayerButtons1 = ["Start", "Difficulty", "Back"]
    buttonSpace(multiplayerButtons1)
    buttonScroll(multiplayerButtons1)


    display.commit()

    # Handle input for solo menu
    buttons.scan()
    if buttons.state(Buttons.B):  # Example: Go back to main menu
        global current_menu
        current_menu = 0
        selectedButton = 0


def difficulty_menu():
    global difficulty

    names = ["Baby", "Easy", "Normal", "Hard", "Torture"]

    buttons.scan()

    display.fill(0)
    display.text("< B", 5, 5, WHITE)

    if buttons.state(Buttons.Left):
        difficulty -= 1
        if difficulty < 0:
            difficulty = 4
        time.sleep(0.2)

    if buttons.state(Buttons.Right):
        difficulty += 1
        if difficulty > 4:
            difficulty = 0
        time.sleep(0.2)

    if buttons.state(Buttons.B):  # Go back to the previous menu
        global current_menu
        current_menu = 1  # Go back to the Graphics menu
        selectedButton = 0  # Reset selected button
        return  # Exit the function to avoid further processing

    display.text("Difficulty", round(SCREEN_WIDTHR // (1/0.3)), 25, WHITE)
    difficultyValue = f"< {names[difficulty]} >"
    difficultyValueWidth = (len(difficultyValue*6))+((len(difficultyValue)-1)*2)
    xDifficultyValue = (SCREEN_WIDTHR - difficultyValueWidth) // 2
    display.text(difficultyValue, xDifficultyValue, 64, WHITE)


    display.commit()




def starting_menu():
    if buttons.state(Buttons.B):  # Go back to the previous menu
        global current_menu
        current_menu = 1  # Go back to the Graphics menu
        selectedButton = 0  # Reset selected button
        return  # Exit the function to avoid further processing









def multiplayer_menu():
    global selectedButton

    display.fill(0)
    display.text("MULTIPLAYER", 20, 10, WHITE)
    
    multiplayerButtons1 = ["Host", "Connect", "Back"]
    buttonSpace(multiplayerButtons1)
    buttonScroll(multiplayerButtons1)  # Ensure buttonScroll is called
    display.commit()


# Generate SSID for the network
def generate_ssid(number):
    return f"{number}MultConn"


# Validate number input
def validate_number(input_str):
    return input_str.isdigit() and len(input_str) == 4


# Initialize server and start listening for connections
def init_server():
    global server_socket, is_host
    
    # Create a socket and bind it to all available interfaces on port 8080
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 8080))
    server_socket.listen(MAX_CLIENTS)
    server_socket.setblocking(False)  # Set to non-blocking mode
    
    is_host = True
    print("Server initialized, listening for connections...")


# Initialize client and connect to server
def init_client(server_ip):
    global client_socket, is_host
    
    # Create a socket and connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, 8080))
    
    is_host = False
    print(f"Connected to server at {server_ip}")


# Check for new client connections (host only)
def check_for_connections():
    global server_socket, connected_clients
    
    try:
        client, addr = server_socket.accept()
        connected_clients.add(addr[0])
        print(f"New client connected: {addr[0]}")
        client.setblocking(False)  # Set client socket to non-blocking
        return client
    except:
        return None  # No new connections


# Send player positions to all clients (host only)
def send_positions_to_clients():
    global player_positions, connected_clients
    
    if not is_host:
        return
    
    # Prepare data
    data = json.dumps(player_positions).encode()
    
    # Send to all clients
    for client_addr in connected_clients:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((client_addr, 8080))
            client_socket.sendall(data)
            client_socket.close()
        except Exception as e:
            print(f"Error sending to {client_addr}: {e}")


# Receive data from server (client only)
def receive_data_from_server():
    global client_socket, player_positions
    
    if is_host:
        return
    
    try:
        data = client_socket.recv(buffer_size)
        if data:
            player_positions = json.loads(data.decode())
            print("Received updated player positions")
    except:
        pass  # No data available


# Update local player position and sync with network
def update_player_position(player_id, x, y):
    global player_positions
    
    # Update local copy
    player_positions[player_id] = [x, y]
    
    # Sync across network
    if is_host:
        send_positions_to_clients()
    else:
        # Clients send their position to the host
        if client_socket:
            data = json.dumps({player_id: [x, y]}).encode()
            try:
                client_socket.sendall(data)
            except Exception as e:
                print(f"Error sending position update: {e}")


# Host menu with SSID and password selection
host_ssid = "0000"
host_password = "0000"
def host_menu():
    global host_ssid, host_password, current_menu

    # Step 1: Choose SSID
    display.fill(0)
    display.text("Choose SSID", 10, 10, WHITE)
    display.text("(0000-9999):", 10, 25, WHITE)
    display.text(host_ssid, 10, 45, WHITE)
    display.text("A: Confirm", 10, 70, WHITE)
    display.commit()

    while True:
        buttons.scan()
        if buttons.state(Buttons.Up):
            host_ssid = str((int(host_ssid) + 1) % 10000)
            host_ssid = zfill(host_ssid, 4)
            display.fill(0)
            display.text("Choose SSID", 10, 10, WHITE)
            display.text("(0000-9999):", 10, 25, WHITE)
            display.text(host_ssid, 10, 45, WHITE)
            display.text("A: Confirm", 10, 70, WHITE)
            display.commit()
            time.sleep(0.2)

        if buttons.state(Buttons.Down):
            host_ssid = str((int(host_ssid) - 1) % 10000)
            host_ssid = zfill(host_ssid, 4)
            display.fill(0)
            display.text("Choose SSID", 10, 10, WHITE)
            display.text("(0000-9999):", 10, 25, WHITE)
            display.text(host_ssid, 10, 45, WHITE)
            display.text("A: Confirm", 10, 70, WHITE)
            display.commit()
            time.sleep(0.2)

        if buttons.state(Buttons.A):
            # Add a delay to prevent accidental input
            time.sleep(1)
            break  # Confirm SSID

    # Step 2: Set Password
    display.fill(0)
    display.text("Set Password", 10, 10, WHITE)
    display.text("(0000-9999):", 10, 25, WHITE)
    display.text(host_password, 10, 45, WHITE)
    display.text("A: Confirm", 10, 70, WHITE)
    display.commit()

    while True:
        buttons.scan()
        if buttons.state(Buttons.Up):
            host_password = str((int(host_password) + 1) % 10000)
            host_password = zfill(host_password, 4)
            display.fill(0)
            display.text("Set Password", 10, 10, WHITE)
            display.text("(0000-9999):", 10, 25, WHITE)
            display.text(host_password, 10, 45, WHITE)
            display.text("A: Confirm", 10, 70, WHITE)
            display.commit()
            time.sleep(0.2)

        if buttons.state(Buttons.Down):
            host_password = str((int(host_password) - 1) % 10000)
            host_password = zfill(host_password, 4)
            display.fill(0)
            display.text("Set Password", 10, 10, WHITE)
            display.text("(0000-9999):", 10, 25, WHITE)
            display.text(host_password, 10, 45, WHITE)
            display.text("A: Confirm", 10, 70, WHITE)
            display.commit()
            time.sleep(0.2)

        if buttons.state(Buttons.A):
            break  # Confirm Password

    # Create network
    ssid = generate_ssid(host_ssid)
    password = host_password * 2  # Repeat password twice

    # Configure Access Point (AP)
    wifi_ap = network.WLAN(network.AP_IF)  # For hosting the network
    wifi_ap.active(True)  # Activate AP mode
    
    # Set SSID, password with proper authentication mode
    wifi_ap.config(essid=ssid, 
                  password=password, 
                  authmode=network.AUTH_WPA_WPA2_PSK,  # Added explicit auth mode
                  hidden=INVISIBLE_SSID)

    # Initialize server for client connections
    init_server()

    display.fill(0)
    display.text("Creating network...", 10, 10, WHITE)
    display.text("SSID:", 10, 30, WHITE)
    display.text(ssid, 10, 45, WHITE)
    display.text("Password:", 10, 65, WHITE)
    display.text(password, 10, 80, WHITE)
    display.commit()

    # Wait for network to be created
    time.sleep(2)

    display.fill(0)
    display.text("Network created!", 10, 10, WHITE)
    display.commit()
    time.sleep(1)
    
    # Initialize player_positions with host as player 1
    player_positions["host"] = [SCREEN_WIDTH//2, SCREEN_HEIGHT//2]
    
    # Move to the lobby menu
    current_menu = 10
    selectedButton = 0


# Connect menu with network selection and password entry
selected_network = "0000"
connect_password = "0000"
def connect_menu():
    global selected_network, connect_password, current_menu

    # Step 1: Choose Network
    display.fill(0)
    display.text("Choose Network", 10, 10, WHITE)
    display.text("(0000-9999):", 10, 25, WHITE)
    display.text(selected_network, 10, 45, WHITE)
    display.text("A: Confirm", 10, 70, WHITE)
    display.commit()

    while True:
        buttons.scan()
        if buttons.state(Buttons.Up):
            selected_network = str((int(selected_network) + 1) % 10000)
            selected_network = zfill(selected_network, 4)
            display.fill(0)
            display.text("Choose Network", 10, 10, WHITE)
            display.text("(0000-9999):", 10, 25, WHITE)
            display.text(selected_network, 10, 45, WHITE)
            display.text("A: Confirm", 10, 70, WHITE)
            display.commit()
            time.sleep(0.2)

        if buttons.state(Buttons.Down):
            selected_network = str((int(selected_network) - 1) % 10000)
            selected_network = zfill(selected_network, 4)
            display.fill(0)
            display.text("Choose Network", 10, 10, WHITE)
            display.text("(0000-9999):", 10, 25, WHITE)
            display.text(selected_network, 10, 45, WHITE)
            display.text("A: Confirm", 10, 70, WHITE)
            display.commit()
            time.sleep(0.2)

        if buttons.state(Buttons.A):
            # Add a delay to prevent accidental input
            time.sleep(1)
            break  # Confirm Network

    # Step 2: Enter Password
    display.fill(0)
    display.text("Enter Password", 10, 10, WHITE)
    display.text("(0000-9999):", 10, 25, WHITE)
    display.text(connect_password, 10, 45, WHITE)
    display.text("A: Confirm", 10, 70, WHITE)
    display.commit()

    while True:
        buttons.scan()
        if buttons.state(Buttons.Up):
            connect_password = str((int(connect_password) + 1) % 10000)
            connect_password = zfill(connect_password, 4)
            display.fill(0)
            display.text("Enter Password", 10, 10, WHITE)
            display.text("(0000-9999):", 10, 25, WHITE)
            display.text(connect_password, 10, 45, WHITE)
            display.text("A: Confirm", 10, 70, WHITE)
            display.commit()
            time.sleep(0.2)

        if buttons.state(Buttons.Down):
            connect_password = str((int(connect_password) - 1) % 10000)
            connect_password = zfill(connect_password, 4)
            display.fill(0)
            display.text("Enter Password", 10, 10, WHITE)
            display.text("(0000-9999):", 10, 25, WHITE)
            display.text(connect_password, 10, 45, WHITE)
            display.text("A: Confirm", 10, 70, WHITE)
            display.commit()
            time.sleep(0.2)

        if buttons.state(Buttons.A):
            break  # Confirm Password

    # Attempt to connect
    ssid = generate_ssid(selected_network)
    password = connect_password * 2  # Repeat password twice

    # Configure Station (STA) mode
    wifi_sta = network.WLAN(network.STA_IF)  # For connecting to a network
    wifi_sta.active(True)  # Activate STA mode
    wifi_sta.connect(ssid, password)  # Connect to the network

    display.fill(0)
    display.text("Connecting...", 10, 10, WHITE)
    display.text("SSID:", 10, 30, WHITE)
    display.text(ssid, 10, 45, WHITE)
    display.text("Password:", 10, 65, WHITE)
    display.text(password, 10, 80, WHITE)
    display.commit()

    # Wait for connection
    timeout = 0
    while not wifi_sta.isconnected() and timeout < 20:  # 10 second timeout
        time.sleep(0.5)
        timeout += 1
    
    if wifi_sta.isconnected():
        display.fill(0)
        display.text("Connected!", 10, 10, WHITE)
        ip = wifi_sta.ifconfig()[0]
        display.text(f"IP: {ip}", 10, 30, WHITE)
        display.commit()
        time.sleep(1)
        
        # Connect to the server (host device)
        # Get server IP (first 3 octets of our IP + .1)
        ip_parts = ip.split('.')
        server_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"
        init_client(server_ip)
        
        # Get client number (will be assigned by server)
        # For now, we're simplifying by using client_id instead of number
        client_id = "client"
        player_positions[client_id] = [SCREEN_WIDTH//2, SCREEN_HEIGHT//2]
            
        # Move to the lobby menu
        current_menu = 10
        selectedButton = 0
    else:
        display.fill(0)
        display.text("Connection failed!", 10, 10, WHITE)
        display.text("Press B to go back", 10, 30, WHITE)
        display.commit()
        
        while True:
            buttons.scan()
            if buttons.state(Buttons.B):
                current_menu = 2  # Back to multiplayer menu
                selectedButton = 0
                break


# New Lobby Menu
def lobby_menu():
    global player_positions, connected_clients
    
    # Update connections if host
    if is_host:
        new_client = check_for_connections()
        if new_client:
            # Assign new client a player ID
            client_id = f"client_{len(connected_clients)}"
            player_positions[client_id] = [SCREEN_WIDTH//2, SCREEN_HEIGHT//2]
    else:
        # If client, receive updates from host
        receive_data_from_server()
    
    display.fill(0)
    display.text("LOBBY", (SCREEN_WIDTHR - 30) // 2, 10, WHITE)
    
    # Display player slots
    display.text("Players:", 20, 30, WHITE)
    
    # Always show "host" in the connected color when hosting
    if is_host:
        display.text("1:Host", 30, 50, CLIENT_COLOR)
    else:
        # Check if host is in player_positions
        if "host" in player_positions:
            display.text("1:Host", 30, 50, CLIENT_COLOR)
        else:
            display.text("1:Host", 30, 50, GRAY)
    
    # Show client slots
    for i in range(2, MAX_CLIENTS + 2):
        x_pos = 30 + ((i-2) % 3) * 30  # Arrange in a grid, 3 per row
        y_pos = 70 + ((i-2) // 3) * 20  # New row every 3 players
        
        client_id = f"client_{i-2}"
        
        # Color depending on connection status
        if client_id in player_positions:
            display.text(f"{i}", x_pos, y_pos, CLIENT_COLOR)  # Connected - special color
        else:
            display.text(f"{i}", x_pos, y_pos, GRAY)  # Disconnected - gray
    
    # Display back option
    display.text("B: Back", 10, SCREEN_HEIGHT - 10, WHITE)
    
    # Check for start game button (host only)
    if is_host:
        display.text("A: Start", 10, SCREEN_HEIGHT - 20, WHITE)
    
    display.commit()
    
    # Handle input
    buttons.scan()
    if buttons.state(Buttons.B):
        if is_host:
            # Close connections
            if server_socket:
                server_socket.close()
                
            # Disable AP mode
            wifi_ap = network.WLAN(network.AP_IF)
            wifi_ap.active(False)
        else:
            # Close connection
            if client_socket:
                client_socket.close()
                
            # Disable STA mode
            wifi_sta = network.WLAN(network.STA_IF)
            wifi_sta.active(False)
        
        # Return to multiplayer menu
        global current_menu
        current_menu = 2
        selectedButton = 0
        
        # Reset player positions
        player_positions = {}
        connected_clients = set()
        
    # Start game (host only)
    if is_host and buttons.state(Buttons.A) and len(player_positions) > 0:
        # Would transition to game state here
        pass
    
    time.sleep(0.2)


def settings_menu():
    global selectedButton

    display.fill(0)
    settingsButtons = ["Graphics", "Sound", "Back"]
    buttonSpace(settingsButtons)
    buttonScroll(settingsButtons)
    display.commit()


def sound_menu():
    global selectedButton, sfxToggle, musicToggle

    display.fill(0)
    settingsButtons = ["Sfx", "Music", "Back"]
    buttonSpaceToggles(settingsButtons, sfxToggle, musicToggle)
    buttonScroll(settingsButtons)
    display.commit()

    if selectedButton == 0 and buttons.state(Buttons.A):
        sfxToggle = not sfxToggle
    
    if selectedButton == 1 and buttons.state(Buttons.A):
        musicToggle = not musicToggle


def graphics_menu():
    global selectedButton

    display.fill(0)
    settingsButtons = ["Ray Count", "FOV", "Back"]
    buttonSpace(settingsButtons)
    buttonScroll(settingsButtons)
    display.commit()


def ray_menu():
    global NUM_RAYS, raySel
    display.fill(0)

    possibleRays = (15, 25, 30, 50, 75, 150)

    buttons.scan()

    display.text("< B", 5, 5, WHITE)

    if buttons.state(Buttons.Left):
        raySel -= 1
        if raySel < 0:
            raySel = 5
        time.sleep(0.2)

    if buttons.state(Buttons.Right):
        raySel += 1
        if raySel > 5:
            raySel = 0
        time.sleep(0.2)

    if buttons.state(Buttons.B):  # Go back to the previous menu
        global current_menu
        current_menu = 6  # Go back to the Graphics menu
        selectedButton = 0  # Reset selected button
        return  # Exit the function to avoid further processing

    # Center "Ray Count" text
    text = "Ray Count"
    text_width = (len(text) * 6) + ((len(text) - 1) * 2)
    x_text = (SCREEN_WIDTHR - text_width) // 2
    display.text(text, x_text, 32, WHITE)

    # Center ray count value
    ray_value = f"< {possibleRays[raySel]} >"
    ray_value_width = (len(ray_value) * 6) + ((len(ray_value) - 1) * 2)
    x_ray_value = (SCREEN_WIDTHR - ray_value_width) // 2
    display.text(ray_value, x_ray_value, 64, WHITE)

    display.commit()


def fov_menu():
    global n
    display.fill(0)

    FOVn = 60 * (4 - n)

    display.text("< B", 5, 5, WHITE)

    # Center "FOV" text
    text = "FOV"
    text_width = (len(text) * 6) + ((len(text) - 1) * 2)
    x_text = (SCREEN_WIDTHR - text_width) // 2
    display.text(text, x_text, 32, WHITE)

    # Center FOV value
    fov_value = f"< {FOVn} >"
    fov_value_width = (len(fov_value) * 6) + ((len(fov_value) - 1) * 2)
    x_fov_value = (SCREEN_WIDTHR - fov_value_width) // 2
    display.text(fov_value, x_fov_value, 64, WHITE)

    buttons.scan()

    if buttons.state(Buttons.Left):
        n += 1
        if n > 3:
            n = 1
        time.sleep(0.2)
        # Caps FOV at 60 deg

    if buttons.state(Buttons.Right):
        n -= 1
        if n < 1:
            n = 3
        time.sleep(0.2)
        # Caps FOV at 180 deg

    if buttons.state(Buttons.B):  # Go back to the previous menu
        global current_menu
        current_menu = 6  # Go back to the Graphics menu
        selectedButton = 0  # Reset selected button
        return  # Exit the function to avoid further processing

    display.commit()


# Define menus array AFTER the functions are defined
menus = {
    0: main_menu,
    1: solo_menu,
    2: multiplayer_menu,
    3: settings_menu,
    4: host_menu, 
    5: connect_menu, 
    6: graphics_menu,
    7: sound_menu,
    8: ray_menu,
    9: fov_menu,
    10: lobby_menu,
    11: difficulty_menu,
    12: starting_menu
}






def menu_controll():
    global selectedButton, current_menu

    # Scan for button state changes
    buttons.scan()

    if buttons.state(Buttons.Up):
        selectedButton -= 1
    
    if buttons.state(Buttons.Down):
        selectedButton += 1

    # Wrap around selectedButton
    if selectedButton < 0:
        selectedButton = len(menuButtons) - 1
    if selectedButton >= len(menuButtons):
        selectedButton = 0

    # Handle button A press to switch menus
    if buttons.state(Buttons.A):
        if current_menu == 0:  # Only handle menu switching in the main menu
            submenus = menu_hierarchy[current_menu]["submenus"]
            if selectedButton < len(submenus):
                current_menu = submenus[selectedButton]
                selectedButton = 0

    time.sleep(0.2)


# Main game loop
while True: 
    if current_menu == 0:  # Only call menu_controll in the main menu
        menu_controll()
    menus[current_menu]()  # Call the current menu function