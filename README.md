# TRAKD  
**Trakd** is a lightweight and socket-based CLI (Command Line Interface) program tracking and time reporting tool for the Linux operating system. Ideal for anyone looking to better manage their time, understand how much time is spent on different programs, and monitor process activity directly from the terminal. With a clean and scriptable interface, it allows seamless integration into your daily workflow, giving you insights into your productivity, and enabling detailed time reporting.

**Why Trakd?**
* **Minimal and fast** - No GUI distractions
* **Linux-first** - Tailored for terminal lovers
* **Local-first** - Your data stays on your machine
* **Scriptable & Automation-ready** – Easily integrate into cron jobs or custom scripts
* **Insightful reports** - View daily or weekly usage breakdowns

## Installation

<details open>

<summary>Steps</summary>

1. **Download the release archive**
```sh
$ wget https://github.com/7ched7/trakd/releases/download/v0.3.0/trakd-v0.3.0.tar.gz
```

2. **Extract the archive**
```sh
$ tar -xzvf trakd-v0.3.0.tar.gz
```

3. **Install the application**
```sh
$ cd trakd-v0.3.0
$ ./install.sh
```

4. **Check the version**
```sh
$ trakd -v
```

</details>

## Commands

<details>
<summary>start</summary>

- **`$ trakd start`**  
Start the server using the IP address and port from user config

</details>

<details>
<summary>stop</summary>

- **`$ trakd stop`**  
Normal stop (fails if processes are tracked)

- **`$ trakd stop -f`**  
Force stop (terminates all tracking and shuts down)

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
<summary>status</summary>

- **`$ trakd status`**  

> **Example output**
```sh
SERVER: running
HOST: 127.0.0.1:10101
TRACKED PROCESSES: 2 (1 running, 1 stopped) 
```

</details>

<details>
<summary>rm</summary>

- **`$ trakd rm <id>`**  
Stop tracking a specific process

</details>

<details>
<summary>report</summary>

- **`$ trakd report`**  
Report program usage (default: daily)

- **`$ trakd report --daily`**  

- **`$ trakd report --weekly`**  

- **`$ trakd report --monthly`**  

> **Example output**
```sh
WEEKLY REPORT - 2025/05/21 - 2025/05/27

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

- **`trakd config set -i 127.0.0.1 -p 8000 -l 8`**  
Set IP address, port, and maximum number of tracked programs

- **`$ trakd config show`**  
Show user config

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
Reset user config

- **`$ trakd reset all`**  
Full reset

- **`$ trakd reset all -y -v`**  
Full reset, skip prompts, verbose output

</details>

## Contributing
Pull requests, issues, and feature ideas are warmly welcome!

## License
This project is licensed under the MIT License. See the [MIT](LICENSE) file for details.