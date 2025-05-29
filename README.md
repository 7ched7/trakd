# TRAKD
**Trakd** is a lightweight and socket-based CLI (Command Line Interface) program tracking and time reporting tool for the Linux operating system. Ideal for anyone looking to better manage their time, understand how much time is spent on different programs, and monitor process activity directly from the terminal. With a clean and scriptable interface, it allows seamless integration into your daily workflow, giving you insights into your productivity, and enabling detailed time reporting.

### Why Trakd?
* **Minimal and fast** - No GUI distractions
* **Linux-first** - Tailored for terminal lovers
* **Local-first** - Your data stays on your machine
* **Scriptable & Automation-ready** – Easily integrate into cron jobs or custom scripts
* **Insightful reports** - View daily or weekly usage breakdowns

## Installation
1. **Download the release archive**
```sh
$ wget https://github.com/cihatar/trakd/releases/download/v0.1.0/trakd-v0.1.0.tar.gz
```

2. **Extract the archive**
```sh
$ tar -xzvf trakd-v0.1.0.tar.gz
```

3. **Install the application**
```sh
$ cd trakd-v0.1.0
$ ./install.sh
```

4. **Check the version**
```sh
$ trakd -v
```

## Usage
### Start the server
```sh
$ trakd start
```

### List all system processes
```sh
$ trakd ls
```

### Start tracking a process
```sh
$ trakd add chrome                       # track by process name
$ trakd add 5173                         # track by pid
$ trakd add chrome -n my_chrome_tracker  # add with custom tracking id
```

### Show tracked processes
```sh
$ trakd ps     # show running tracked processes
$ trakd ps -a  # show all (running + stopped)
$ trakd ps -d  # detailed view
```
* Example output
```sh
TRACK ID           PROCESS    PID    STARTED              STATUS    CONNECTION
-----------------  ---------  -----  -------------------  --------  ---------------
my_chrome_tracker  chrome     2705   2025/05/28 09:04:36  running   127.0.0.1/47602
45f6e7c16e87       mongod     2591   2025/05/28 10:22:40  running   127.0.0.1/47612
2515fc63e592       vim        --     2025/05/28 11:30:12  stopped   127.0.0.1/47618
```

### Stop tracking a process
```sh
$ trakd rm my_chrome_tracker
```
> To stop tracking a process, you must use its `track ID` instead of the `process name` or `PID`.

### View usage reports 
```sh
$ trakd report           # default: daily
$ trakd report --daily   # explicit daily report
$ trakd report --weekly  # weekly report
```

* Example output
```sh
WEEKLY REPORT - 2025/05/21 - 2025/05/27

Process       Total Run Time    Active Days
------------------------------------------
chrome        36h 12m 30s       7
mongod        18h 45m 22s       5
vim           8h 30m 41s        4
```

### Stop the server
```sh
$ trakd stop
```
> If you have programs that are still being tracked, the `stop` command will return an error. Instead, you can use the `--force` flag to stop tracking all processes and stop the server.
```sh
$ trakd stop -f 
```

### Manage configuration
```sh
$ trakd config set -i 127.0.0.1 -p 8000 -l 8  # set config
$ trakd config show                           # view current config
```

* Example output
```sh
HOST IP ADDRESS: 127.0.0.1
PORT: 8000
MAXIMUM PROCESS LIMIT: 8
```

### Reset application
```sh
$ trakd reset logs       # clear logs
$ trakd reset config     # reset configuration
$ trakd reset all        # full reset
$ trakd reset all -y -v  # skip prompts, verbose output
```

## Contributing
Pull requests, issues, and feature ideas are warmly welcome!

## License
[MIT](LICENSE) ©