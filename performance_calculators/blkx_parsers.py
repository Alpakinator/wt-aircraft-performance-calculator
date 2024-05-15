import json
import os

def blkx_parser(blkx_dir):
    with open(blkx_dir) as blkx_unpars:
        blkx_dict = json.load(blkx_unpars)
    return blkx_dict

def plane_file_accepter(files_to_plot, read_dir):
    planes_to_plot_dict = {}
    with open(read_dir, "r") as central_to_fm_json:
        central_to_fm_dict = json.load(central_to_fm_json)
        for file in files_to_plot:
            if file in central_to_fm_dict.keys():
                planes_to_plot_dict[file] = central_to_fm_dict[file]
            else:
                print(file + " FM Doesn't exist")
                continue
    return planes_to_plot_dict

def fm_parser(fm_dir, files_to_plot, read_dir):
    planes_to_plot_dict = plane_file_accepter(files_to_plot, read_dir)
    named_fm_dict = {}
    for central_name, fm_file in planes_to_plot_dict.items():
        fm_parsed = blkx_parser(os.path.join(fm_dir, fm_file))
        if fm_parsed:
            named_fm_dict[central_name] = fm_parsed
    return named_fm_dict

def central_parser(central_dir, files_to_plot, read_dir, file_extension):
    planes_to_plot_dict = plane_file_accepter(files_to_plot, read_dir)
    named_central_dict = {}
    for central_name in planes_to_plot_dict.keys():
        central_parsed = blkx_parser(central_dir + central_name + file_extension)
        if central_parsed:
            named_central_dict[central_name] = central_parsed
    return named_central_dict


def main():
    """To test if the parsers make a correct dictionaty out of .blkx file"""
    central_dir = "input_files/central_files/"

    fm_filepath = ("output_files/plane_name_files/central-fm_plane_names_piston.json")
    with open(fm_filepath, "r") as fm_json:
        # FM_dict = json.load(fm_json) #every sinhle aircraft cenral fm file parsed and printed
        FM_dict = ['re_2000_int']
        for file in FM_dict:
            print("this plane" ,file)
            fm_dir = (central_dir + file + '.blkx')
            # print(fm_dir)
            parsed = blkx_parser(fm_dir)
            print(parsed)



if __name__ == "__main__":
        main()
