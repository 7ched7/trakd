# TRAKD  

![Version](https://img.shields.io/badge/version-0.5.0-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

**Trakd** is a lightweight and socket-based CLI (Command Line Interface) program tracking and time reporting tool. Ideal for anyone looking to better manage their time, understand how much time is spent on different programs, and monitor process activity directly from the terminal.

**Why Trakd?**
* **Minimal and fast** - No GUI distractions
* **Local-first** - Your data stays on your machine
* **Terminal-focused** - Tailored for terminal lovers
* **Scriptable & Automation-ready** – Easily integrate into cron jobs or custom scripts
* **Insightful reports** - View daily or weekly usage breakdowns

## Installation

<details>
<summary>Linux</summary>

1. **Download**
```sh
$ wget https://github.com/7ched7/trakd/releases/download/v0.5.0/trakd-v0.5.0-linux.tar.gz
```

2. **Extract**
```sh
$ tar -xzvf trakd-v0.5.0-linux.tar.gz
```

3. **Install**
```sh
$ cd trakd-v0.5.0-linux
$ ./install.sh
```

4. **Verify**
```sh
$ trakd -v
```

</details>

<details>
<summary>Windows</summary>

1. **Download**
<br> [Trakd Windows](https://github.com/7ched7/trakd/releases/download/v0.5.0/trakd-v0.5.0-win.zip)

2. **Extract**
<br> Right-click → **"Extract All..."**

3. **Install**
<br> Right-click → `install.bat` → **"Run as administrator"**

4. **Verify**
```cmd
$ trakd -v
```

</details>

## Commands

<details>
<summary>server</summary>

- **`$ trakd server install`**  
Install the socket server as a system service (Windows Service or systemd)

- **`$ trakd server remove`**  
Remove/uninstall the socket server service

- **`$ trakd server enable`**  
Enable the service to start automatically at boot

- **`$ trakd server disable`**  
Disable auto-start (you'll need to start the service manually)

- **`$ trakd server start`**  
Start the socket server (uses IP/port from config)

- **`$ trakd server start --daemonize`**  
Start the socket server in the background (detached daemon process)

- **`$ trakd server status`**  
Show server status and tracked processes

- **`$ trakd server stop`**  
Stop the running server/service 

</details>

<details>
<summary>ls</summary>

- **`$ trakd ls`**  
List all processes available for tracking

</details>

<details>
<summary>add</summary>

- **`$ trakd add <process_name>`**  
Track by process name

- **`$ trakd add <pid>`**  
Track by pid

- **`$ trakd add <process_name> -n <id>`**  
Add with custom tracking id

- **`$ trakd add <process_name> --fg`**  
Foreground mode

</details>

<details>
<summary>rm</summary>

- **`$ trakd rm <id>`**  
Stop tracking a specific process

</details>

<details>
<summary>ps</summary>

- **`$ trakd ps`**  
Show running tracked processes

- **`$ trakd ps -a`**  
Show all tracked processes (running + stopped)

- **`$ trakd ps -d`**  
Detailed view

> **Example output**
```sh
TRACK ID           PROCESS    PID    STARTED              RUNTIME     STATUS    CONNECTION
my_chrome_tracker  chrome     37133  2025/05/28 10:30:42  1h 25m 30s  running   127.0.0.1/59780
d6213668effb       mongod     37455  2025/05/28 11:22:18  0h 25m 28s  running   127.0.0.1/50936
41d9a30368f5       vim        --     2025/05/28 11:25:05  0h 22m 08s  stopped   127.0.0.1/50938
```

</details>

<details>
<summary>rename</summary>

- **`$ trakd rename <old_id> <new_id>`**  
Rename the tracking identifier

</details>

<details>
<summary>report</summary>

- **`$ trakd report`**  
Report program usage (default: daily)

- **`$ trakd report --start "5 months ago" --end "6 days ago"`**  
Report a specific date range with the --start and --end arguments

- **`$ trakd report --start "2025/05/21" --end "2025/05/27"`**  

> **Example output**
```sh
REPORT | 2025/05/21 00:00:00 - 2025/05/27 00:00:00

PROCESS       TOTAL RUN TIME    ACTIVE DAYS
chrome        36h 12m 30s       7
mongod        18h 45m 22s       5
vim           8h 30m 41s        4
```

</details>

<details>
<summary>user</summary>

- **`$ trakd user add <username>`**  
Create a new user with the specified username

- **`$ trakd user add <username> -s`**  
Create a new user and immediately switch to that user

- **`$ trakd user switch <username>`**  
Switch to an existing user

- **`$ trakd user rename <old_username> <new_username>`**  
Rename an existing user

- **`$ trakd user ls`**  
List all users currently in the system

- **`$ trakd user rm <username>`**  
Remove an existing user by specifying the username

</details>

<details>
<summary>config</summary>

- **`$ trakd config set -i <ip_address> -p <port> -l <limit>`**  
Set IP address, port, and maximum number of tracked processes

- **`$ trakd config show`**  
Show current user configuration

> **Example output**
```sh
HOST IP ADDRESS: 127.0.0.1
PORT: 8000
MAXIMUM PROCESS LIMIT: 8
```

</details>

<details>
<summary>reset</summary>

- **`$ trakd reset logs`**  
Clear tracking logs

- **`$ trakd reset config`**  
Reset current user configuration

- **`$ trakd reset all`**  
Full reset (logs + config)

- **`$ trakd reset all -y -v`**  
Full reset, skip prompts, verbose output

</details>

## Contributing
Pull requests, issues, and feature ideas are warmly welcome!

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.