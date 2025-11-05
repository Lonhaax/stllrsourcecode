# system_info.py
import platform
import psutil
import socket
import uuid
import os
import datetime
import json

def get_system_info():
    info = {}

    # Basic system info
    info['system'] = platform.system()
    info['node_name'] = platform.node()
    info['release'] = platform.release()
    info['version'] = platform.version()
    info['machine'] = platform.machine()
    info['processor'] = platform.processor()
    info['architecture'] = platform.architecture()[0]
    info['boot_time'] = str(datetime.datetime.fromtimestamp(psutil.boot_time()))

    # CPU info
    info['cpu_count_logical'] = psutil.cpu_count(logical=True)
    info['cpu_count_physical'] = psutil.cpu_count(logical=False)
    info['cpu_freq'] = psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
    info['cpu_percent'] = psutil.cpu_percent(interval=1)

    # Memory info
    info['virtual_memory'] = psutil.virtual_memory()._asdict()
    info['swap_memory'] = psutil.swap_memory()._asdict()

    # Disk info
    info['disk_partitions'] = [p._asdict() for p in psutil.disk_partitions()]
    info['disk_usage'] = psutil.disk_usage('/')._asdict()
    info['disk_io_counters'] = psutil.disk_io_counters()._asdict()

    # Network info
    info['hostname'] = socket.gethostname()
    info['ip_address'] = socket.gethostbyname(socket.gethostname())
    info['mac_address'] = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                                    for ele in range(0,8*6,8)][::-1])
    info['network_io_counters'] = psutil.net_io_counters()._asdict()
    info['network_interfaces'] = {name: [a.address for a in addrs] for name, addrs in psutil.net_if_addrs().items()}

    # Battery info
    if hasattr(psutil, "sensors_battery"):
        batt = psutil.sensors_battery()
        info['battery'] = batt._asdict() if batt else None

    # Environment info
    info['python_version'] = platform.python_version()
    info['python_build'] = platform.python_build()
    info['python_compiler'] = platform.python_compiler()
    info['environment_vars'] = dict(os.environ)

    return info


if __name__ == "__main__":
    data = get_system_info()

    # Build AppData\output path
    appdata_path = os.getenv('APPDATA')
    output_dir = os.path.join(appdata_path, 'output')
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, 'sys_info.txt')

    # Save data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

