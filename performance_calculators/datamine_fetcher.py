import fsspec
import json

from git import Repo
import os
import shutil
import stat
from pathlib import Path

def datamine_folder_fetcher(destination_folder, source_folder, tag):
    destination = Path.cwd() / destination_folder
    destination.mkdir(exist_ok=True, parents=True)
    if tag:
        fs = fsspec.filesystem("github", org="gszabi99", repo="War-Thunder-Datamine", ref=tag)
    else:
        fs = fsspec.filesystem("github", org="gszabi99", repo="War-Thunder-Datamine")
    fs.get(fs.ls(source_folder), destination.as_posix())

def datamine_file_fetcher(destination_file, source_file, tag):
    destination = Path.cwd() / destination_file
    destination.mkdir(exist_ok=True, parents=True)
    if tag:
        fs = fsspec.filesystem("github", org="gszabi99", repo="War-Thunder-Datamine", ref=tag)
    else:
        fs = fsspec.filesystem("github", org="gszabi99", repo="War-Thunder-Datamine")
    fs.get(source_file, destination.as_posix())

def airplane_img_downloader(destination_dir, source_dir, central_fm_dict_dir, tag):
    destination = Path.cwd() / destination_dir
    destination.mkdir(exist_ok=True, parents=True)
    with open (central_fm_dict_dir, "r") as central_fm_dict_json:
        central_fm_dict = json.load(central_fm_dict_json)
        for central_name, fm_name in central_fm_dict.items():
            source_file = source_dir + central_name + '.png'
            destination_file = destination_dir
            try:
                datamine_file_fetcher(destination_file, source_file, tag)
            except:
                
                continue
    return

def newest_repo_getter():
    """Downloads and processes latest War Thunder datamine files"""
    # Setup paths
    repo_url = "https://github.com/gszabi99/War-Thunder-Datamine.git"
    temp_dir = "input_files/temp_repo"
    datamines_dir = "input_files/datamines"
    plane_names_dir = "input_files/vehicle_names"
    plane_br_dir = "input_files/vehicle_br"
    plane_images_dir = "input_files/vehicle_images"

    # 1. Clone repo
    print("Cloning latest wt datamine repository...")
    repo = Repo.clone_from(repo_url, temp_dir, branch = "master")

    # 2. Remove existing latest folders
    print("Removing an old 'latest' folder...")
    for item in Path(datamines_dir).glob("*latest*"):
        if item.is_dir():
            shutil.rmtree(item)

    # 3. Get version and move aces folder
    print("Moving aces.vromfs folder...")
    version_file = Path(temp_dir) / "aces.vromfs.bin_u" / "version"
    with open(version_file, 'r') as f:
        version = f.read().strip()
    
    source_aces = Path(temp_dir) / "aces.vromfs.bin_u"
    dest_aces = Path(datamines_dir) / f"aces_{version}_latest"
    if source_aces.exists():
        shutil.copytree(source_aces, dest_aces)

    # 4. Move units.csv
    print("Moving units.csv...")
    source_units = Path(temp_dir) / "lang.vromfs.bin_u" / "lang" / "units.csv"
    dest_units = Path(plane_names_dir) / "units.csv"
    if source_units.exists():
        os.makedirs(plane_names_dir, exist_ok=True)
        shutil.copy2(source_units, dest_units)

    print("Moving wpcost.blkx...")
    source_br = Path(temp_dir) / "char.vromfs.bin_u" / "config" / "wpcost.blkx"
    dest_br = Path(plane_br_dir) / "wpcost.blkx"
    if source_br.exists():
        os.makedirs(plane_br_dir, exist_ok=True)
        shutil.copy2(source_br, dest_br)

    # 5. Clear and update plane images
    print("Updating plane images...")
    if os.path.exists(plane_images_dir):
        shutil.rmtree(plane_images_dir)
    os.makedirs(plane_images_dir)
    
    source_images = Path(temp_dir) / "atlases.vromfs.bin_u" / "units"
    if source_images.exists():
        for image in source_images.glob("*"):
            if image.is_file():
                shutil.copy2(image, Path(plane_images_dir) / image.name)

    # 6. Cleanup with error handling

    answer01 = input("Do you want to remove the temporary full datamine? \n(yes/no) ")
    if answer01 == 'yes':
        print("Cleaning up...")
        def on_rm_error(func, path, exc_info):
            # Make files writeable if needed
            os.chmod(path, stat.S_IWRITE)
            os.unlink(path)

        if os.path.exists(temp_dir):
            # Close any open Git objects
            if os.path.exists(os.path.join(temp_dir, '.git')):
                repo.close()
            # Remove with error handler
            shutil.rmtree(temp_dir, onexc=on_rm_error)

    print("Done!")

def main():
    datamines_dir = "input_files/datamines"
    print("Removing an old 'latest' folder...")
    for item in Path(datamines_dir).glob("*latest*"):
        if item.is_dir():
            shutil.rmtree(item)
    print("Fetching starts")
    # newest_repo_getter()
    print('Finished fetching datamine files!')
    
if __name__ == "__main__":
    main()  