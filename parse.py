# Parser for Shaftkit MSA SHAFT.OUT file
# Zac Schramm
# April 2022
# Use compile.py script to create exectuable
# Run this (and compiled exe) from same directory as SHAFT.OUT

from cmath import sqrt
import os
import time
from csv import reader, writer
import configparser
from math import pi
from scipy.interpolate import interp1d
from matplotlib.collections import PatchCollection, cm
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon

def read_config(filename):
    # Config file
    global settings
    settings = dict([])
    config = configparser.ConfigParser(allow_no_value=True)

    # check if file exists already
    if os.path.isfile(filename):
        # Read in config file
        config.read(filename)
        try:
            settings['shaft_out_location'] = config['settings']['shaft_out_location']
        except KeyError:
            settings['shaft_out_location'] = ""

        try:
            settings['brg_names'] = config['settings']['brg_names'].split(',')
        except KeyError:
            settings['brg_names'] = ""

        try:
            settings['gauge_nodes'] = config['settings']['gauge_nodes'].split(',')
        except KeyError:
            settings['gauge_nodes'] = ""

    else:
        # create default file
        settings['shaft_out_location'] = ''
        settings['brg_names'] = 'aft sterntube, fwd. sterntube, aft gear, fwd. gear'
        settings['gauge_nodes'] = ''
        config['settings'] = {'shaft_out_location' : settings['shaft_out_location'],
                              'brg_names' : settings['brg_names'],
                              'gauge_nodes' : settings['gauge_nodes']}
        with open(filename, 'w') as config_file:
            config.write(config_file)
            print(f'Created default {filename} file')
        pass

def linspace(a, b, n=100):
    # Generate points along range (instead of importing numpy library)
    if n < 2:
        return b
    diff = (float(b) - a)/(n - 1)
    return [diff * i + a  for i in range(n)]

def read_data(filename):
    # Read in SHAFT.OUT

    ##############################################
    # Initialize variables
    nodes = []
    elements = []
    conc_masses = []
    conc_springs = []
    conc_damps = []
    forces = []
    spring_reacts = []
    disps = []
    beam_forces = []
    brg_reacts = []
    inf = []

    ################################################
    # open and read in output file
    try:
        with open(filename, "r") as file:
            data = [x.replace('\0', '') for x in file]
            csvreader = reader(data, delimiter='\t')
            for k, row in enumerate(csvreader):
        
                try:
                    if row[0] == " NODES":
                        row = next(csvreader)
                        while row[0] != " ELEMEN DEF":
                            x = row[0].split()
                            nodes.append([int(x[0]), float(x[1])])
                            row = next(csvreader)

                    if row[0] == " BEAM TYPES ":
                        row = next(csvreader)
                        while row[0] != " CONC MASS":
                            x = row[0].split()
                            elements.append([float(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4])])
                            row = next(csvreader)

                    if row[0] == " CONC MASS":
                        row = next(csvreader)
                        while row[0] != " CONC SPRING":
                            x = row[0].split()
                            conc_masses.append([int(x[0]), int(x[1]), float(x[2])])
                            row = next(csvreader)

                    if row[0] == " CONC SPRING":
                        row = next(csvreader)
                        while row[0] != " CONC DAMP":
                            x = row[0].split()
                            conc_springs.append([int(x[0]), int(x[1]), float(x[2])])
                            row = next(csvreader)

                    if row[0] == " CONC DAMP":
                        row = next(csvreader)
                        while row[0] != " Force No.   Type    Node   DOF":
                            x = row[0].split()
                            conc_damps.append([int(x[0]), int(x[1]), float(x[2])])
                            row = next(csvreader)

                    if row[0] == " Force No.   Type    Node   DOF":
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        while row[0] != "           SPRING REACTIONS":
                            x = row[0].split()
                            forces.append([int(x[0]), int(x[1]), int(x[2]), int(x[3]), float(x[4])])
                            row = next(csvreader)

                    if row[0] == "           SPRING REACTIONS":
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        while row[0] != "           DISPLACEMENTS":
                            x = row[0].split()
                            spring_reacts.append([int(x[0]), int(x[1]), float(x[2])])
                            row = next(csvreader)

                    if row[0] == "           DISPLACEMENTS":
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        while row[0] != "    BEAM FORCES":
                            x = row[0].split()
                            disps.append([int(x[0]), float(x[1]), float(x[2])])
                            row = next(csvreader)

                    if row[0] == "    BEAM FORCES":
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        while row[0] != "Bearing Reactions":
                            x = row[0].split()
                            beam_forces.append([int(x[0]), int(x[1]), float(x[2]),  float(x[3])])
                            row = next(csvreader)

                    if row[0] == "Bearing Reactions":
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        x = row[0].split()
                        brg_reacts.append([float(x[0]), float(x[1]), float(x[2])])

                    if row[0] == "Influence Coefficients":
                        row = next(csvreader)
                        row = next(csvreader)
                        row = next(csvreader)
                        while len(row) != 0:
                            # Characteres per value (since sometimes no whitespace between)
                            num = int(len(row[0]) / 10)
                            skip =  len(row[0]) - 10*num
                            inf.append([float(row[0][skip+i*10:skip+i*10+10])/1000 for i in range(num)])
                            row = next(csvreader)

                # if row data exception, continue
                except Exception as e:
                    print(f'Line {k} Exception: {e}')
                    pass
    
    # filename exception 
    except Exception as e:
        print(e)
        quit()
    

    ############################################################
    # Assemble model [element num, OD (m), ID (m), E (MPa), G (MPa), rho(kg/m^3),
    #                 length (m), mass (kg), section modulus (m^3), mom. inertia (m^4)]
    # Start with original read in data
    model = elements.copy()

    # for each line, calculate additional values and add to row
    for i in range(len(elements)):
            length = nodes[i+1][1] - nodes[i][1]
            mass = (elements[i][0]**2 - elements[i][1]**2) * pi / 4 * elements[i][4] * length
            inertia = pi / 64 * (elements[i][0]**4 - elements[i][1]**4)
            secmod = inertia / (elements[i][0] / 2)
            model[i] = [i+1, *model[i], length, mass, secmod, inertia]

    # for v in zip(model):
    #     print (v)

    ############################################################
    # Assemble output [node num, x (m), disp (mm), slope (mrad), shear (kN),
    #                  bm (kNm), bs (MPa)]
    # all values left side of element except last value (and bending moment in shaftkit is right side)
    output = []
 
    # first node
    bs =  beam_forces[0][3] /1000 * model[0][1]/2 / model[0][9] / 1000
    output.append([nodes[0][0], nodes[0][1], disps[0][1]*1000, disps[0][2]*1000,
                   beam_forces[0][2]/1000, beam_forces[0][3]/1000, bs])
    
    # remainder of nodes
    for i in range(1, len(nodes)-1):
        bs =  beam_forces[2*i-1][3] /1000 * model[i][1]/2 / model[i][9] / 1000
        output.append([nodes[i][0], nodes[i][1], disps[i][1]*1000,
                       disps[i][2]*1000, beam_forces[2*i][2]/1000,
                       beam_forces[2*i-1][3]/1000,  bs])

    # last node
    beam_forces[-1][3] /1000 * model[-1][1]/2 / model[-1][9] / 1000
    output.append([nodes[-1][0], nodes[-1][1], disps[-1][1]*1000, disps[-1][2]*1000,
                   beam_forces[-1][2]/1000, beam_forces[-1][3]/1000, bs])

    #############################################################
    # Tabulate Sums
    # Total nodes and elements
    telems = len(model)
    tlength = output[-1][1]

    # Sum of Element Masses (kg)
    tmass_elems = 0
    for elem in model:
        tmass_elems += elem[7]
    
    # Sum of Concentrated Masses (kg)
    tmass_conc = 0
    for mass in conc_masses:
        tmass_conc += mass[2]
    
    # Sum of Total Model (kg) / (kN)
    tmass = tmass_elems + tmass_conc
    tweight = tmass * 9.81/1000
    summary = dict({'Total Number of Elements' : telems,
                    'Total Length' : tlength, 'Total Element Mass (kg)' : tmass_elems,
                    'Total Concentrated Mass (kg)' : tmass_conc, 'Total Mass (kg)' : tmass,
                    'Total Weight (kN)' : tweight})

    #############################################################
    # Clean up influence
    straight_reactions = inf[0]
    inf = inf[1:]

    #############################################################
    # Bearing details  [node, x (m), offset (mm), reactions (kN),
    #                   offset (mm), reactions (kN), name, l/d ratio w/ next bearing]

    # Setup offsets and reactions values
    calc_offsets = [output[brg[0]-1][2] for brg in conc_springs]
    calc_reactions = []
    for j in range(len(inf)):
        temp = 0
        for i in range(len(inf[j])):
            temp += inf[j][i] * calc_offsets[i]
        calc_reactions.append(straight_reactions[j] - temp)

    # Bearing Names
    if len(settings['brg_names']) != len(conc_springs):
        print("NOTE: Bearing names in shaftkit-parser.ini does not match number of bearings in model, using 'N/A'.")
        settings['brg_names'] = ["N/A" for x in conc_springs]
    
    # Write to bearing data object
    brgs = []
    for i in range(len(conc_springs)):
        node = conc_springs[i][0] - 1

        # Calculate bearing spacing
        if i < len(conc_springs) - 1:
            node2 = conc_springs[i+1][0] - 1
        
            brg1 = nodes[node][1]
            brg2 = nodes[node2][1]
            span = brg2 - brg1

            # Calculate average diameter of span
            total = 0
            for j in range(node, node2):
                total += model[j][6] * model[j][1]**2
                print(j)
            print(total)
            ratio = sqrt(total / span)
        else:
            ratio = ""

        brgs.append([conc_springs[i][0], nodes[node][1],
                     straight_reactions[i], calc_offsets[i], calc_reactions[i],
                     settings['brg_names'][i].strip(), ratio])

    return model, output, brgs, inf, summary

def output_csv(filename, model, output, brgs, inf, summary):
    # Output all data to CSV

    # Will crash if csv file open in excel, so check first
    try:
        csvfile = open(filename, "w", newline="")
        f = writer(csvfile)

        f.writerow(['Shaftkit SHAFT.OUT parser'])
        f.writerow([time.strftime("%Y-%m-%d %H:%M")])

        ##############################################
        # write summary values
        f.writerow(['Model Summary'])
        for row in summary.items():
            f.writerow(row)

        f.writerow('')
        f.writerow('')

        ##############################################
        # write influence
        f.writerow(['Bearing Influence (kN/mm'])
        for row in inf:
            f.writerow(row)

        f.writerow('')
        f.writerow('')

        #################################################
        # write model
        f.writerow(['Model'])
        f.writerow(['Element' , 'OD (m)', 'ID (m)', 'E (MPa)', 'G (MPa)',
                    'Density (kg/m^3)', 'Length (m)', 'Mass (kg)', 'Sec. Modulus (m^3)',
                    'Mom. Inertia (m^4)', 'Left x (m)', 'Right x (m)'])
        x = 0
        for i, elem in enumerate(model):
            # Add left and right x coordinate to table
            elem.append(output[i][1])
            elem.append(output[i+1][1])
            f.writerow(elem)

        f.writerow('')
        f.writerow('')

        ##############################################
        # write output at nodes
        f.writerow(['Output'])
        f.writerow(['Node', 'x (m)', 'Disp (mm)', 'Slope (mrad)',
                    'Shear (kN) Right End', 'Bending Moment (kNm) Left End', 'Bending Stress (MPa)'])
        for node in output:
            f.writerow(node)

        f.writerow('')
        f.writerow('')

        ##############################################
        # write bearings
        f.writerow(['Bearings'])
        f.writerow(['Node' , 'x (m)', 'Straight Reactions (kN)',
                    'Calc Offsets (mm)', 'Calc Reactions (kN)', 'Name', 'L/D'])
        for brg in brgs:
            f.writerow(brg)

        f.writerow('')
        f.writerow('')

        ##############################################
        csvfile.close()
    except PermissionError:
        print('Permission Error: Close output .csv file (excel maybe) before running')
        
def create_output_plots(fileprefix, output, brgs):
    # Transpose lists for plotting
    data = list(zip(*output))
    brgs_zip = list(zip(*brgs))
    
    # Axis lables
    labels = ['Deflection (mm)', 'Slope (mrad)', 'Shear Force (kN)', 'Bending Moment (kNm)', 'Bending Stress (MPa)']
    files = ['defl', 'slope', 'shear', 'moment', 'stress']

    # Bearing offsets for deflection plot
    offsets = brgs_zip[3]

    #############################################
    # Plot each
    for j in range(len(labels)):
        
        # display settings for plot
        plt.rcParams['figure.figsize'] = [12, 5]
        plt.rcParams['figure.autolayout'] = True

        # Increase x-axis limits by 2% at each end to prevent cropping        
        length = output[-1][1]
        plt.xlim(0-length*0.02, output[-1][1]*1.02)
        plt.xlabel('Position (m)')

        
        if files[j] == 'shear' or files[j] == 'moment' :   
            # Plot points
            plt.plot(data[1], data[2+j], 'o-', color='black')

        else:
            # Smooth out curve
            list_x_new = linspace(min(data[1]), max(data[1]), 1000)
            list_y_smooth = interp1d(data[1], data[2+j], kind='cubic')

            # Plot points
            plt.plot(data[1], data[2+j], 'o', color='black')        

            # Plot smooth curve
            plt.plot(list_x_new, list_y_smooth(list_x_new), '-' , color='black')

        #####################################################        
        # Plot bearings
        plt.plot(brgs_zip[1], offsets, '^', markersize = 15, color='red')
        plt.ylabel(labels[j])

        # Add bearing names


        ######################################################
        # Y axis lable, make larger??
        #fig.text(0.06, 0.5, 'Relative Displacement', ha='center', va='center', rotation='vertical')

        plt.grid()

        # save plot
        # old file was not being overwritten without os.remove
        strFile = fileprefix + files[j] + '.png'
        if os.path.isfile(strFile):
            os.remove(strFile)
        plt.savefig(strFile)

        # clear all plot settings
        plt.close('all')

        # show bearings at zero after 1st plot (deflection)
        offsets = [0 for x in brgs_zip[4]]
# add bearing names

def create_model_plot(filename, model, output, brgs):
    # Plot model to image file

    plt.rcParams['figure.figsize'] = [10, 4]
    plt.rcParams['figure.autolayout'] = True
    fig, ax = plt.subplots()
    elements = []
    y_max = 0

    ##########################################################
    # Plot element properties
    for i in range(len(model)):

        # Set corners of each element
        left = output[i][1]
        right = output[i+1][1]
        top = model[i][1] / 2
        bottom = -top

        # save max diameter
        if top > y_max: y_max = top

        # Shape to plot
        rect = [[left, top],
                [left, bottom],
                [right, bottom],
                [right, top],
                [left, top]]

        # Add as polygon
        polygon = Polygon(xy=rect, closed=True)
        elements.append(polygon)

    # Assign elements to be plot and colors
    p = PatchCollection(elements, cmap=cm.jet, alpha=0.4)
    p.set_edgecolor('black')
    p.set_facecolor(None)

    ##############################################################
    # Plot node properties
    # for z in range(0, len(model)):
    #     #############################################


    #     ##############################################
    #     # Make list of concentrated masses
    #     if shaft.nodes[z].concMass != 0:

    #         # TODO need next named element
    #         # As long as not the last element, get larger of ODs
    #         if z != len(shaft.elems) - 1:
    #             y = max(shaft.elems[z].massOD, shaft.elems[z + 1].massOD) / 2

    #         else:
    #             y = shaft.elems[z].massOD

    #         # Assign concentrated masses to plot
    #         ax.annotate(round(shaft.nodes[z].concMass),
    #                     xy=(shaft.nodes[z].x, y),
    #                     xycoords='data',
    #                     xytext=(shaft.nodes[z].x, y * 2),
    #                     arrowprops=dict(facecolor='black', shrink=0.05),
    #                     horizontalalignment='center', verticalalignment='top')

    # # Assign first & last node concentrated mass to plot
    # if shaft.nodes[0].concMass != 0:
    #     ax.annotate(round(shaft.nodes[0].concMass),
    #                 xy=(shaft.nodes[0].x, shaft.elems[0].massOD / 2),
    #                 xycoords='data',
    #                 xytext=(shaft.nodes[0].x, shaft.elems[0].massOD * 1.25),
    #                 arrowprops=dict(facecolor='black', shrink=0.05),
    #                 horizontalalignment='center', verticalalignment='top')

    # if shaft.nodes[z + 1].concMass != 0:
    #     ax.annotate(round(shaft.nodes[z + 1].concMass),
    #                 xy=(shaft.nodes[z + 1].x, shaft.elems[z].massOD / 2),
    #                 xycoords='data',
    #                 xytext=(shaft.nodes[z + 1].x, shaft.elems[z].massOD * 1.25),
    #                 arrowprops=dict(facecolor='black', shrink=0.05),
    #                 horizontalalignment='center', verticalalignment='top')

    ##############################################################
    # x-axis settings
    plt.xlim(0 - model[-1][1] * 1.05, output[-1][1] * 1.05)
    plt.xlabel('Location (m)')

    # y-axis settings
    y_max = 1.5 * y_max
    plt.ylim(-y_max, y_max)
    plt.ylabel('Diameter (m)')

    #############################################################
    # Assign bearings to plot
    brg_x = [brg[1] for brg in brgs] 
    brg_y = [-model[brg[0]-1][1] for brg in brgs]
    ax.plot(brg_x, brg_y, '^', markersize=10, color='red')

    # # Add bearing naming
    # brg_names = [brg[5] for brg in brgs]
    # for i, brg in enumerate(brgs):
    #     # vertical plotting position
    #     txt = ax.annotate(brg[5],  xy=(brg_x[i], y_max * -0.75), ha='center', size=10, color='gray', wrap=True)
    #     txt._get_wrap_line_width = lambda : 50.

    ax.add_collection(p)

    ###########################################################
    # save plot
    # old file was not being overwritten without os.remove
    if os.path.isfile(filename):
        os.remove(filename)
    plt.savefig(filename)

    # clear all plot settings
    plt.close('all')
# Scale plot based on model width and max OD
# show ID
# Scale marker size based on # of elements
# arrows for concentrated mass
# plot title cut off
# arrows for concentrated masses?
# add bearing names?

if __name__ == "__main__":
    # read in config file
    filename = 'parser-settings.ini'
    brg_names = read_config(filename)

    # read in SHAFT.OUT and config file
    if settings['shaft_out_location'] == '':
        filename = 'SHAFT.OUT'
    else:
        filename = settings['shaft_out_location']
    model, output, brgs, inf, summary= read_data(filename)

    # output to csv
    filename = 'parser-output.csv'
    output_csv(filename, model, output, brgs, inf, summary)

    # create plots
    fileprefix = 'parser-output-'
    create_output_plots(fileprefix, output, brgs)

    # create model graphic
    filename = 'parser-model.png'
    create_model_plot(filename, model, output, brgs)

    print('Finished')
    time.sleep(2.5)




# Unused code
# def format_values(item):
#     # Format numbers to 3 decimal places
    
#     str_new = []
#     for row in item:
#         new_row = []
#         for val in row:
#             try:
#                 new_row.append("{0:.3f}".format(val))
#             except ValueError:
#                 pass
#         str_new.append(new_row)

#     return str_new


    # # Format numbers to 3 decimal places
    # str_model = format_values(model)
    # str_output = format_values(output)
    # str_inf = format_values(inf)
    # str_brgs = format_values(brgs)
