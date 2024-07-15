import math as ma
import json
from pathlib import Path
from ram_pressure_density_calculator import air_pressurer, altitude_at_pressure, rameffect_er, air_densitier
from inspect import currentframe, getframeinfo

"""
The most important file of the entire WTAPC.org project.
File with all the functions needed to calculate engine power curves of all piston engine aircraft, and save them to .json. 
All of it was made step by step, by comparing generated power curves to the logged (with WTRTI) power curves while climbing in-game.
Therefore the file is not perfect, but still within +-1% accuracy for more than 95% of the aircraft.
"""
########################################################################################################################

def optimal_dict_initializer(final_engine_modes, compr_stages_count):
    """
    Creates an empty dictionary for every supercharger stage/speed and power mode in a 'power_curves' dictionary. Calculated power will be put into it
    """
    power_curves = {}
    for engine_mode in final_engine_modes:
        power_curves[engine_mode] = {}
        for stage in range(0, compr_stages_count):
            power_curves[engine_mode][stage] = []
    return power_curves

def enginecounter(named_fm_dict):
    """
    Counts engines, needed to calculate power/weight
    """
    plane_engine_count = {}
    for plane_name, fm_dict in named_fm_dict.items():
        engine_count = 0
        number = 0
        for key in fm_dict:
            if "Engine" in key:
                if type(fm_dict[key]) == dict and "Type" in fm_dict[key]:
                    if fm_dict[key]["Type"] == 0:
                        for char in key:
                            if char.isdigit():
                                number = int(char)
                        if number > engine_count:
                            engine_count = number
                else:
                    for char in key:
                        if char.isdigit():
                            number = int(char)
                    if number > engine_count:
                        engine_count = number
        plane_engine_count[plane_name] = engine_count + 1 # +1 because engines are counted from 0 in fm files
    return plane_engine_count

def torquer(Main, lower_RPM, higher_RPM):
    """
    Calculates the effect of RPM change on engine power
    Torque curve is an upside down parabola that has a maximum at 75% of WEP RPM
    Here Main["WEP_RPM"] or Main["military_RPM"] are equivalent to 'x' and 'Torque_max_RPM' to 'b' in:
    = -(x^2) + 2bx curve of torque. then to get engine power you multiply by RPM. 
    """
    Torque_max_RPM = 0.75 * higher_RPM
    WEP_military_RPM_boost = ((higher_RPM * ((2 * Torque_max_RPM * higher_RPM) - (higher_RPM ** 2))) / (
            lower_RPM * ((2 * Torque_max_RPM * lower_RPM) - (lower_RPM ** 2))))
    return WEP_military_RPM_boost
########################################################################################################################

def torque_from_hp(power, reduct_RPM):
    """
    Getting propeller hub torque in kgf based on engine power in hp.
    Not confirmed if that's how it works in WT, but that's how it works IRL.
    https://binsfeld.com/power-torque-speed-conversion-calculator/
    https://www.mountztorque.com/torque-conversion-calculator
    1 ft-lbs = 0.1382549544 kgf
    Power (Hp) = Torque (ft-lbs) * RPM / 5252
    Power (Hp) = Torque (kgf) * RPM / 726.115
    Torque (kgf) = 726.115 * Power (Hp) / RPM 
    alternatively Torque (kgf) = (power * 75) / ((reduct_RPM * 2 * 3.14159265359)/60)
    """
    torque = (power * 726.115) / (reduct_RPM)
    return torque

########################################################################################################################
def engine_shortcuter(fm_dict):
    """
    Defining paths to dictionaries inside dictionaries to have cleaner code
    """
    Engine = fm_dict
    Compressor = fm_dict
    Main = fm_dict
    Afterburner = fm_dict
    if "Engine0" in fm_dict:  # Some planes have no engine section apparently
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
        Propeller = Engine["Propellor"]
    # elif "PropellerType0" in fm_dict:
    #     Propeller = fm_dict["PropellerType0"]["Governor"]
    else:
        Propeller = Main
    return Engine, Compressor, Main, Afterburner, Propeller
########################################################################################################################

def exception_fixer(central_file, Compressor, Main):
    """
    Fixes minor quirks of flightmodel files
    """
    if "PowerConstRPMCurvature0"  in Compressor and type(Compressor["PowerConstRPMCurvature0"]) == list:
        Compressor["PowerConstRPMCurvature1"] = float(Compressor["PowerConstRPMCurvature0"][1])
        Compressor["PowerConstRPMCurvature0"] = float(Compressor["PowerConstRPMCurvature0"][0])
    return

def old_type_fm_detector(Compressor, Main):
    """
    Modifies very old flightmodel files (example lagg-3-1) to be compatible with the rest of the code
    """
    if "CompressorOmegaFactorSq" not in Compressor:
        Compressor["ExactAltitudes"] = True
        Compressor["CompressorOmegaFactorSq"] = 1.0
    if "Multiplier0" in Compressor:
        military_mp = 1
        Main["Power"] = Main ["HorsePowers"]
        for e in range (0, 10):
            if "ATA" +str(e) in Compressor:
                military_mp = Compressor["ATA" +str(e)]
        Compressor["AfterburnerManifoldPressure"] = Compressor["AfterburnerCompressionFactor"] * military_mp
        for f in range (0,6):
            if "Altitude" + str(f) in Compressor:
                Compressor["Power" + str(f)] = Main["Power"] * Compressor["Multiplier" + str(f)]
            else:
                return
    else:
        return
########################################################################################################################
    
def rpm_er(fm_dict, Main, Propeller):
    """
    Extracts RPM values from flightmodel files for military and WEP mode
    """
    Main["WEP_RPM"] = 666
    Main["military_RPM"] = 666
    for key, value in Propeller.items():
        if key[:-1] != "ThrottleRPMAuto":
            continue
        if type(value[0]) is list:
            for value1 in value:
                if float(value1[0]) == 1.0:
                    Main["military_RPM"] = float(value1[1])
                    Main["WEP_RPM"] = float(value1[1])
                elif float(value1[0]) == 1.1:
                    Main["WEP_RPM"] = float(value1[1])
        elif float(value[0]) == 1.0:
            Main["military_RPM"] = float(value[1])
            Main["WEP_RPM"] = float(value[1])
        elif float(value[0]) == 1.1:
            Main["WEP_RPM"] = float(value[1])
    
    #FOR REFINEMENT. B7A2 hOMARE 2900 RPM
    # if "PropellerType0" in fm_dict:
    #     Main["WEP_RPM"] = fm_dict["PropellerType0"]["Governor"]["GovernorAfterburnerParam"]
    #     if Main["military_RPM"] >= Main["WEP_RPM"]:
    #         Main["military_RPM"] == Main["WEP_RPM"]
    return

def wep_mp_er(Engine, Compressor, Main, Afterburner):
    """
    Calculates MP ratio and RPM ratio between WEP and military power, for accurate WEP prediction.
    """
    mode_manifolds = {}
    non_wep_manifolds = {}
    Main["Octane_MP"] = 1
    Main["WEP_MP"] = 1
    Main["Military_MP"] = 1

    for key_T, value_T in Engine["Temperature"].items():
        if key_T[:-1] == "Mode":
            mode_manifolds[key_T] = value_T["ManifoldPressure"]
            mode_manifolds = dict(sorted(mode_manifolds.items(), key=lambda item: item[1]))

    for key_A, value_A in Compressor.items():
        if key_A[:-1] == "ATA":
            non_wep_manifolds[key_A] = value_A
            non_wep_manifolds = dict(sorted(non_wep_manifolds.items(), key=lambda item: item[1]))

    if Afterburner:
        Main["Military_MP"] = list(non_wep_manifolds.values())[-1]
        if list(mode_manifolds.values())[-1] - Compressor["AfterburnerManifoldPressure"] > 0.02:
            Main["WEP_MP"] = Compressor["AfterburnerManifoldPressure"]
        else:
            Main["WEP_MP"] = Compressor["AfterburnerManifoldPressure"]
    elif not Afterburner:
        if ma.isclose(list(mode_manifolds.values())[-1], Compressor["AfterburnerManifoldPressure"], abs_tol=0.011):
            Main["Military_MP"] = list(non_wep_manifolds.values())[-1]
            Main["Military_MP"] = list(non_wep_manifolds.values())[-1]
        elif list(mode_manifolds.values())[-1] - Compressor["AfterburnerManifoldPressure"] < -0.02:
            Main["Military_MP"] = list(non_wep_manifolds.values())[-1]
    return

def wep_rpm_ratioer(Main, Compressor, Propeller):
    """
    Equation governing how much RPM increase on WEP, strengthens supercharger effectiveness.
    Uses surprisingly many parameters from FM file in complex ways.

    Main["WEP-mil_RPM_EffectOnSupercharger"] (float): usually between 1<->1.3 Coefficient of supercharger strength when switching form military to WEP.
    """ 
    if ("ShaftRPMMax" in Main and Main["ShaftRPMMax"] - Main["military_RPM"] > 5 and Main["ShaftRPMMax"] - Main["WEP_RPM"] < 5):
        Main["default_RPM"] = Main["ShaftRPMMax"]
    elif ("RPMNom" in Main and Main["RPMNom"] - Main["military_RPM"] > 5):
        Main["default_RPM"] = Main["RPMNom"]  # For when Shaft RPM = WEP RPM. Becasue "CompressorPressureAtRPM0" is defined for WEP RPM, not military RPM
    elif ("GovernorMaxParam" in Propeller and ((Propeller["GovernorMaxParam"] - Main["military_RPM"]) > 5)):
        Main["default_RPM"] = Propeller["GovernorMaxParam"]
    else:
        Main["default_RPM"] = Main["military_RPM"]
    # Main["default_RPM"] = 2600
    Main["default-mil_RPM_EffectOnSupercharger"] = (1 + ((1 - Compressor["CompressorPressureAtRPM0"]) / Main["military_RPM"]) * (Main["default_RPM"] - Main["military_RPM"])) \
                        ** (1 + Compressor["CompressorOmegaFactorSq"])
    Main["WEP-mil_RPM_EffectOnSupercharger"] = (1 + ((1 - Compressor["CompressorPressureAtRPM0"]) / Main["military_RPM"]) * (Main["WEP_RPM"] - Main["military_RPM"])) \
                        ** (1 + Compressor["CompressorOmegaFactorSq"])
    # else:  # When military RPM is actually the default one
    #     Main["WEP-mil_RPM_EffectOnSupercharger"] = (1 + ((1 - Compressor["CompressorPressureAtRPM0"]) / Main["military_RPM"]) * (Main["WEP_RPM"] - Main["military_RPM"])) \ ** (1 + Compressor["CompressorOmegaFactorSq"])
    return

def definition_alt_power_adjuster(Main, Compressor, Propeller, i):
    """
    If engine power and crit alts in FM file are defined for engine running at WEP RPM, not mil RPM, this function adjusts them to mil RPM.
    """
    Compressor["Old_Power" + str(i)] = Compressor["Power" + str(i)]
    Compressor["Old_Power_new_RPM" + str(i)] = Compressor["Old_Power" + str(i)]
    Compressor["Old_Altitude" + str(i)] = Compressor["Altitude" + str(i)]
    if Ceiling_is(Compressor, i):
        Compressor["Old_Ceiling" + str(i)] = Compressor["Ceiling" + str(i)]
    if ConstRPM_is(Compressor, i):
        Compressor["Old_PowerConstRPM" + str(i)] = Compressor["PowerConstRPM" + str(i)]
    if (("ShaftRPMMax" in Main and Main["ShaftRPMMax"] - Main["military_RPM"] > 5 and Main["ShaftRPMMax"] - Main["WEP_RPM"] < 5) or
            ("RPMNom" in Main and Main["RPMNom"] - Main["military_RPM"] > 5) or ("GovernorMaxParam" in Propeller and ((Propeller["GovernorMaxParam"] - Main["military_RPM"]) > 5) )):  # If fm power and crit alt is for WEP RPM
        if ConstRPM_is(Compressor, i):
            Compressor["Old_PowerConstRPM" + str(i)] = Compressor["PowerConstRPM" + str(i)]
            Compressor["PowerConstRPM" + str(i)] = Compressor["PowerConstRPM" + str(i)] / (
                torquer(Main, Main["military_RPM"], Main["default_RPM"]))
        # Useful for marking the wep_crit_alt <-> mil_crit alt area
        Compressor["Old_Power" + str(i)] = Compressor["Power" + str(i)]
        Compressor["Old_Power_new_RPM" + str(i)] = Compressor["Old_Power" + str(i)]/torquer(Main, Main["military_RPM"], Main["default_RPM"])
        Compressor["Old_Altitude" + str(i)] = Compressor["Altitude" + str(i)]

        fake_mil_crit_supercharger_strength = Main["Military_MP"] / air_pressurer(Compressor["Altitude" + str(i)])
        Main["crit_supercharger_strength" + str(i)] = fake_mil_crit_supercharger_strength / Main["default-mil_RPM_EffectOnSupercharger"]
        Compressor["Altitude" + str(i)] = round(altitude_at_pressure(Main["Military_MP"] / Main["crit_supercharger_strength" + str(i)]))

        fake_mil_deck_supercharger_strength = Main["Military_MP"] / air_pressurer(0)
        Main["deck_supercharger_strength" + str(i)] = fake_mil_deck_supercharger_strength / Main["default-mil_RPM_EffectOnSupercharger"]
        Main["Deck_Altitude" + str(i)] = altitude_at_pressure(Main["Military_MP"] /Main["deck_supercharger_strength" + str(i)])

        Compressor["Power" + str(i)] = ((equationer(Compressor["Power" + str(i)], Compressor["Old_Altitude" + str(i)],
                                        Compressor["Power" + str(i)] * ((Main["Power"]/Compressor["Old_Power" + str(0)] )),Compressor["Old_Altitude" + str(i)]-Compressor["Old_Altitude" + str(0)], Compressor["Altitude" + str(i)], 1))
                                        / (torquer(Main, Main["military_RPM"], Main["default_RPM"])))
        if Ceiling_is(Compressor, i):
            Compressor["Old_Ceiling" + str(i)] = Compressor["Ceiling" + str(i)]
            Compressor["Old_PowerAtCeiling" + str(i)] = Compressor["PowerAtCeiling" + str(i)]
            fake_mil_ceil_supercharger_strength = Main["Military_MP"] / air_pressurer(Compressor["Ceiling" + str(i)])
            ceil_supercharger_strength = fake_mil_ceil_supercharger_strength / Main["default-mil_RPM_EffectOnSupercharger"]
            Compressor["Ceiling" + str(i)] = round(altitude_at_pressure(Main["Military_MP"] / ceil_supercharger_strength))

        if ConstRPM_is(Compressor, i) and Compressor["Old_PowerConstRPM" + str(i)] == Compressor["Old_Power" + str(i)]:
            #For Hornet Mk3. After adjusting military power and crit alts to lower RPM, "AltitudeConstRPM" is no longer
            # below "Altitude", so it stops affecting how Main[Power] is calculated in typical way. However, Power and
            # ConstRPM power are adjusted differently, so this correction here, adjusts them identically,
            # so that later logic changing Main[Power] works as if "constRPM" was above crit alt and had the same
            # power as "Power"
            Compressor["PowerConstRPM" + str(i)] = Compressor["Power" + str(i)]
        deck_power_maker(Main, Compressor, i) #Important. Redefines Main["Power" + str(i)] in case things abpve changed how Main["Power" + str(i)] should be defined.        
        Main["Power" + str(i)] = equationer(Compressor["Old_Power" + str(i)], Compressor["Old_Altitude" + str(i)],
                                            Main["Power" + str(i)], 0, Main["Deck_Altitude" + str(i)], 1) / (
                                     torquer(Main, Main["military_RPM"], Main["default_RPM"]))    
    return

def deck_power_maker(Main, Compressor, i):
    """
    Creates engine power values for supercharger speeds/stages above first, just like Main["Power"] by default defined for first. 
    As a result it determines the rate at which power drops(throttling losses) or increases (some variable speed superchargers) below critical altitude.
    Very complicated and not perfect. The biggest flaw of these engine power calculations. Why Gaijin, why?
    """
    if not "Power" + str(0) in Main:
        Main["Power" + str(0)] = Main["Power"]
    if not "Deck_Altitude" + str(i) in Main:
        Main["Deck_Altitude" + str(i)] = 0
    if "Power" + str(i) in Main: # to not overwrite hard coded Main[Power] from exception fixer
        return
    else:
        Main["Power" + str(i)] = 0.8 * Main["Power" + str(i-1)]
    if Main["Power" + str(i)] < (0.8 * Compressor["Power" + str(i)]):
        Main["Power" + str(i)] = 0.8 * Compressor["Power" + str(i)]               
    return


def soviet_octane_adder(central_dict, Compressor, Main, i, octane):
    """
    Adds effect of soviet higher octane engine upgrade
    """
    if not "modifications" in central_dict:
        return
    if (octane and "ussr_fuel_b-95" in central_dict["modifications"] and
        central_dict["modifications"]["ussr_fuel_b-95"]["effects"]["addHorsePowers"] == 50) or \
        (octane and "ussr_fuel_b-100" in central_dict["modifications"] and
        central_dict["modifications"]["ussr_fuel_b-100"]["effects"]["addHorsePowers"] == 50):
        universal_octane_modifier = 1.018
        if i == 0:
            Main["Power"] = Main["Power"] * universal_octane_modifier
        if ConstRPM_is(Compressor, i):
            Compressor["PowerConstRPM" + str(i)] = Compressor["PowerConstRPM" + str(i)] * universal_octane_modifier
        Compressor["Power" + str(i)] = Compressor["Power" + str(i)] * universal_octane_modifier
        if Ceiling_is_useful(Compressor, i):
            Compressor["PowerAtCeiling" + str(i)] = Compressor["PowerAtCeiling" + str(i)] * universal_octane_modifier
    return


def brrritish_octane_adder(central_dict, Main, octane):
    """
    Adds effect of British higher octane engine upgrade
    """
    Main["OctaneAfterburnerMult"] = 1
    if not "modifications" in central_dict:
        return
    if "150_octan_fuel" in central_dict["modifications"] and \
            central_dict["modifications"]["150_octan_fuel"]["invertEnableLogic"] == False:
        Octane_modifier = central_dict["modifications"]["150_octan_fuel"]["effects"]["afterburnerMult"]
        if octane == True:
            Main["OctaneAfterburnerMult"] = Octane_modifier
            Main["Octane_MP"] = Main["Military_MP"] + ((Main["WEP_MP"] - Main["Military_MP"])
                            * central_dict["modifications"]["150_octan_fuel"]["effects"]["afterburnerCompressorMult"])
    elif "150_octan_fuel" in central_dict["modifications"] and \
                central_dict["modifications"]["150_octan_fuel"]["invertEnableLogic"] == True:
        temp_mp = Main["WEP_MP"]
        Main["WEP_MP"] = Main["Military_MP"] + ((Main["WEP_MP"] - Main["Military_MP"])
                            * central_dict["modifications"]["150_octan_fuel"]["effects"]["afterburnerCompressorMult"])
        Main["Octane_MP"] = temp_mp
        De_Octane_modifier = central_dict["modifications"]["150_octan_fuel"]["effects"]["afterburnerMult"]
        if octane == False:
            Main["OctaneAfterburnerMult"] = De_Octane_modifier
    elif "100_octan_spitfire" in central_dict["modifications"] and \
        central_dict["modifications"]["100_octan_spitfire"]["invertEnableLogic"] == True:
        De_Octane_modifier = central_dict["modifications"]["100_octan_spitfire"]["effects"]["afterburnerMult"]
        temp_mp = Main["WEP_MP"]
        Main["WEP_MP"] = Main["Military_MP"] + ((Main["WEP_MP"] - Main["Military_MP"]) *
                                central_dict["modifications"]["100_octan_spitfire"]["effects"]["afterburnerCompressorMult"])
        Main["Octane_MP"] = temp_mp
        if octane == False:
            Main["OctaneAfterburnerMult"] = De_Octane_modifier
    return



def wep_mulitiplierer(octane, Main, Compressor, i, mode):
    """
    Calcualtes critical altitues in WEP mode
    """
    if not 'AfterburnerPressureBoost' + str(i) in Compressor:
        Compressor['AfterburnerPressureBoost' + str(i)] = 1
    Compressor["Old_Altitude_WEPboost" + str(i)] = round(altitude_at_pressure(air_pressurer(Compressor["Old_Altitude"+ str(i)])/Compressor['AfterburnerPressureBoost' + str(i)]))


    Main["deck_supercharger_strength" + str(i)] = Main["Military_MP"] / air_pressurer(Main["Deck_Altitude" + str(i)])
    Main["WEP_deck_supercharger_strength"] = Main["deck_supercharger_strength" + str(i)] * Main["WEP-mil_RPM_EffectOnSupercharger"] * Compressor['AfterburnerPressureBoost' + str(i)]
    Main["crit_supercharger_strength" + str(i)] = Main["Military_MP"] / air_pressurer(Compressor["Altitude" + str(i)])
    Main["WEP_crit_supercharger_strength"] = Main["crit_supercharger_strength" + str(i)] * Main["WEP-mil_RPM_EffectOnSupercharger"] * Compressor['AfterburnerPressureBoost' + str(i)]
    ########################################################################################################################
    if all(k in Compressor for k in ("Ceiling" + str(i), "PowerAtCeiling" + str(i))):
        # ceil_supercharger_strength = Main["Military_MP"] / air_pressurer(Compressor["Ceiling" + str(i)])
        # WEP_ceil_supercharger_strength = ceil_supercharger_strength * Main["WEP-mil_RPM_EffectOnSupercharger"]
        # Main["WEP_ceil_altitude"] = altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) /
        # WEP_ceil_supercharger_strength)
        Main["WEP_ceil_altitude"] = Compressor["Ceiling" + str(i)]
    else:
        Main["WEP_ceil_altitude"] = 0
    if Main["Octane_MP"] == 1:
        octane = False

    if octane:
        Main["WEP_deck_altitude"] = round(altitude_at_pressure(Main["Octane_MP"] / Main["WEP_deck_supercharger_strength"]))
        Main["WEP_crit_altitude"] = round(altitude_at_pressure(Main["Octane_MP"] / Main["WEP_crit_supercharger_strength"]))
    else:
        Main["WEP_deck_altitude"] = round(altitude_at_pressure(Main["WEP_MP"] / Main["WEP_deck_supercharger_strength"]))
        Main["WEP_crit_altitude"] = round(altitude_at_pressure(Main["WEP_MP"] / Main["WEP_crit_supercharger_strength"]))

    if mode == "WEP" and Compressor["ExactAltitudes"] == False and ConstRPM_is(Compressor, i): # F2G-1
        Main["constRPM_supercharger_strength"] = Main["Military_MP"] / air_pressurer(
            Compressor["AltitudeConstRPM" + str(i)])
        Main["WEP_constRPM_supercharger_strength"] = Main["constRPM_supercharger_strength"] * Main["WEP-mil_RPM_EffectOnSupercharger"] * Compressor['AfterburnerPressureBoost' + str(i)]
        if octane:
            Main["WEP_powerconstRPM"] = altitude_at_pressure(
                Main["Octane_MP"] / Main["WEP_constRPM_supercharger_strength"])
        else:
            Main["WEP_powerconstRPM"] = altitude_at_pressure(
                Main["WEP_MP"] / Main["WEP_constRPM_supercharger_strength"])

    if mode == "WEP":
        if not ("AfterburnerBoostMul" + str(i)) in Compressor:
            Compressor["AfterburnerBoostMul" + str(i)] = 1
        Main["WEP_power_mult"] = ((1 + ((Main["AfterburnerBoost"] - 1) * Main["OctaneAfterburnerMult"])) *
                              Main["ThrottleBoost"] * Compressor["AfterburnerBoostMul" + str(i)]) * (torquer(Main, Main["military_RPM"], Main["WEP_RPM"]))
                            # Adding effect of 150 oct fuel upgrade
        # else:
        #     Main["WEP_power_mult"] = (Main["AfterburnerBoost"] * Main["ThrottleBoost"] * boost_mul) * (
        #         torquer(Main))
        if Compressor["AfterburnerBoostMul" + str(i)] == 0:
            Main["WEP_deck_altitude"] = 0
            Main["WEP_crit_altitude"] = Compressor["Altitude" + str(i)]
            Main["WEP_power_mult"] = 1
    else:
        Main["WEP_power_mult"] = 1
    return Main["WEP_power_mult"]


########################################################################################################################

def ConstRPM_is(Compressor, i):
    if all(k in Compressor for k in ("AltitudeConstRPM" + str(i), "PowerConstRPM" + str(i))):
        return True
    else:
        return False

def ConstRPM_bends_above_crit_alt(Compressor, i):
    if ConstRPM_is(Compressor, i) and Compressor["AltitudeConstRPM" + str(i)] == Compressor["Altitude" + str(i)] and \
            Compressor["Power" + str(i)] - Compressor["PowerAtCeiling" + str(i)] > 1 and \
            Compressor["PowerConstRPMCurvature0"] > 1:
        return True
    else:
        return False

def ConstRPM_is_high_bends_below_critalt(Compressor, i):
    if (ConstRPM_is(Compressor, i)
            and Compressor["AltitudeConstRPM" + str(i)] > Compressor["Altitude" + str(i)]
            and Compressor["AltitudeConstRPM" + str(i)] > Compressor["Ceiling" + str(i)]
            and Compressor["PowerConstRPM" + str(i)] > Compressor["Power" + str(i)]):
        return True
    else:
        return False
def ConstRPM_is_high_but_useless(Compressor, i):
    if (ConstRPM_is(Compressor, i)
            and Compressor["AltitudeConstRPM" + str(i)] > Compressor["Old_Altitude" + str(i)]
            and Compressor["AltitudeConstRPM" + str(i)] > Compressor["Old_Ceiling" + str(i)]
            and Compressor["Old_PowerConstRPM" + str(i)] == Compressor["Old_Power" + str(i)]):
        return True
    else:
        return False


def ConstRPM_is_high_equal_to_power(Compressor, i):
    if (ConstRPM_is(Compressor, i) and i != 0
            and Compressor["AltitudeConstRPM" + str(i)] == Compressor["Altitude"+ str(i)]
            and Compressor["PowerConstRPM" + str(i)] == Compressor["Power" + str(i)]):
        return True
    else:
        return False


def ConstRPM_bends_below_critalt(Compressor, i):
    if ConstRPM_is(Compressor, i) and -1 > Compressor["AltitudeConstRPM" + str(i)] - Compressor[
        "Altitude" + str(i)]:
        return True
    else:
        return False
    
def ConstRPM_bends_below_old_critalt(Compressor, i):
    if ConstRPM_is(Compressor, i) and -1 > Compressor["AltitudeConstRPM" + str(i)] - Compressor[
        "Old_Altitude" + str(i)]:
        return True
    else:
        return False
    
def ConstRPM_bends_below_WEP_critalt(Main, Compressor, i):
    if ConstRPM_is(Compressor, i) and -1 > Compressor["AltitudeConstRPM" + str(i)] - Main[
        "WEP_crit_altitude"]:
        return True
    else:
        return False

def ConstRPM_bends_below_critalt_0(Compressor):
    if ConstRPM_is(Compressor, 0) and -1 > Compressor["AltitudeConstRPM" + str(0)] - Compressor[
        "Altitude" + str(0)]:  # For A7M2 - cases when constrpm equals altitude
        return True
    else:
        return False
    
def ConstRPM_bends_below_old_critalt_0(Compressor):
    if ConstRPM_is(Compressor, 0) and -1 > Compressor["AltitudeConstRPM" + str(0)] - Compressor[
        "Old_Altitude" + str(0)]:  # For A7M2 - cases when constrpm equals altitude
        return True
    else:
        return False
        
def ConstRPM_is_power(Compressor, i):
    if (ConstRPM_is(Compressor, i) and Compressor["AltitudeConstRPM" + str(i)] == Compressor["Altitude" + str(i)]
            and Compressor["PowerConstRPM" + str(i)] == Compressor["Power" + str(i)]):
        return True
    else:
        return False

def ConstRPM_is_below_deck(Compressor, i):
    if ConstRPM_is(Compressor, i) and Compressor["AltitudeConstRPM" + str(i)] <= 0:
        return True
    else:
        return False

# def ConstRPM_is_deck_power(Main, Compressor, i):
#     # For cases like Do-217 when constrpm is deck power
#     if ConstRPM_is(Compressor, i) and Compressor["AltitudeConstRPM" + str(i)] == Main["Deck_Altitude" + str(i)]:
#         return True
#     else:
#         return False

def Power_is_deck_power(Main, Compressor, i):
    if Compressor["Altitude" + str(i)] == Main["Deck_Altitude" + str(i)]:
        #For cases like Do-217 when constrpm is good main power
        return True
    else:
        return False
    
def Ceiling_is(Compressor, i):
    if all(k not in Compressor for k in ("Ceiling" + str(i), "PowerAtCeiling" + str(i))):
        return False
    else:
        return True

def Ceiling_is_useful(Compressor, i):
    if all(k not in Compressor for k in ("Ceiling" + str(i), "PowerAtCeiling" + str(i))) or (
            Compressor["Ceiling" + str(i)] - Compressor["Altitude" + str(i)] < 2) or (
            Compressor["Power" + str(i)] - Compressor["PowerAtCeiling" + str(i)] < 2):  # For F8F #
        return False
    else:
        return True

def variabler(Compressor, Main, i, alt_RAM, mode):
    """
    Assigns values from FM files to "lower", "lower_power", "higher" and "higher_power" at a given altitude.
    These variables are used by the equationer to make a correct power curve for a given supercharger gear.
    Very complicated; contains most of the logic determinig shape of engine power curves of differnt planes.

    When equationer is run inside this function it means that a power value is calculated recursively. 
    For explanation assume following: 
    Engine with critical altitude at 2000m and 1300hp at military mode. 
    Due to throttling losses it has 1230hp at 1200m. 
    With WEP, critical altitude drops to 1200m.  
    Main["WEP_power_mult"] = 1.15.

    With those parameters equationer is run.
    Based on this a military curve is drawn with all horsepower values multiplied by 1.15, resulting in a mock WEP power curve.
    Then power from 1200m (actual WEP crit alt) of this mock power curve is taken (1230hp*1.15)=1414hp and that is true WEP critical altitude power.
    That means that on WEP, the engine will have critical altitude at 1200m with (1230hp*1.15)=1414hp, not (1300*1.15)=1495hp; that's what I mean by recursion.

    Those values are then assigned to either lower & lower_power or higher & higher_power and based on them a true WEP power curve is drawn.
    Recusive calculation is also used for military power calcuation if in files military power was defined for WEP RPM, not military RPM.
    """

    curvature = 1
    if mode == "military" and alt_RAM <= Compressor["Altitude" + str(i)]:
        if ConstRPM_is(Compressor, i) and ConstRPM_is_below_deck(Compressor, i) and alt_RAM < Compressor["AltitudeConstRPM" + str(i)]:
            # print(getframeinfo(currentframe()).lineno)
            higher = Compressor["AltitudeConstRPM" + str(i)]
            higher_power = 0
            lower = Compressor["AltitudeConstRPM" + str(i)] - 10
            lower_power = 0
        elif (not ConstRPM_bends_below_critalt(Compressor, i) ) and not Power_is_deck_power(Main, Compressor, i):
            # Between the deck and crit alt
            # print(getframeinfo(currentframe()).lineno)
            higher = Compressor["Altitude" + str(i)]
            higher_power = Compressor["Power" + str(i)]
            lower = Main["Deck_Altitude" + str(i)]
            lower_power = Main["Power" + str(i)]
        elif ConstRPM_bends_below_critalt(Compressor, i) and alt_RAM < Compressor["AltitudeConstRPM" + str(i)]:
            # print(getframeinfo(currentframe()).lineno)
            higher = Compressor["AltitudeConstRPM" + str(i)]  # It doesn't change with WEP
            higher_power = Compressor["PowerConstRPM" + str(i)]
            lower = Main["Deck_Altitude" + str(i)]
            lower_power = Main["Power" + str(i)]
        elif ConstRPM_bends_below_critalt(Compressor, i) and alt_RAM >= Compressor["AltitudeConstRPM" + str(i)]:
            # print(getframeinfo(currentframe()).lineno)
            # between start of variable speed and crit alt
            curvature = Compressor["PowerConstRPMCurvature" + str(i)]
            higher = Compressor["Altitude" + str(i)]
            higher_power = Compressor["Power" + str(i)]
            lower = Compressor["AltitudeConstRPM" + str(i)]
            lower_power = Compressor["PowerConstRPM" + str(i)]
        elif Power_is_deck_power(Main, Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            higher = Compressor["Ceiling" + str(i)]
            higher_power = Compressor["PowerAtCeiling" + str(i)]
            lower = Compressor["Altitude" + str(i)]
            lower_power = Compressor["Power" + str(i)]
    if mode == "military" and Compressor["Altitude" + str(i)] < alt_RAM <= Compressor["Old_Altitude" + str(i)]:
        # print(getframeinfo(currentframe()).lineno)
        lower = Compressor["Altitude" + str(i)]
        lower_power = Compressor["Power" + str(i)]
        if not Ceiling_is_useful(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            higher = Compressor["Old_Altitude" + str(i)]
            higher_power = ((equationer(Compressor["Old_Power_new_RPM" + str(i)], Compressor["Altitude" + str(i)],
                                        Main["Power" + str(i)], Main["Deck_Altitude" + str(i)],
                                        Compressor["Altitude" + str(i)], curvature))
                            * (air_pressurer(Compressor["Old_Altitude" + str(i)]) / air_pressurer(
                        Compressor["Altitude" + str(i)])))
            
        if Ceiling_is_useful(Compressor, i) and not ConstRPM_bends_above_crit_alt(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            if Compressor["ExactAltitudes"]:
                # print(getframeinfo(currentframe()).lineno)
                higher = Compressor["Old_Altitude" + str(i)]
                higher_power = equationer(Compressor["PowerAtCeiling" + str(i)],
                                          altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                                                  air_pressurer(Compressor["Altitude" + str(i)]) / air_pressurer(
                                              (Compressor["Altitude" + str(i)])))),
                                          Compressor["Old_Power_new_RPM" + str(i)], Compressor["Altitude" + str(i)],
                                          Compressor["Old_Altitude" + str(i)], curvature)
                # old_version
                # higher_power = equationer(Compressor["PowerAtCeiling" + str(i)],
                #                           altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                #                                   air_pressurer(Compressor["Altitude" + str(i)]) / air_pressurer(
                #                               (Compressor["Altitude" + str(i)])))),
                #                           Compressor["Power" + str(i)], Compressor["Altitude" + str(i)],
                #                           Compressor["Old_Altitude" + str(i)], curvature)
            else:
                # print(getframeinfo(currentframe()).lineno)
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]
        if Ceiling_is_useful(Compressor, i) and ConstRPM_bends_above_crit_alt(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            curvature = Compressor["PowerConstRPMCurvature" + str(i)]
            if Compressor["ExactAltitudes"]:
                # print(getframeinfo(currentframe()).lineno)
                higher = Compressor["Old_Altitude" + str(i)]
                higher_power = equationer(Compressor["PowerAtCeiling" + str(i)],
                                          altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                                                  air_pressurer(Compressor["Altitude" + str(i)]) / air_pressurer(
                                              (Compressor["Altitude" + str(i)])))),
                                          Compressor["Old_Power_new_RPM" + str(i)], Compressor["Altitude" + str(i)],
                                          Compressor["Old_Altitude" + str(i)], curvature)
            else:
                # print(getframeinfo(currentframe()).lineno)
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]
    if mode == "military" and Compressor["Old_Altitude" + str(i)] < alt_RAM:  # TO be chANGED
        # print(getframeinfo(currentframe()).lineno)
        if not Ceiling_is_useful(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            lower = Compressor["Old_Altitude" + str(i)]
            lower_power = ((equationer(Compressor["Old_Power_new_RPM" + str(i)], Compressor["Altitude" + str(i)],
                                        Main["Power" + str(i)], Main["Deck_Altitude" + str(i)],
                                        Compressor["Altitude" + str(i)], curvature))
                            * (air_pressurer(Compressor["Old_Altitude" + str(i)]) / air_pressurer(
                        Compressor["Altitude" + str(i)])))
            higher = alt_RAM
            higher_power = lower_power * (air_pressurer(alt_RAM) / air_pressurer(lower))

        elif Ceiling_is_useful(Compressor, i) and not ConstRPM_bends_above_crit_alt(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            if Compressor["ExactAltitudes"]:
                # print(getframeinfo(currentframe()).lineno)
                lower = Compressor["Old_Altitude" + str(i)]
                lower_power = equationer(Compressor["PowerAtCeiling" + str(i)],
                                          altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                                                  air_pressurer(Compressor["Altitude" + str(i)]) / air_pressurer(
                                              (Compressor["Altitude" + str(i)])))),
                                          Compressor["Old_Power_new_RPM" + str(i)], Compressor["Altitude" + str(i)],
                                          Compressor["Old_Altitude" + str(i)], curvature)
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]
            else:
                # print(getframeinfo(currentframe()).lineno)
                lower = Compressor["Altitude" + str(i)]
                lower_power = Compressor["Power" + str(i)]
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]
        elif Ceiling_is_useful(Compressor, i) and ConstRPM_bends_above_crit_alt(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            curvature = Compressor["PowerConstRPMCurvature" + str(i)]
            if Compressor["ExactAltitudes"]:
                # print(getframeinfo(currentframe()).lineno)
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]
                lower = Compressor["Old_Altitude" + str(i)]
                lower_power = equationer(Compressor["PowerAtCeiling" + str(i)],
                                          altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                                                  air_pressurer(Compressor["Altitude" + str(i)]) / air_pressurer(
                                              (Compressor["Altitude" + str(i)])))),
                                          Compressor["Old_Power_new_RPM" + str(i)], Compressor["Altitude" + str(i)],
                                          Compressor["Old_Altitude" + str(i)], curvature)
            else:
                # print(getframeinfo(currentframe()).lineno)
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]
                lower = Compressor["Old_Altitude" + str(i)]
                lower_power = Compressor["Power" + str(i)]

    ####################################################################################################################
    ###################################################### WEP #########################################################
    ####################################################################################################################
    if mode == "WEP" and alt_RAM <= Main["WEP_crit_altitude"] and alt_RAM <= Compressor[
        "Old_Altitude" + str(i)]:  # I'm really not sure about it
        # print(getframeinfo(currentframe()).lineno)
        if ConstRPM_is(Compressor, i) and ConstRPM_is_below_deck(Compressor, i) and alt_RAM < Compressor["AltitudeConstRPM" + str(i)]:
            # print(getframeinfo(currentframe()).lineno)
            higher = Compressor["AltitudeConstRPM" + str(i)]
            higher_power = 0
            lower = Compressor["AltitudeConstRPM" + str(i)] - 10
            lower_power = 0
        elif (not ConstRPM_bends_below_critalt(Compressor, i) ) and not Power_is_deck_power(Main, Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            # Between the deck and crit alt of stage above 1
            if Compressor["ExactAltitudes"]:
                higher = Main["WEP_crit_altitude"]
                higher_power = equationer(Compressor["Power" + str(i)] * Main["WEP_power_mult"],
                                          Compressor["Altitude" + str(i)],
                                          Main["Power" + str(i)] * Main["WEP_power_mult"],
                                          Main["Deck_Altitude" + str(i)], higher,
                                          curvature)
                lower = Main["WEP_deck_altitude"]
                lower_power = equationer(Compressor["Power" + str(i)] * Main["WEP_power_mult"], Compressor["Altitude" + str(i)],
                                         Main["Power" + str(i)] * Main["WEP_power_mult"], Main["Deck_Altitude" + str(i)], lower,
                                         curvature)
            else:
                higher = Main["WEP_crit_altitude"]
                higher_power = Compressor["Power" + str(i)] * Main["WEP_power_mult"]
                lower = Main[
                    "Deck_Altitude" + str(0)]  # Apparently doesn't change with WEP, just like constrpm altitude
                lower_power = Main["Power" + str(i)] * Main["WEP_power_mult"]
        elif Compressor["ExactAltitudes"] and alt_RAM < Compressor["AltitudeConstRPM" + str(i)]:
            # print(getframeinfo(currentframe()).lineno)
            # Below 1st variable speed super
            higher_power = Compressor["PowerConstRPM" + str(i)] * Main["WEP_power_mult"]
            lower = Main["Deck_Altitude" + str(i)]  
            lower_power = Main["Power" + str(i)] * Main["WEP_power_mult"]
            higher = Compressor["AltitudeConstRPM" + str(i)]  # It doesn't lower with WEP

        elif not Compressor["ExactAltitudes"] and alt_RAM < Main["WEP_powerconstRPM"]:
            # print(getframeinfo(currentframe()).lineno)
            higher_power = Compressor["PowerConstRPM" + str(i)] * Main["WEP_power_mult"]
            lower = Main["Deck_Altitude" + str(i)]  
            lower_power = Main["Power" + str(i)] * Main["WEP_power_mult"]
            higher = Main["WEP_powerconstRPM"]  # Here it does lower with WEP
        elif Compressor["ExactAltitudes"] and alt_RAM >= Compressor["AltitudeConstRPM" + str(i)]:
            # print(getframeinfo(currentframe()).lineno)
                        # between start of variable speed and crit alt
            curvature = Compressor["PowerConstRPMCurvature" + str(i)]
            higher = Main["WEP_crit_altitude"]
            lower_power = Compressor["PowerConstRPM" + str(i)] * Main["WEP_power_mult"]  #recursion needed either way
            lower = Compressor["AltitudeConstRPM" + str(i)]  # altitude doesn't change when wepping
            higher_power = equationer(Compressor["Power" + str(i)] * Main["WEP_power_mult"],
                                      Compressor["Altitude" + str(i)],
                                      Compressor["PowerConstRPM" + str(i)] * Main["WEP_power_mult"],
                                      Compressor["AltitudeConstRPM" + str(i)], higher, curvature)  # yes recursion

        elif not Compressor["ExactAltitudes"] and alt_RAM >= Main["WEP_powerconstRPM"]:
            # print(getframeinfo(currentframe()).lineno)
            curvature = Compressor["PowerConstRPMCurvature" + str(i)]
            higher = Main["WEP_crit_altitude"]
            lower_power = Compressor["PowerConstRPM" + str(i)] * Main["WEP_power_mult"]  #recursion needed either way
            lower = Main["WEP_powerconstRPM"]
            higher_power = Compressor["Power" + str(i)] * Main["WEP_power_mult"]  # no recursion
        elif Power_is_deck_power(Main, Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            if Compressor["ExactAltitudes"]:
                higher = Compressor["Ceiling" + str(i)]
                higher_power = equationer(Compressor["PowerAtCeiling" + str(i)] * Main["WEP_power_mult"],
                                              altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                                                      air_pressurer(Main["WEP_crit_altitude"]) / air_pressurer(
                                                  (Compressor["Altitude" + str(i)])))),
                                              Compressor["Power" + str(i)] * Main["WEP_power_mult"],
                                              Main["WEP_crit_altitude"],
                                              Compressor["Ceiling" + str(i)], curvature)
            else:
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]
                lower = Main["WEP_crit_altitude"]
                lower_power = Compressor["Power" + str(i)] * Main["WEP_power_mult"]
    if mode == "WEP" and Compressor["Old_Altitude" + str(i)] < alt_RAM <= Main["WEP_crit_altitude"]:
        # print(getframeinfo(currentframe()).lineno)
        # For situations when WEP crit alt is higher than mil Compressor["Old_Altitude" + str(i)].
        # In those cases power doesn't change between those 2 altitudes (Fw-190A-1).
        higher = Main["WEP_crit_altitude"]
        higher_power = equationer(Compressor["Power" + str(i)] * Main["WEP_power_mult"], Compressor["Altitude" + str(i)],
                                  Main["Power" + str(i)] * Main["WEP_power_mult"],
                                  Main["Deck_Altitude" + str(i)], Compressor["Old_Altitude" + str(i)],
                                  curvature)
        lower = Compressor["Old_Altitude" + str(i)]
        lower_power = higher_power
    if mode == "WEP" and round(Main["WEP_crit_altitude"]) < alt_RAM <= round(Compressor["Old_Altitude" + str(i)]):
        # print(getframeinfo(currentframe()).lineno)
        
        if not ConstRPM_bends_below_WEP_critalt(Main, Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            lower = Main["WEP_crit_altitude"]
            if Compressor["ExactAltitudes"]:  # This means, that WEP crit alt power is calculated with recursion
                lower_power = equationer(Compressor["Power" + str(i)] * Main["WEP_power_mult"], Compressor["Altitude" + str(i)],
                                         Main["Power" + str(i)] * Main["WEP_power_mult"],
                                         Main["Deck_Altitude" + str(i)], lower, curvature)
            else:  # This means, that WEP crit alt power is calculated simply with no with recursion
                lower_power = Compressor["Power" + str(i)] * Main["WEP_power_mult"]
        elif ConstRPM_bends_below_WEP_critalt(Main, Compressor, i):
            
            # print(getframeinfo(currentframe()).lineno)
            lower = Main["WEP_crit_altitude"]
            if Compressor["ExactAltitudes"]:  # This means, that WEP crit alt power is calculated with recursion
                lower_power = equationer(Compressor["Power" + str(i)] * Main["WEP_power_mult"], Compressor["Altitude" + str(i)],
                                         Compressor["PowerConstRPM" + str(i)] * Main["WEP_power_mult"],
                                         Compressor["AltitudeConstRPM" + str(i)], lower,
                                         Compressor["PowerConstRPMCurvature" + str(i)])
            else:  # This means, that WEP crit alt power is calculated simply with no with recursion
                lower_power = Compressor["Power" + str(i)] * Main["WEP_power_mult"]
        if not Ceiling_is_useful(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            higher = Compressor["Old_Altitude" + str(i)]
            higher_power = ((equationer(Compressor["Power" + str(i)] * Main["WEP_power_mult"], Compressor["Altitude" + str(i)],
                                        Main["Power" + str(i)] * Main["WEP_power_mult"], Main["Deck_Altitude" + str(i)],
                                        higher, curvature))
                            * (air_pressurer(Compressor["Old_Altitude" + str(i)]) / air_pressurer(lower)))
            # higher = alt_RAM
            # higher_power = lower_power * (air_pressurer(alt_RAM) / air_pressurer(lower)) #why did i do this option? for f8f weird curve?
        if Ceiling_is_useful(Compressor, i) and not ConstRPM_bends_above_crit_alt(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            if Compressor["ExactAltitudes"]:
                higher = Compressor["Old_Altitude" + str(i)]
                higher_power = equationer(Compressor["PowerAtCeiling" + str(i)] * Main["WEP_power_mult"],
                                          altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                                                  air_pressurer(Main["WEP_crit_altitude"]) / air_pressurer(
                                              (Compressor["Altitude" + str(i)])))),
                                          Compressor["Old_Power_new_RPM" + str(i)] * Main["WEP_power_mult"], Main["WEP_crit_altitude"],
                                          Compressor["Old_Altitude" + str(i)], curvature)
            else:
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]
        elif Ceiling_is_useful(Compressor, i) and ConstRPM_bends_above_crit_alt(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            curvature = Compressor["PowerConstRPMCurvature" + str(i)] # for P-63s bulging power above crit alt. Work in progress
            if Compressor["ExactAltitudes"]:
                higher = Compressor["Old_Altitude" + str(i)]
                higher_power = equationer(Compressor["PowerAtCeiling" + str(i)] * Main["WEP_power_mult"],
                                          altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                                                  air_pressurer(Main["WEP_crit_altitude"]) / air_pressurer(
                                              (Compressor["Altitude" + str(i)])))),
                                          Compressor["Old_Power_new_RPM" + str(i)] * Main["WEP_power_mult"], Main["WEP_crit_altitude"],
                                          Compressor["Old_Altitude" + str(i)], curvature)
            else:
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]
    if mode == "WEP" and alt_RAM > Compressor["Old_Altitude" + str(i)] and alt_RAM > Main["WEP_crit_altitude"]:
        if Main["WEP_crit_altitude"] < Compressor["Altitude" + str(i)]:
            # print(getframeinfo(currentframe()).lineno)
            lower = Compressor["Old_Altitude" + str(i)]
            if not Ceiling_is_useful(Compressor, i):
                # print(getframeinfo(currentframe()).lineno)
                lower_power = ((equationer(Compressor["Power" + str(i)] * Main["WEP_power_mult"],
                                            Compressor["Altitude" + str(i)],
                                            Main["Power" + str(i)] * Main["WEP_power_mult"],
                                            Main["Deck_Altitude" + str(i)],
                                            lower, curvature))
                               * (air_pressurer(Compressor["Old_Altitude" + str(i)]) / air_pressurer(Main["WEP_crit_altitude"])))
            else:
                if Compressor["ExactAltitudes"]:
                    # print(getframeinfo(currentframe()).lineno)
                    lower_power = equationer(Compressor["PowerAtCeiling" + str(i)] * Main["WEP_power_mult"],
                                            altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                                                        air_pressurer(Main["WEP_crit_altitude"]) / air_pressurer(
                                                    (Compressor["Altitude" + str(i)])))),
                                            Compressor["Old_Power_new_RPM" + str(i)] * Main["WEP_power_mult"],
                                            Main["WEP_crit_altitude"],
                                            lower,
                                            curvature)
                else:
                    lower = Main["WEP_crit_altitude"]
                    lower_power = Compressor["Power" + str(i)] * Main["WEP_power_mult"]
                
        elif not ConstRPM_bends_below_critalt(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            lower = Main["WEP_crit_altitude"]
            if Compressor["ExactAltitudes"]:
                                # This means, that WEP crit alt power is calculated with recursion
                lower_power = equationer(Compressor["Power" + str(i)] * Main["WEP_power_mult"], Compressor["Altitude" + str(i)],
                                         Main["Power" + str(i)] * Main["WEP_power_mult"],
                                         Main["Deck_Altitude" + str(i)], Compressor["Old_Altitude" + str(i)],
                                         curvature)
            else:
                                # This means, that WEP crit alt power is calculated simply with no with recursion
                lower_power = Compressor["Power" + str(i)] * Main["WEP_power_mult"]
        elif ConstRPM_bends_below_critalt(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            lower = Main["WEP_crit_altitude"]
            lower_power = equationer(Compressor["Power" + str(i)] * Main["WEP_power_mult"], Compressor["Altitude" + str(i)],
                                     Compressor["PowerConstRPM" + str(i)] * Main["WEP_power_mult"],
                                     Compressor["AltitudeConstRPM" + str(i)], lower, curvature)
        if not Ceiling_is_useful(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            higher = alt_RAM
            higher_power = lower_power * (air_pressurer(alt_RAM) / air_pressurer(lower))
        if Ceiling_is_useful(Compressor, i) and not ConstRPM_bends_above_crit_alt(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            if Compressor["ExactAltitudes"]:
                higher = altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                            air_pressurer(Main["WEP_crit_altitude"]) / air_pressurer((Compressor["Altitude" + str(i)]))))
                higher_power = Compressor["PowerAtCeiling" + str(i)] * Main["WEP_power_mult"]
            else:
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]

        if Ceiling_is_useful(Compressor, i) and ConstRPM_bends_above_crit_alt(Compressor, i):
            # print(getframeinfo(currentframe()).lineno)
            curvature = Compressor["PowerConstRPMCurvature" + str(i)] # for P-63s bulging power above crit alt. Work in progress
            if Compressor["ExactAltitudes"]:
                higher = altitude_at_pressure(air_pressurer(Compressor["Ceiling" + str(i)]) * (
                            air_pressurer(Main["WEP_crit_altitude"]) / air_pressurer((Compressor["Altitude" + str(i)]))))
                higher_power = Compressor["PowerAtCeiling" + str(i)]
            else:
                higher = Compressor["Ceiling" + str(i)]
                higher_power = Compressor["PowerAtCeiling" + str(i)]
        if (higher < lower) and (higher_power > lower_power):
            lower, higher = higher, lower
            lower_power, higher_power = higher_power, lower_power

    # print(alt_RAM, '[',higher_power, higher, lower_power, lower, curvature,']', Compressor["Power" + str(i)] , 'old_altitude: ', Compressor["Old_Altitude" + str(i)], 'new_altitude: ', Compressor["Altitude" + str(i)], Compressor["Old_Power" + str(i)] , Compressor["Old_Altitude" + str(i)], Main["WEP_crit_altitude"], )
    return higher_power, higher, lower_power, lower, curvature


########################################################################################################################

def equationer(higher_power, higher, lower_power, lower, alt_RAM, curvature):
    """
    The function calculating power at altitudes between 'lower' and 'higher'.
    It draws a staight line between [lower_power, lower] and [higher_power, higher] and applies curvature to this line.
    """
    power_difference = 0
    if alt_RAM >= lower:
        power_difference = (higher_power - lower_power)
    elif alt_RAM < lower:
        power_difference = (lower_power - higher_power)

    curve_equation = lower_power + power_difference * (abs((air_pressurer(alt_RAM) - air_pressurer(lower)) /
                                                           (air_pressurer(higher) - air_pressurer(lower)))) ** curvature
    
    return curve_equation


def power_curve_culator(named_fm_dict, named_central_dict, speed, speed_type, air_temp, octane, engine_modes, alt_tick):
    """
    A bulk function running previous functions to make a list of engine power values from -4000m to 20000m for every superchrger gear.
    """
    plane_speed_multipliers = {}
    named_power_curves = {}
    compr_stages_count = 1
    for plane_name, central_dict in named_central_dict.items():
        fm_dict = named_fm_dict[plane_name]
        Engine, Compressor, Main, Afterburner, Propeller = engine_shortcuter(fm_dict)
        "Prepping parameters in fm_dict for calculation"
        old_type_fm_detector(Compressor, Main)
        exception_fixer(plane_name, Compressor, Main)
        rpm_er(fm_dict, Main, Propeller)
        wep_rpm_ratioer(Main, Compressor, Propeller)
        wep_mp_er(Engine, Compressor, Main, Afterburner)
        brrritish_octane_adder(central_dict, Main, octane)

        for compr_stage in range(0, 6):
            if "Power" + str(compr_stage) in Compressor:
                compr_stages_count = compr_stage + 1
        # print(compr_stages_count, "compr_stg")
        if not Afterburner:
            final_engine_modes = ["military"]
        else:
            final_engine_modes = engine_modes
        power_curves = optimal_dict_initializer(final_engine_modes, compr_stages_count)
        for g in range(0, compr_stages_count):
                soviet_octane_adder(central_dict, Compressor, Main, g, octane)
        for h in range(0, compr_stages_count):
            definition_alt_power_adjuster(Main, Compressor, Propeller, h)
            deck_power_maker(Main, Compressor, h)
        print(plane_name)
        # print( Main["military_RPM"], Main["default_RPM"], Main["WEP_RPM"])
        # if "GovernorMaxParam" in Propeller.keys():
        #     print('mil_RPM: ',Main["military_RPM"], 'WEP_RPM: ', Main["WEP_RPM"], 'governor_mil_RPM: ', Propeller["GovernorMaxParam"], 'governor_WEP_RPM: ', Propeller["GovernorAfterburnerParam"])
        
        'Calculations begin'
        for i in range(0, compr_stages_count):
            for mode in final_engine_modes:
                wep_mulitiplierer(octane, Main, Compressor, i, mode)
                for alt in range(-4000, 20000, alt_tick):

                    if speed > 0:
                        alt_RAM = rameffect_er(alt, air_temp, speed, speed_type, Compressor)
                    else:
                        alt_RAM = alt
                    # print(alt_RAM)
                    higher_power, higher, lower_power, lower, curvature = variabler(Compressor, Main, i, alt_RAM, mode)
                    curve_equation = round(equationer(higher_power, higher, lower_power, lower, alt_RAM, curvature),1)
                    # power_curves[mode][i].append(curve_equation)
                    power_curves[mode][i].append(curve_equation)
        plane_speed_multipliers[plane_name] = Compressor["SpeedManifoldMultiplier"]
        named_power_curves[plane_name] = power_curves
    named_power_curves_merged = plot_merger(named_power_curves)
    return named_power_curves_merged, plane_speed_multipliers


def plot_merger(named_power_curves):
    """
    Combines power curve dictionaries of every supercharger speed/stage into one optimal curve, both for military and WEP power
    """
    named_power_curves_merged = {}
    for plane_name, power_curves in named_power_curves.items():
        MODEL_dict = {}
        power_curves_merged = {}
        for mode, lines in power_curves.items():
            for i in lines:
                if lines[i]:
                    MODEL_dict = lines[i]
            for i in lines:
                for alt in range (len(lines[i])):
                    if MODEL_dict[alt] < lines[i][alt]:
                        MODEL_dict[alt] = lines[i][alt]
                power_curves_merged[mode] = MODEL_dict
        named_power_curves_merged[plane_name] = power_curves_merged
    return named_power_curves_merged

########################################################################################################################

def engine_power_to_json(power_write_dir, named_power_curves_merged, plane_speed_multipliers,  plane_engine_count):
    """Saves calcualted engine power values into .json file for each plane

    Args:
        power_write_dir (_type_): directory to which power .json files should be weritten
        named_power_curves_merged (_type_): the input set of dictionaties to be converted into .json
        plane_speed_multipliers (_type_): multipliers of dynamic pressure, needed for RAM effect calculation
        plane_engine_count (_type_): number of engines, needed for power/weight calcualtion
    """
    destination = Path.cwd() / power_write_dir
    destination.mkdir(exist_ok=True, parents=True)
    for (planename, plane_power), (planename2, speed_mult), (planename3, engine_count) in zip(named_power_curves_merged.items(), plane_speed_multipliers.items(), plane_engine_count.items()):
        assert planename == planename2 == planename3 # To check if 3 dictionaries are in sync
        print(planename)
        for engine_mode, power_of_mode in plane_power.items():
            complete_power_dict = {}
            complete_power_dict['speed_mult'] = speed_mult
            complete_power_dict['engine_count'] = engine_count
            complete_power_dict['power_at_alt'] = power_of_mode
            powerwritepath = Path(power_write_dir) / (planename + "_" + engine_mode + ".json")
            with open(powerwritepath, 'w') as plane_power_piston_json:
                json.dump(complete_power_dict, plane_power_piston_json)

def main():
    help(engine_power_to_json)        
if __name__ == "__main__":
    main()