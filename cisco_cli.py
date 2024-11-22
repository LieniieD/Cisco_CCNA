python

#! /usr/bin/python3
# Enhanced Cisco CLI Manager
# Author: Me and ChatGPT


import os
import logging
from netmiko import ConnectHandler
from typing import Optional, List
import click
from getpass import getpass

# Configure logging
logging.basicConfig(
    filename="cisco_cli.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Global connections storage
connections = []

# Utility Functions
def list_connections() -> None:
    """Print the list of saved connections."""
    if not connections:
        print("No saved connections.")
        return

    print("\nSaved Connections:")
    for idx, conn in enumerate(connections):
        print(f"{idx + 1}: Host {conn['host']} - Port {conn['port']} - Username {conn['username']}")
    print()

def save_connections_to_file(file_path: str = "connections.txt") -> None:
    """Save connections to a file."""
    with open(file_path, "w") as file:
        for conn in connections:
            file.write(f"{conn['host']} {conn['username']} {conn['port']}\n")
    print(f"Connections saved to {file_path}")

def load_connections_from_file(file_path: str = "connections.txt") -> None:
    """Load connections from a file."""
    global connections
    if not os.path.exists(file_path):
        print(f"No saved connections file found: {file_path}")
        return

    with open(file_path, "r") as file:
        for line in file:
            host, username, port = line.strip().split()
            connections.append({"host": host, "username": username, "port": port})
    print("Connections loaded.")

def get_device_type(connection) -> str:
    """Identify the device type based on 'show version' output."""
    output = connection.send_command("show version")
    if "IOS-XE" in output:
        return "cisco_ios"
    elif "NX-OS" in output:
        return "cisco_nxos"
    elif "IOS XR" in output:
        return "cisco_xr"
    else:
        return "unknown"

# Main CLI Application
@click.group()
def cli():
    """Cisco CLI Manager - A tool for managing Cisco devices."""
    pass

@cli.command()
def list_conns():
    """List all saved connections."""
    list_connections()

@cli.command()
@click.option('--host', prompt='Host', help='IP address of the Cisco device.')
@click.option('--username', prompt='Username', help='SSH username.')
@click.option('--port', default=22, help='SSH port (default 22).')
def new_connection(host: str, username: str, port: int):
    """Create a new connection."""
    global connections
    connections.append({"host": host, "username": username, "port": port})
    save_connections_to_file()
    print(f"New connection added: {host}:{port} - {username}")

@cli.command()
@click.option('--id', prompt='Connection ID', type=int, help='ID of the connection to delete.')
def del_conn(id: int):
    """Delete a saved connection."""
    global connections
    if 0 < id <= len(connections):
        deleted = connections.pop(id - 1)
        save_connections_to_file()
        print(f"Deleted connection: {deleted['host']}:{deleted['port']} - {deleted['username']}")
    else:
        print("Invalid connection ID.")

@cli.command()
@click.option('--id', prompt='Connection ID', type=int, help='ID of the connection to use.')
def connect(id: int):
    """Connect to a Cisco device."""
    global connections
    if 0 < id <= len(connections):
        conn = connections[id - 1]
        password = getpass("Enter SSH Password: ")
        try:
            device = {
                "device_type": "cisco_ios",
                "host": conn["host"],
                "username": conn["username"],
                "password": password,
                "port": conn["port"],
            }
            connection = ConnectHandler(**device)
            print(f"Connected to {conn['host']}")
            handle_device_session(connection)
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            print(f"Failed to connect: {e}")
    else:
        print("Invalid connection ID.")

def handle_device_session(connection) -> None:
    """Handle the session with the device."""
    while True:
        print("\nDevice Menu:")
        print("1: Run Command")
        print("2: Import and Execute Config")
        print("3: Save Config")
        print("4: Disconnect")
        try:
            choice = int(input("Choose an option: "))
            if choice == 1:
                command = input("Enter command: ")
                output = connection.send_command(command)
                print(output)
            elif choice == 2:
                config_file = input("Enter config file path: ")
                if os.path.exists(config_file):
                    with open(config_file, "r") as file:
                        commands = file.readlines()
                    for cmd in commands:
                        print(connection.send_command(cmd.strip()))
                else:
                    print("File not found.")
            elif choice == 3:
                output = connection.send_command("write memory")
                print(output)
            elif choice == 4:
                print("Disconnecting...")
                connection.disconnect()
                break
            else:
                print("Invalid choice.")
        except Exception as e:
            logging.error(f"Error during session: {e}")
            print(f"Error: {e}")

# Load connections at startup
load_connections_from_file()

# Entry point
if __name__ == "__main__":
    cli()
