import os
from ftputil import FTPHost
from ftplib import FTP

from utils import remove_parent_folder_from_path


def ftp_create_dir_recursively_if_not_exists(ftp: FTPHost, dir: str):
    if not ftp.path.exists(dir.replace('\\', '/')):
        head, tail = os.path.split(dir)
        if head != '':
            ftp_create_dir_recursively_if_not_exists(ftp, head)
        ftp.mkdir(dir.replace('\\', '/'))


def get_time_diff_local_machine_vs_ftp(ftp: FTPHost) -> float:
    """
    Returns "local machine time" - "ftp time" in seconds.
    """
    filename = '___temp_time_check_helper'
    extra_helper = 0
    filepath = f'{filename}_{extra_helper}'
    while os.path.exists(filepath) or ftp.path.exists(filepath):
        extra_helper += 1
        filepath = f'{filename}_{extra_helper}'
    with open(filepath, 'wb') as f:
        # This will create an empty file
        pass
    with open(filepath, 'rb') as source:
        with ftp.open(filepath, 'wb') as target:
            # similar to shutil.copyfileobj
            ftp.copyfileobj(source, target)
    modification_time_local_machine = os.path.getmtime(filepath)
    modification_time_ftp = ftp.path.getmtime(filepath)

    # Clean up
    os.remove(filepath)
    ftp.remove(filepath)
    return modification_time_local_machine - modification_time_ftp


def deploy_to_ftp(host: str, user: str, password: str, base_folder: os.PathLike):
    # Connect to host, default port
    with FTPHost(
        host,
        user,
        password
    ) as ftp:
        
        project_folder = os.path.join('sites', base_folder)
        
        time_diff = get_time_diff_local_machine_vs_ftp(ftp)

        for root, dirs, files in os.walk(project_folder):
            for name in files:
                filepath = os.path.join(root, name)
                filepath: str = remove_parent_folder_from_path(filepath)
                filepath = filepath.replace('\\', '/')

                # Check if local file is newer than ftp version
                needs_upload = True
                if ftp.path.exists(filepath):
                    local_mod_time = os.path.getmtime(filepath)
                    ftp_mod_time = ftp.path.getmtime(filepath) + time_diff
                    if ftp_mod_time >= local_mod_time:
                        needs_upload = False
                        print(f"Skipping upload of {filepath} because it hasn't changed since last upload.")
                if needs_upload:
                    print(f'Uploading {filepath}...')
                    # Create dir in ftp location if it doesn't exist
                    folder, filename = os.path.split(filepath)
                    ftp_create_dir_recursively_if_not_exists(ftp, folder)
                    with open(filepath, 'rb') as source:
                        with ftp.open(filepath, 'wb') as target:
                            # similar to shutil.copyfileobj
                            ftp.copyfileobj(source, target)
