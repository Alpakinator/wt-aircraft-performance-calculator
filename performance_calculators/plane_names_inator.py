import pandas as pd
import os
import json
from pathlib import Path
from blkx_parsers import blkx_parser


def fm_lister(central_dir, fm_dir, write_dir):
    '''
    Makes a .json file list of all piston plane fm files in fm/ folder
    :return:
    '''
    fmwritepath = os.path.join(write_dir, "fm_plane_names_piston.json")

    path_to_make = Path.cwd() / write_dir
    path_to_make.mkdir(exist_ok=True, parents=True)
    path_to_make = Path.cwd() / fm_dir
    path_to_make.mkdir(exist_ok=True, parents=True)

    with open(fmwritepath, 'w') as fm_plane_names_piston:
        list_fm_plane_names_piston = []
        for filename in os.listdir(fm_dir):
            fmfilepath = os.path.join(fm_dir, filename)
            if os.path.isfile(fmfilepath):
                fm_dict = blkx_parser(fmfilepath)
            if not fm_dict:
                continue
            Engine, Compressor, Main, Afterburner, RPM = shortcuter(fm_dict)
            if fm_dict and Main["Type"] == "Inline" or Main["Type"] == "Radial":
                list_fm_plane_names_piston.append(filename)
                # print(filename + " is a prop")
            else:
                continue #ignore jets and rockets because props are the focus of the project (for now)
        json.dump(list_fm_plane_names_piston, fm_plane_names_piston, indent=2)
    return

def central_fm_jsoner(central_dir, write_dir, image_dir):
    central_fm_dict ={}

    fmwritepath = os.path.join(write_dir, "fm_plane_names_piston.json")
    central_fmwritepath = os.path.join(write_dir, "central-fm_plane_names_piston.json")

    path_to_make = Path.cwd() / write_dir
    path_to_make.mkdir(exist_ok=True, parents=True)
    path_to_make = Path.cwd() / central_dir
    path_to_make.mkdir(exist_ok=True, parents=True)

    with open(central_fmwritepath, "w") as central_fm_json, open(fmwritepath, "r") as prop_fm_file:
        prop_fm_filelist = json.load(prop_fm_file)
        for central_file in os.listdir(central_dir):
            centralfilepath = os.path.join(central_dir, central_file)
            imagefilepath = os.path.join(image_dir, central_file[:-4]+"png")
            # checking if it is a file
            with open(image_dir) as vehicle_img_json:
                vehicle_img_list = json.load(vehicle_img_json)
                if vehicle_img_list:
                    if central_file[:-4]+"png" not in vehicle_img_list:
                        continue
            if not os.path.isfile(centralfilepath):
                print(central_file + " is not a central_file")
                continue
            # if not os.path.isfile(imagefilepath): # This excludes all hidden planes in War Thunder!!! 
            #     print(central_file + " has no picture so it's not in the game")
            #     continue
            central_dict = blkx_parser(centralfilepath)
            if "_killstreak" in central_file:
                continue
            if central_dict and "fmFile" in central_dict:
                if type(central_dict["fmFile"]) == str:
                    fm_file = central_dict["fmFile"][3:] + "x"
                elif type(central_dict["fmFile"]) == list:
                    fm_file = central_dict["fmFile"][0][3:] + "x"
                #   deleting quotes and adding "x" to "blk"
                print(central_file, fm_file)
            elif central_dict:
                fm_file = central_file
            else:
                print(central_file + "has no assigned flight model file and is skipped")
                continue
            if fm_file in prop_fm_filelist:
                central_fm_dict[central_file[:-5]] = fm_file
            # else: #that part works for jets and turboprops. Disabled for now, because props are the focus of this project (for now)
            #     central_fm_dict[central_file] = "fm_file"
        json.dump(central_fm_dict, central_fm_json, indent=2)


def ingame_central_names_lister(read_dir, write_dir):
    '''
    Makes a dictionary of ingame plane names and file plane names
    '''
    units_filepath = os.path.join(read_dir, "units.csv")

    central_fmwritepath = os.path.join(write_dir, "central-fm_plane_names_piston.json")
    central_ingamefilewritepath = os.path.join(write_dir, "central-ingame_plane_names_piston.json")

    path_to_make = Path.cwd() / write_dir
    path_to_make.mkdir(exist_ok=True, parents=True)
    path_to_make = Path.cwd() / read_dir
    path_to_make.mkdir(exist_ok=True, parents=True)

    dict_ingame_infiles = {}
    unit_names = pd.read_csv(units_filepath ,sep=";")
    dict_ingame_infiles = unit_names.set_index('<ID|readonly|noverify>')['<English>'].to_dict()
    with open (central_fmwritepath, "r") as central_fm_json:
        central_fm_filedict = json.load(central_fm_json)
        # Initialize the third dictionary
        central_ingame_dict = {}
        # Iterate through the first dictionary
        for central_name in central_fm_filedict:
            for infiles, ingame in dict_ingame_infiles.items():
                if central_name + '_0' == infiles:
                    if ingame == "":
                        central_ingame_dict[central_name] = central_name
                    else:
                        central_ingame_dict[central_name] = ingame.replace(u"\u00A0", " ").replace(u"-", "‑")
        for central_name in central_fm_filedict:
            if central_name not in central_ingame_dict:
                central_ingame_dict[central_name] = central_name
        # here it ends
    with open (central_ingamefilewritepath, "w") as central_ingame_json:
        json.dump(central_ingame_dict, central_ingame_json, indent=2)
    return

def dict_to_objectarray_converter(write_dir):
    central_ingamefilereadpath = os.path.join(write_dir, "central-ingame_plane_names_piston.json")
    central_ingamefilewritepath = os.path.join(write_dir, "central-ingame_plane_names_piston_arr.json")

    path_to_make = Path.cwd() / write_dir
    path_to_make.mkdir(exist_ok=True, parents=True)

    central_ingame_array = []
    with open(central_ingamefilereadpath, "r") as central_ingame_json:
        central_ingame_dict = json.load(central_ingame_json)
        for central, ingame in central_ingame_dict.items():
            central_ingame_array.append({"id": central, "name":ingame})
    with open (central_ingamefilewritepath, "w") as central_ingame_objectarray_json:
        json.dump(central_ingame_array, central_ingame_objectarray_json, indent=2)
    return

        
def vehicle_image_name_jsoner(source_file, destination_dir):
    images_folder = Path(source_file)
    all_image_names = [file.name for file in images_folder.iterdir() if file.is_file() and file.name.endswith('.png')]
    destination_file =  os.path.join(destination_dir, "vehicle_image_names.json")
    path_to_make = Path.cwd() / destination_dir
    path_to_make.mkdir(exist_ok=True, parents=True)
    with open(destination_file, 'w') as png_names_destination:
        json.dump(all_image_names, png_names_destination, indent=2)
        # for item in all_image_names:
            # file.write("%s\n" % item)

# for changing icons into antional abbreviations like [UK]
# rep = {u"\u00A0": " ",
#        u"\u25cb": "[Seal-Clubbing]",
#        u"\u2417":"[CN]",
#        u"\u2582": "[SU]",
#        u"\u2584": "[FR]",
#        u"\u2580": "[DE]",
#        u"": "[]",
#        u"": "[]",
#        u"": "[]",
#        u"": "[]",
#        u"": "[]",
#        u"": "[]",
#        u"": "[]",
#        u"": "[]",
#         u"": "[]",
#         u"": "[]",
#         u"": "[]",
#
#        }
# rep = dict((re.escape(k), v) for k, v in rep.iteritems())
# #Python 3 renamed dict.iteritems to dict.items so use rep.items() for latest versions
# pattern = re.compile("|".join(rep.keys()))
# text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)




def shortcuter(fm_dict):
    """
    Defining paths to dictionaries inside dictionaries to have a cleaner code
    """
    Engine = fm_dict
    Compressor = fm_dict
    Main = fm_dict
    Afterburner = fm_dict
    RPM = fm_dict
    if "Engine0" in fm_dict: # Some planes have no engine section apparently
        if "Compressor" in fm_dict["Engine0"]:
            Engine = fm_dict["Engine0"]
            Compressor = fm_dict["Engine0"]["Compressor"]
            Main = fm_dict["Engine0"]["Main"]
            Afterburner = fm_dict["Engine0"]["Afterburner"]["IsControllable"]
    if "EngineType0" in fm_dict:
        if "Compressor" in fm_dict["EngineType0"]:
            Engine = fm_dict["EngineType0"]
            Compressor = fm_dict["EngineType0"]["Compressor"]
            Main = fm_dict["EngineType0"]["Main"]
            Afterburner = fm_dict["EngineType0"]["Afterburner"]["IsControllable"]
        if "Propellor" in Engine:
            RPM = Engine["Propellor"]
        else:
            RPM = Main
    return Engine, Compressor, Main, Afterburner, RPM

def main():
    read_dir = "input_files/vehicle_name_files/"
    write_dir = "output_files/plane_name_files/"
    fm_dir = "input_files/fm_files/"
    central_dir = "input_files/central_files/"
    # fm_lister(central_dir,fm_dir, write_dir)
    # central_fm_jsoner(central_dir, write_dir, image_dir)
    ingame_central_names_lister(read_dir, write_dir)
    dict_to_objectarray_converter(write_dir)
    


if __name__ == "__main__":
    main()