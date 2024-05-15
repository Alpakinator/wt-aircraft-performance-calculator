import fsspec
import json
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

def main():
    print("Fetching starts")
    datamine_folder_fetcher("input_files/fm_files", "aces.vromfs.bin_u/gamedata/flightmodels/fm/")
    # datamine_folder_fetcher("input_files/central_files", "aces.vromfs.bin_u/gamedata/flightmodels/")
    # datamine_folder_fetcher("input_files/weapon_files", "aces.vromfs.bin_u/gamedata/weapons/")
    # datamine_file_fetcher("input_files/vehicle_name_files", "lang.vromfs.bin_u/lang/units.csv")
    # airplane_img_downloader('input_files/plane_images/', 'atlases.vromfs.bin_u/units/', 'plane_name_files/central-fm_plane_names_piston.json')
    print('Finished fetching datamine files!')
    
if __name__ == "__main__":
    main()  