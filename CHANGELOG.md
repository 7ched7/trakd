## Version 0.4.0 - 11/13/2025
### Added
- Windows support
- Run the socket server in the background as a service (Windows Service, systemd)
- Flexible date range options for report command  

## Version 0.3.1 - 10/29/2025
### Improvement
- Improve CLI error handling and messaging
### Refactor
- Refactor the project to utilize a class-based structure, removing utility functions for better maintainability
### Fixed
- Fix an error occurred when the process following the program suddenly stopped
- Fix a bug when renaming user to prevent conflicts

## Version 0.3.0 - 10/28/2025
### Added
- Multi-user feature: Users can be created, deleted, switched between and renamed
- Colored output support for enhanced readability
### Fixed
- Prevent the program from tracking itself

## Version 0.2.0 - 06/05/2025
### Added
- Ability to rename tracking IDs 
- Status command to check server status and the number of tracked processes
- Monthly report generation
- Periodic data saving to prevent data loss in case of sudden shutdowns
### Fixed
- Improved the error message for invalid IP address when connecting to the server

## Version 0.1.0 - 05/29/2025
### Features
- Server start, stop and force stop commands
- Process listing and tracking by PID, name or custom tracking ID
- Daily and weekly usage reporting
- Configuration management and reset options