import os
import platform
import shutil
import requests
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime

CONFIG_FILE = 'config.json'

def get_hosts_file_path():
    if platform.system() == 'Windows':
        path = r'C:\blocked_hosts\hosts'
    else:
        path = '/etc/blocked_hosts/hosts'
    return path

def ensure_directory_exists(path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def backup_hosts_file(hosts_path):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = f"{hosts_path}_backup_{timestamp}"
    try:
        shutil.copy2(hosts_path, backup_path)
        shutil.copy2(hosts_path, 'hosts_last_used')
        return backup_path
    except FileNotFoundError:
        messagebox.showerror("Error", f"Hosts file not found at {hosts_path}. Creating a new one.")
        ensure_directory_exists(hosts_path)
        open(hosts_path, 'w').close()  # Create an empty hosts file
        backup_hosts_file(hosts_path)  # Retry backing up the newly created hosts file
    except PermissionError:
        messagebox.showerror("Error", f"Permission denied: Unable to access {hosts_path}. Please run the script as an administrator.")
        raise

def restore_hosts_file():
    hosts_path = get_hosts_file_path()
    if os.path.exists('hosts_last_used'):
        shutil.copy2('hosts_last_used', hosts_path)
        messagebox.showinfo("Restore", "Hosts file restored to the last used state.")
    else:
        messagebox.showerror("Restore", "No backup found to restore.")

def download_and_parse_lists(urls):
    domains = {
        'malicious': set(),
        'advertisement': set(),
        'malware': set(),
        'tracking': set()
    }

    for url in urls:
        try:
            print(f"Downloading from {url}...")
            response = requests.get(url)
            response.raise_for_status()
            
            print(f"Content from {url}:\n{response.text[:500]}...\n")  # Print first 500 characters
            
            for line in response.text.splitlines():
                line = line.strip()
                domain_type = None
                
                if 'malicious' in url:
                    domain_type = 'malicious'
                elif 'ads-and-tracking' in url:
                    domain_type = 'advertisement'
                elif 'malware' in url:
                    domain_type = 'malware'
                elif 'tracking' in url:
                    domain_type = 'tracking'
                
                if domain_type and (line.startswith('0.0.0.0') or line.startswith('127.0.0.1')):
                    parts = line.split()
                    if len(parts) > 1:
                        domain = parts[1]
                        domains[domain_type].add(domain)
        except requests.RequestException as e:
            print(f"Failed to download {url}: {e}")
    
    print(f"Collected domains: {domains}")
    return domains

def append_to_hosts_file(hosts_path, domains):
    with open(hosts_path, 'a') as hosts_file:
        for domain_type, domain_set in domains.items():
            if domain_set:
                hosts_file.write(f"\n# {domain_type.capitalize()} domains\n")
                hosts_file.write('\n'.join(f"0.0.0.0 {domain}" for domain in domain_set) + '\n')
    print(f"Appended domains to hosts file: {domains}")

def update_hosts_file(block_ads, block_malware, block_tracking, block_malicious, log_text):
    with open(CONFIG_FILE, 'r') as file:
        config = json.load(file)

    urls = []
    if block_ads:
        urls.extend(config.get('ad_block_lists', []))
    if block_malware:
        urls.extend(config.get('malware_block_lists', []))
    if block_tracking:
        urls.extend(config.get('tracking_block_lists', []))
    if block_malicious:
        urls.extend(config.get('malicious_block_lists', []))

    if not urls:
        messagebox.showerror("Error", "No block lists selected.")
        return

    domains = download_and_parse_lists(urls)
    hosts_path = get_hosts_file_path()
    try:
        backup_hosts_file(hosts_path)
        append_to_hosts_file(hosts_path, domains)
        messagebox.showinfo("Success", "Hosts file updated successfully.")
    except PermissionError:
        return

def create_gui():
    root = tk.Tk()
    root.title("Hosts-Based Domain Blocker")
    root.geometry('400x300')
    root.configure(bg='lightgrey')

    frame = ttk.Frame(root, padding="10")
    frame.pack(fill='both', expand=True)

    label = ttk.Label(frame, text="Select the types of content to block:")
    label.grid(row=0, column=0, columnspan=2, pady=10)

    block_ads = tk.BooleanVar()
    block_malware = tk.BooleanVar()
    block_tracking = tk.BooleanVar()
    block_malicious = tk.BooleanVar()

    ttk.Checkbutton(frame, text="Advertisements", variable=block_ads).grid(row=1, column=0, sticky='w')
    ttk.Checkbutton(frame, text="Malware", variable=block_malware).grid(row=2, column=0, sticky='w')
    ttk.Checkbutton(frame, text="Tracking", variable=block_tracking).grid(row=3, column=0, sticky='w')
    ttk.Checkbutton(frame, text="Malicious", variable=block_malicious).grid(row=4, column=0, sticky='w')

    log_text = tk.Text(frame, height=10, wrap='word')
    log_text.grid(row=5, column=0, columnspan=2, pady=10, sticky='nsew')

    frame.grid_rowconfigure(5, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    update_button = ttk.Button(frame, text="Update Hosts File", command=lambda: update_hosts_file(block_ads.get(), block_malware.get(), block_tracking.get(), block_malicious.get(), log_text))
    update_button.grid(row=6, column=0, pady=10)

    restore_button = ttk.Button(frame, text="Restore Hosts File", command=restore_hosts_file)
    restore_button.grid(row=6, column=1, pady=10)

    root.mainloop()

if __name__ == '__main__':
    create_gui()
