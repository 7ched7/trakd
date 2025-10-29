import os
import shutil
from typing import Callable, Generator, List, Optional, Tuple
from constants import DEFAULT_IP_ADDRESS, DEFAULT_PORT, DEFAULT_LIMIT
from filelock import FileLock
from contextlib import contextmanager
from type import ProfileType

class ProfileManager:
    '''
    Manages user profiles including reading, writing, creating, 
    deleting, updating, and switching between profiles. Handles the directory and file 
    operations needed for profile storage.
    '''

    @staticmethod
    def _trakd_path() -> str:
        '''
        Returns the path to the directory where profile-related files are stored.
        - Creates the directory if it does not exist
        '''

        dir_path = os.path.expanduser('~/.trakd')
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    @staticmethod
    def _profile_path() -> str:
        '''
        Returns the full path to the profile file.
        - The profile file contains user profile details
        '''

        dir_path = ProfileManager._trakd_path()
        return os.path.join(dir_path, 'profile')

    @staticmethod
    @contextmanager
    def _manage_lock(lock_file: str) -> Generator[None, None, None]:
        '''
        Context manager for handling file locks.
        - Ensures that only one process can access and modify profile data at a time
        '''
        
        lock = FileLock(lock_file)
        with lock:
            yield

    def _write_profiles(self, profiles: List[ProfileType]) -> None:
        '''
        Writes the list of profiles to the profile file.
        - Converts the profiles into a formatted string and writes it to the file
        '''

        profile_path = self._profile_path()
        data = '\n'.join(f'{p['username']}|{p['ip']}|{p['port']}|{p['limit']}|{p['selected']}' for p in profiles) + '\n'

        lock_file = os.path.join(self._trakd_path(), 'lck.lock')
        
        with self._manage_lock(lock_file):
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(data)

    def get_profiles(self) -> List[ProfileType]:
        '''
        Retrieves all profiles from the profile file.
        - Reads the profile data and returns it as a list of dictionaries
        '''

        profile_path = self._profile_path()
        profiles: List[ProfileType] = []
        lock_file = os.path.join(self._trakd_path(), 'lck.lock')

        with self._manage_lock(lock_file):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()

                        if not line:
                            continue

                        u, i, p, l, s = (x.strip() for x in line.split('|'))
                        
                        profiles.append({
                            'username': u,
                            'ip': i,
                            'port': int(p),
                            'limit': int(l),
                            'selected': int(s),
                        })
            except:
                pass
        return profiles

    def get_current_profile(self) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[int]]:
        '''
        Retrieves the current selected profile.
        - Finds and returns the profile that is marked as selected
        - Returns the username, IP, port, and limit for the selected profile
        '''

        for p in self.get_profiles():
            if p['selected']:
                limit = max(1, min(p['limit'], 24))
                return p['username'], p['ip'], p['port'], limit
        return None, None, None, None

    def _modify_profiles(
        self,
        modifier: Callable[[List[ProfileType]], bool],
        post_action: Optional[Callable[[], None]] = None
    ) -> bool:
        '''
        Modifies the list of profiles.
        - Calls the provided modifier function to apply changes to the profiles list
        - If successful, writes the modified profiles back to the profile file
        - Optionally calls a post-action function after modifying profiles
        '''
        
        profiles = self.get_profiles()
        if not modifier(profiles):
            return False

        self._write_profiles(profiles)
        if post_action:
            post_action()
        return True
    
    def create_profile(
        self,
        username: str,
        ip: str = DEFAULT_IP_ADDRESS,
        port: int = DEFAULT_PORT,
        limit: int = DEFAULT_LIMIT,
        selected: int = 0,
    ) -> bool:
        '''
        Creates a new user profile.
        - Adds a new profile with the given parameters (username, IP, port, limit, selected)
        - If the profile is successfully created, also creates the user's log directory
        '''

        def modifier(profiles):
            if any(p['username'].strip() == username.strip() for p in profiles):
                return False
            profiles.append({
                'username': username,
                'ip': ip,
                'port': port,
                'limit': limit,
                'selected': selected,
            })
            return True

        def post_action():
            logs_dir = os.path.expanduser(f'~/.trakd/logs/{username}')
            os.makedirs(logs_dir, exist_ok=True)

        return self._modify_profiles(modifier, post_action)
    
    def remove_profile(self, username: str) -> bool:
        '''
        Removes an existing profile.
        - Deletes the profile with the specified username from the profile file
        - Also removes the user's corresponding log directory
        '''

        def modifier(profiles):
            old_len = len(profiles)
            profiles[:] = [p for p in profiles if p['username'].strip() != username.strip()]
            return len(profiles) < old_len

        def post_action():
            logs_dir = os.path.expanduser(f'~/.trakd/logs/{username}')
            if os.path.isdir(logs_dir):
                shutil.rmtree(logs_dir)

        return self._modify_profiles(modifier, post_action)
    
    def switch_profile(self, username: str) -> bool:
        '''
        Switches the currently selected profile.
        - Marks the profile with the specified username as selected
        - Unmarks all other profiles
        '''

        def modifier(profiles):
            found = False
            for p in profiles:
                if p['username'].strip() == username.strip():
                    p['selected'] = 1
                    found = True
                else:
                    p['selected'] = 0
            return found
        
        return self._modify_profiles(modifier)

    def rename_profile(self, old_username: str, new_username: str) -> bool:
        '''
        Renames a profile.
        - Changes the username of the specified profile from old_username to new_username
        - Renames the user's log directory accordingly
        '''

        old_dir = os.path.expanduser(f'~/.trakd/logs/{old_username}')
        new_dir = os.path.expanduser(f'~/.trakd/logs/{new_username}')

        def modifier(profiles):
            for p in profiles:
                if p['username'].strip() == old_username.strip():
                    p['username'] = new_username
                    return True
            return False

        def post_action():
            if os.path.isdir(old_dir):
                os.makedirs(os.path.dirname(new_dir), exist_ok=True)
                os.rename(old_dir, new_dir)

        return self._modify_profiles(modifier, post_action)

    def update_profile(self, username: str, ip=DEFAULT_IP_ADDRESS, port=DEFAULT_PORT, limit=DEFAULT_LIMIT) -> bool:
        '''
        Updates the details of an existing profile.
        - Modifies the IP address, port, and limit for the specified profile
        '''

        def modifier(profiles):
            for p in profiles:
                if p['username'].strip() == username.strip():
                    p['ip'], p['port'], p['limit'] = ip, port, limit
                    return True
            return False

        return self._modify_profiles(modifier)