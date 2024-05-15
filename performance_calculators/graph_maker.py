import re
import plotly.express as px
import pandas as pd
from PIL import Image

def dict_dataframer(named_power_curves_merged, alt_unit):
    """
    Converts military and WEP power curve dictionaries into dataframes, joins them and then adds to a MODEL dataframe
    """
    MODEL_dataf_all, MODEL_WEP_dataf, MODEL_military_dataf, joined_plots_dataf = \
        (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),)
    for plane_name, power_curves_merged in named_power_curves_merged.items():

        if len(plane_name) >= 30:
            plane_name = plane_name[:50]
        if "military" in power_curves_merged:
            MODEL_military_dataf = pd.DataFrame(power_curves_merged["military"].items(),
                                                columns=["Altitude [" + alt_unit + "]", plane_name + ' (mil)' ])
            joined_plots_dataf = MODEL_military_dataf
        if "WEP" in power_curves_merged:
            MODEL_WEP_dataf = pd.DataFrame(power_curves_merged["WEP"].items(),
                                           columns=["Altitude [" + alt_unit + "]", plane_name + ' (WEP)' ])
            joined_plots_dataf = MODEL_WEP_dataf
        if "military" in power_curves_merged and "WEP" in power_curves_merged:
            joined_plots_dataf = MODEL_military_dataf.merge(MODEL_WEP_dataf, on=("Altitude [" + alt_unit + "]"))  # pass column name as a tuple

        if "Altitude [" + alt_unit + "]" not in MODEL_dataf_all:
            MODEL_dataf_all = MODEL_dataf_all.assign(altitude=pd.to_numeric(joined_plots_dataf["Altitude [" + alt_unit + "]"]))
        if "military" in power_curves_merged:
            MODEL_dataf_all = MODEL_dataf_all.assign(power_mil=joined_plots_dataf[plane_name + ' (mil)' ])

        if "WEP" in power_curves_merged:
            MODEL_dataf_all = MODEL_dataf_all.assign(power_WEP=joined_plots_dataf[plane_name + ' (WEP)' ])
        MODEL_dataf_all = MODEL_dataf_all.rename(columns={"altitude": "Altitude [" + alt_unit + "]",
                                                              "power_mil": plane_name + ' (mil)' })
        MODEL_dataf_all = MODEL_dataf_all.rename(columns={"altitude": "Altitude [" + alt_unit + "]",
                                                              "power_WEP": plane_name + ' (WEP)' })
    return MODEL_dataf_all 
            

def plotter(MODEL_TEST_dataf, highest_alt, alt_unit, speed, speed_type, speed_unit, air_temp, air_temp_unit,
            axis_layout, plot_t):
    """
    Plots scatter-plots of modelled power curves and tested ones with plotly, and adjusts the plot to look pleasing.
    """
    print(MODEL_TEST_dataf)
    # power_columns = MODEL_TEST_dataf.columns.values.tolist()[1:] # fastest, doesn't work with premade files
    power_columns = [col for col in MODEL_TEST_dataf.columns if any(x in col for x in ('(mil)', '(WEP)'))]
    # Find the highest power + 100, to use for x-axis
    colour_set = ['rgb(228,26,28)', 'rgb(55,126,184)', 'rgb(77,175,74)', 'rgb(152,78,163)', 'rgb(255,127,0)', 
                  'rgb(255,255,51)', 'rgb(166,86,40)', 'rgb(247,129,191)', 'rgb(153,153,153)', 'rgb(27,158,119)', 
                  'rgb(217,95,2)', 'rgb(117,112,179)', 'rgb(231,41,138)', 'rgb(102,166,30)', 'rgb(230,171,2)', 
                  'rgb(166,118,29)', 'rgb(102,102,102)', 'rgb(254,0,206)', 'rgb(34,255,167)']
        
    WTAPPC_Logo = Image.open("readme_assets/WTAPPC_logo.png")

    if speed == 69:
        speed = "69 (nice)"
    if plot_t == 'power':
        highest_power = (MODEL_TEST_dataf[power_columns].to_numpy().max()) + 100
        lowest_power = (MODEL_TEST_dataf[power_columns].to_numpy().min()) - 100
        title = "Engine power at different altitudes, when flying at " + str(speed) +" "+ speed_unit +" "+ speed_type
        response_axis_title = "Power [hp]"
        response_axis_tick = 100

    elif plot_t == 'power/weight':
        highest_power = (MODEL_TEST_dataf[power_columns].to_numpy().max()) + 0.03
        lowest_power = (MODEL_TEST_dataf[power_columns].to_numpy().min()) - 0.03
        title = "Power to weight ratio at different altitudes, when flying at " + str(
            speed) + " " + speed_unit + " " + speed_type
        response_axis_title = "Power/weight [hp/kg]"
        response_axis_tick = 0.05
    explanatory_axis_title = "Altitude ["+alt_unit+"]"
    explanatory_axis_tick = 1000
    if alt_unit == 'ft':
        explanatory_axis_tick = 3000
    air_temperature = "Temperature at sea level: " + str(air_temp) + " " + air_temp_unit

    ###PLOTLY###
    if axis_layout == True:
        final_plot = px.scatter(data_frame=MODEL_TEST_dataf, x=power_columns, y="Altitude [" + alt_unit + "]",
                                title=title, ).update_traces(mode="lines+markers", line={'width': 4},marker_size=3)
        final_plot.update_xaxes(range=[lowest_power, highest_power])
        final_plot.update_yaxes(range=[0, highest_alt])
        final_plot.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=response_axis_tick, tickfont=dict(size=14)),
                                 xaxis_title=dict(text=response_axis_title, font=dict(size=18)),
                                 yaxis=dict(tickmode='linear', tick0=0, dtick=explanatory_axis_tick, tickfont = dict(size=14)),
                                 yaxis_title=dict(text=explanatory_axis_title, font=dict(size=18)))
        # Addon for testing purposes. Adds curves from testflight
        for column in MODEL_TEST_dataf:
            if "TestPower" in column:
                final_plot.add_scatter(name=column, x=MODEL_TEST_dataf[column],
                                    y=MODEL_TEST_dataf["Altitude, m" + re.findall(r'\d+',column)[0]], line={'width': 4}) 
        
    else:
        final_plot = px.scatter(data_frame=MODEL_TEST_dataf, y=power_columns, x="Altitude [" + alt_unit + "]",
                                title=title, ).update_traces(mode="lines+markers", line={'width': 4},marker_size=3)
        final_plot.update_yaxes(range=[lowest_power, highest_power])
        final_plot.update_xaxes(range=[0, highest_alt])
        final_plot.update_layout(yaxis=dict(tickmode='linear', tick0=0, dtick=response_axis_tick, tickfont=dict(size=14)),
                                 yaxis_title=dict(text=response_axis_title, font=dict(size=18)),
                                 xaxis=dict(tickmode='linear', tick0=0, dtick=explanatory_axis_tick, tickfont = dict(size=14)),
                                 xaxis_title=dict(text=explanatory_axis_title, font=dict(size=18)))
        # Addon for testing purposes. Adds curves from testflight
        for column in MODEL_TEST_dataf:
            if "TestPower" in column:
                final_plot.add_scatter(name=column, x=MODEL_TEST_dataf["Altitude, m" + re.findall(r'\d+',column)[0]],
                                    y=MODEL_TEST_dataf[column], line={'width': 6}) 
               
    final_plot.add_annotation(text=air_temperature, showarrow=False, font=dict(size=14), xref="paper",  x=0, yref="paper",  y=-0.06)
    final_plot.add_annotation(text="Do not use in War Thunder bug reports, because it's not <br>a valid source. Otherwise Gaijin can ban datamining forever!", 
                              opacity= 0.12, showarrow= False, font=dict(size= 20, color='white'), 
                              x= 1, y= 0, xref= "paper", yref= "paper", xanchor= 'right', yanchor= 'bottom', 
                                textangle=0),


    final_plot.add_layout_image(dict(x= 0, y= 0.0015,  sizex= 0.12, sizey= 0.12, source= WTAPPC_Logo, opacity= 0.5, xanchor= "left", xref= "paper", yanchor= "bottom", yref= "paper"
    ))
    final_plot.update_layout(template="plotly_dark", paper_bgcolor='#111111',plot_bgcolor='#111111',
                             autosize=True, title=dict(font=dict(size=22), x=0.5),
                             legend=dict(yanchor="top",y=1,xanchor="right", x=1,font=dict(size=14)), legend_title=None,
                             hoverlabel_font_color='#F2F5FA', font_family=("Inter, Segoe UI"),
                             margin=dict(l=100,r=25,b=5,t=50,pad=5), modebar_orientation= 'h')
    final_plot.show(config={'modeBarButtonsToAdd': ["hoverclosest","hovercompare"]})
    return final_plot


# "https://raw.githubusercontent.com/Alpakinator/wt-aircraft-performance-pre-calculator/main/WTAPPC_logo.png"