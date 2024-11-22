python

from netmiko import ConnectHandler
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import logging
import json

# Налаштування логування
logging.basicConfig(
    filename="terminalnator.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Функція підключення до пристрою
def connect_to_device(host, username, password, device_type="cisco_ios", port=22, secret=None):
    device = {
        "device_type": device_type,
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "secret": secret,
    }
    try:
        connection = ConnectHandler(**device)
        if secret:
            connection.enable()  # Увімкнення привілейованого режиму, якщо є секрет
        logging.info(f"Connected to {host}:{port} as {username}")
        return connection
    except Exception as e:
        logging.error(f"Error connecting to {host}:{port} - {e}")
        messagebox.showerror("Connection Error", f"Could not connect to {host}. Error: {e}")
        return None


# Клас GUI
class TerminalnatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Terminalnator v2.0")
        self.root.geometry("500x400")

        # Список підключень
        self.connections = []
        self.load_connections()

        self.conn_list = ttk.Treeview(root, columns=("Host", "Port", "Username"), show="headings")
        self.conn_list.heading("Host", text="Host")
        self.conn_list.heading("Port", text="Port")
        self.conn_list.heading("Username", text="Username")
        self.conn_list.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.refresh_conn_list()

        # Кнопки
        self.btn_connect = ttk.Button(root, text="Connect", command=self.connect)
        self.btn_connect.pack(side=LEFT, padx=5, pady=5)

        self.btn_add = ttk.Button(root, text="Add", command=self.add_connection)
        self.btn_add.pack(side=LEFT, padx=5, pady=5)

        self.btn_delete = ttk.Button(root, text="Delete", command=self.delete_connection)
        self.btn_delete.pack(side=LEFT, padx=5, pady=5)

        self.btn_refresh = ttk.Button(root, text="Refresh", command=self.refresh_conn_list)
        self.btn_refresh.pack(side=LEFT, padx=5, pady=5)

    def load_connections(self):
        """Завантаження збережених підключень із файлу."""
        try:
            with open("connections.json", "r") as file:
                self.connections = json.load(file)
        except FileNotFoundError:
            self.connections = []

    def save_connections(self):
        """Збереження підключень у файл."""
        with open("connections.json", "w") as file:
            json.dump(self.connections, file)

    def refresh_conn_list(self):
        """Оновлення списку підключень у GUI."""
        for item in self.conn_list.get_children():
            self.conn_list.delete(item)

        for conn in self.connections:
            self.conn_list.insert("", "end", values=(conn["host"], conn["port"], conn["username"]))

    def add_connection(self):
        """Додавання нового підключення."""
        add_window = Toplevel(self.root)
        add_window.title("Add New Connection")
        add_window.geometry("300x250")

        # Поля для вводу даних
        Label(add_window, text="Host:").pack(pady=5)
        host_entry = Entry(add_window)
        host_entry.pack(pady=5)

        Label(add_window, text="Port:").pack(pady=5)
        port_entry = Entry(add_window)
        port_entry.pack(pady=5)

        Label(add_window, text="Username:").pack(pady=5)
        username_entry = Entry(add_window)
        username_entry.pack(pady=5)

        Label(add_window, text="Password:").pack(pady=5)
        password_entry = Entry(add_window, show="*")
        password_entry.pack(pady=5)

        def save_new_connection():
            host = host_entry.get()
            port = int(port_entry.get())
            username = username_entry.get()
            password = password_entry.get()

            if host and port and username and password:
                self.connections.append({
                    "host": host,
                    "port": port,
                    "username": username,
                    "password": password
                })
                self.save_connections()
                self.refresh_conn_list()
                add_window.destroy()
                messagebox.showinfo("Success", "Connection added successfully!")
            else:
                messagebox.showerror("Error", "All fields are required!")

        ttk.Button(add_window, text="Save", command=save_new_connection).pack(pady=10)

    def delete_connection(self):
        """Видалення обраного підключення."""
        selected_item = self.conn_list.focus()
        if not selected_item:
            messagebox.showerror("Error", "No connection selected!")
            return

        conn_values = self.conn_list.item(selected_item, "values")
        self.connections = [conn for conn in self.connections if conn["host"] != conn_values[0]]
        self.save_connections()
        self.refresh_conn_list()
        messagebox.showinfo("Success", "Connection deleted successfully!")

    def connect(self):
        """Підключення до обраного пристрою."""
        selected_item = self.conn_list.focus()
        if not selected_item:
            messagebox.showerror("Error", "No connection selected!")
            return

        conn_values = self.conn_list.item(selected_item, "values")
        conn = next((c for c in self.connections if c["host"] == conn_values[0]), None)
        if not conn:
            messagebox.showerror("Error", "Connection not found!")
            return

        connection = connect_to_device(
            host=conn["host"],
            username=conn["username"],
            password=conn["password"],
            port=conn["port"]
        )
        if connection:
            self.open_command_window(connection)

    def open_command_window(self, connection):
        """Вікно для введення та виконання команд."""
        cmd_window = Toplevel(self.root)
        cmd_window.title("Execute Commands")
        cmd_window.geometry("400x300")

        cmd_label = Label(cmd_window, text="Enter command:")
        cmd_label.pack(pady=5)

        cmd_entry = Entry(cmd_window)
        cmd_entry.pack(pady=5)

        output_text = Text(cmd_window, wrap=WORD, height=15, width=50)
        output_text.pack(pady=5)

        def execute_command():
            command = cmd_entry.get()
            if command:
                try:
                    output = connection.send_command(command)
                    output_text.insert(END, f"\n> {command}\n{output}\n")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to execute command: {e}")

        ttk.Button(cmd_window, text="Run", command=execute_command).pack(pady=5)

        def disconnect():
            connection.disconnect()
            cmd_window.destroy()
            messagebox.showinfo("Disconnected", "Connection closed!")

        ttk.Button(cmd_window, text="Disconnect", command=disconnect).pack(pady=5)


# Головне вікно програми
if __name__ == "__main__":
    root = Tk()
    app = TerminalnatorGUI(root)
    root.mainloop()
