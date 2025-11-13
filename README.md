# TRAKD  

![Version](https://img.shields.io/badge/version-0.4.0-blue)
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
$ wget https://github.com/7ched7/trakd/releases/download/v0.4.0/trakd-v0.4.0-linux.tar.gz
```

2. **Extract**
```sh
$ tar -xzvf trakd-v0.4.0-linux.tar.gz
```

3. **Install**
```sh
$ cd trakd-v0.4.0-linux
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
<br> [trakd-v0.4.0-win.zip](https://github.com/7ched7/trakd/releases/download/v0.4.0/trakd-v0.4.0-win.zip)

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
Install the socket service as a Windows Service

- **`$ trakd server remove`**  
Remove the Windows socket service

- **`$ trakd server enable`**  
Enable the socket service on Linux (systemd)

- **`$ trakd server disable`**  
Disable the socket service on Linux

- **`$ trakd server start`**  
Start the socket server (uses IP/port from config)

- **`$ trakd server start --daemonize`**  
Start the socket server as a background process

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
TRACK ID           PROCESS    PID    STARTED              STATUS    CONNECTION
-----------------  ---------  -----  -------------------  --------  ---------------
my_chrome_tracker  chrome     2705   2025/05/28 09:04:36  running   127.0.0.1/47602
45f6e7c16e87       mongod     2591   2025/05/28 10:22:40  running   127.0.0.1/47612
2515fc63e592       vim        --     2025/05/28 11:30:12  stopped   127.0.0.1/47618
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

Process       Total Run Time    Active Days
------------------------------------------
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