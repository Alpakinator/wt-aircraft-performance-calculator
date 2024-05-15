def air_pressurer(alt):
    """
    Calculates air pressure at a given altitude
    based on www.engineeringtoolbox.com
    :param alt:
    :return:
    """
    air_pressure = (1 - 0.0000225577 * alt) ** 5.25588
    
    return air_pressure


def altitude_at_pressure(air_pressure):
    """
    Calculates altitude af air given air pressure
    inverse of 'air_pressurer' function
    :param air_pressure:
    :return:
    """
    alt = (1 - (air_pressure ** (1 / 5.25588))) * (1 / 0.0000225577)
    return alt


def air_densitier(air_pressure, air_temp, alt):
    """
    Calculates air density given its pressure and temperature
    291.127 R_specific was empirically calculated to match the output of
    https://www.calctool.org/atmospheric-thermodynamics/air-density 
    :param alt:
    :param air_pressure:
    :param air_temp:
    :return:
    """
    air_temp_at_alt = air_temp - (0.0065 * alt)
    R_specific = 287.0500676
    air_density = 101325 * air_pressure / ((273.15 + air_temp_at_alt) * R_specific)
    return air_density


def ias_tas_er(speed, air_density):
    """
    Calculates TAS based on IAS and air density
    0.72 used to be 1.225
    """
    speed = speed * (1.225 / air_density) ** (1 / 2)
    return speed


def rameffect_er(alt, air_temp, speed, speed_type, Compressor):
    """
    Based or air RAM effect and alt calculates equivalent alt with no ram effect where total air pressure is identical
    :return:
    """
    air_pressure = air_pressurer(alt)
    air_density = air_densitier(air_pressure, air_temp, alt)
    if speed == 0:
        return alt     
    elif speed_type == "IAS":
        TASspeed = ias_tas_er(speed, air_density)
    else:
        TASspeed = speed
    dynamic_pressure = (((air_density * ((TASspeed / 3.6) ** 2)) / 2) * Compressor) / 101325
    total_pressure = air_pressure + dynamic_pressure
    alt_RAM = int(altitude_at_pressure(total_pressure))
    return alt_RAM