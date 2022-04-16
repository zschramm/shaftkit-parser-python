# Parser for Shaftkit MSA SHAFT.OUT file
# Zac Schramm
# April 2022
# Use compile.py script to create exectuable
# Run this (and compiled exe) from same directory as SHAFT.OUT

import os
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
    config = configparser.ConfigParser()

    # check if file exists already
    if os.path.isfile(filename):
        # Read in config file
        config.read(filename)
        settings['brg_names'] = config['settings']['brg_names'].split(',')

    else:
        # create default file
        settings['brg_names'] = 'aft sterntube, fwd. sterntube, aft gear, fwd. gear'
        config['settings'] = {'brg_names' : settings['brg_names']}
        with open(filename, 'w') as config_file:
            config.write(config_file)
            print(f'Created default {filename} file')
        pass
# add gauge nodes?  then tabulate Shear & BM at gauge locations

def linspace(a, b, n=100):
    # Generate points along range (instead of importing numpy library)
    if n < 2:
        return b
    diff = (float(b) - a)/(n - 1)
    return [diff * i + a  for i in range(n)]

def read_data():
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
    with open('SHAFT.OUT', "r") as file:
        data = [x.replace('\0', '') for x in file]
        csvreader = reader(data, delimiter='\t')
        for row in csvreader:
    
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

            # if exception, continue
            except:
                pass

    ############################################################

    # Assemble model [element num, OD (m), ID (m), E (MPa), G (MPa), rho(kg/m^3), length (m), mass (kg), section modulus (m^3)]
    model = elements.copy()
    for i in range(len(elements)):
            length = nodes[i+1][1] - nodes[i][1]
            mass = (elements[i][0]**2 - elements[i][1]**2) * pi / 4 * elements[i][4] * length
            secmod = pi / 64 * (elements[i][0]**4 - elements[i][1]**4) / (elements[i][0] / 2)
            model[i] = [i+1, *model[i], length, mass, secmod]

    # for v in zip(model):
    #     print (v)

    ############################################################
    # Assemble output [node num, x (m), disp (mm), slope (mrad), shear (kN), bm (kNm), bs (MPa)]
    # all values left side of element except last value
    output = []
    bs =  beam_forces[0][2] / 1000 / model[0][8] / 1000
    output.append([nodes[0][0], nodes[0][1], disps[0][1]*1000, disps[0][2]*1000,
                   beam_forces[0][2]/1000, beam_forces[0][3]/1000, bs])
    for i in range(1, len(nodes)):
        bs =  -beam_forces[2*i-1][2] / 1000 / model[i-1][8] / 1000
        output.append([nodes[i][0], nodes[i][1], disps[i][1]*1000,
                       disps[i][2]*1000, -beam_forces[2*i-1][2]/1000,
                       beam_forces[2*i-1][3]/1000,  bs])

    #############################################################
    # Tabulate Sums
    # Sum of Element Masses
    tmass_elems = 0
    for elem in model:
        tmass_elems += elem[7]
    
    # Sum of Concentrated Masses
    tmass_conc = 0
    for mass in conc_masses:
        tmass_conc += mass[2]
    
    # Sum of Total Model
    tmass = tmass_elems + tmass_conc

    #############################################################
    # Clean up influence
    straight_reactions = inf[0]
    inf = inf[1:]

    #############################################################
    # Bearing details  [node, x (m), stiffness (N/m), offset (mm), reactions (kN), offset (mm), reactions (kN), name]
    calc_offsets = [output[brg[0]-1][2] for brg in conc_springs]
    calc_reactions = []
    for j in range(len(inf)):
        temp = 0
        for i in range(len(inf[j])):
            temp += inf[j][i] * calc_offsets[i]
        calc_reactions.append(straight_reactions[j] - temp)

    if len(settings['brg_names']) < len(conc_springs):
        print("ERROR: Bearing names in shaftkit-parser.ini file is too short.")
        settings['brg_names'] = ["ERROR" for x in conc_springs]
    
    brgs = []
    for i in range(len(conc_springs)):
        brgs.append([conc_springs[i][0], nodes[conc_springs[i][0]-1][1], conc_springs[i][2],
                     straight_reactions[i], calc_offsets[i], calc_reactions[i],
                     settings['brg_names'][i].strip() ])

    # print(brgs)

    return model, output, brgs, inf

def output_csv(filename, model, output, brgs, inf):
    # Output all data to CSV

    csvfile = open(filename, "w", newline="")
    f = writer(csvfile)

    ##############################################
    # write model
    f.writerow(['Model'])
    f.writerow(['Element' , 'OD (m)', 'ID (m)', 'E (MPa)', 'G (MPa)',
                'rho(kg/m^3)', 'length (m)', 'mass (kg)', 'section modulus (m^3)'])
    for elem in model:
        f.writerow(elem)

    f.writerow('')
    f.writerow('')

    ##############################################
    # write output at nodes
    f.writerow(['Output'])
    f.writerow(['Node', 'x (m)', 'disp (mm)', 'slope (mrad)',
                'shear (kN)', 'Bending Moment (kNm)', 'Bending Stress (MPa)'])
    for node in output:
        f.writerow(node)

    f.writerow('')
    f.writerow('')

    ##############################################
    # write bearings
    f.writerow(['Bearings'])
    f.writerow(['Node' , 'x (m)', 'Stiffness (N/m)', 'Straight Reactions (kN)',
                'Calc Offsets (mm)', 'Calc Reactions (kN)', 'Name'])
    for brg in brgs:
        f.writerow(brg)

    f.writerow('')
    f.writerow('')

    ##############################################
    # write influence
    f.writerow(['Bearing Influence (kN/mm'])
    for i in range(len(inf)):
        f.writerow(inf[i])

    f.writerow('')
    f.writerow('')

    ##############################################
    csvfile.close()
# Add mass summary
# add bending stress

def create_output_plots(fileprefix, output, brgs):
    # Plots of beam output

    # Transpose lists for plotting
    data = list(zip(*output))
    brgs_zip = list(zip(*brgs))
    
    # Axis lables
    labels = ['Deflection (mm)', 'Slope (mrad)', 'Shear Force (kN)', 'Bending Moment (kNm)'] #, 'Bending Stress (MPa)']
    files = ['defl', 'slope', 'shear', 'moment'] #, 'shear']

    #############################################
    # display settings for plot
    offsets = brgs_zip[4]
    for j in range(len(labels)):
        plt.rcParams['figure.figsize'] = [12, 5]
        plt.xlim(0, output[-1][1])
        plt.xlabel('Position (m)')

        # Smooth out curve
        list_x_new = linspace(min(data[1]), max(data[1]), 1000)
        list_y_smooth = interp1d(data[1], data[2+j], kind='cubic')
        
        # Plot displacement points
        plt.plot(data[1], data[2+j], 'o', color='black')
    
        # Plot smooth curve
        plt.plot(list_x_new, list_y_smooth(list_x_new), '-' , color='black')
        
        # Plot bearings
        plt.plot(brgs_zip[1], offsets, '^', markersize = 15, color='red')
        plt.ylabel(labels[j])

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
# add bending stress
# don't smooth shear plot?
# add bearing names

def create_model_plot(filename, model, output, brgs):
    # Plot model to image file

    # TODO


    plt.rcParams['figure.figsize'] = [10, 3]
    fig, ax = plt.subplots()
    elements = []

    ##########################################################
    # Plot element properties
    for i in range(len(model)):

        # Set corners of each element
        left = output[i][1]
        right = output[i+1][1]
        top = model[i][1] / 2
        bottom = -top

        # Shape to plot
        rect = [[left, top],
                [left, bottom],
                [right, bottom],
                [right, top],
                [left, top]]

        # Add as polygon
        polygon = Polygon(rect, True)
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

    # Assign bearings to plot
    brg_x = [brg[1] for brg in brgs] 
    brg_y = [-model[brg[0]-1][1]/2 for brg in brgs]
    ax.plot(brg_x, brg_y, '^', markersize=30, color='red')

    ##############################################################
    # x-axis settings
    plt.xlim(0 - model[-1][1] * 1.05, output[-1][1] * 1.05)
    plt.xlabel('Location (m)')

    # TODO make this dynamic
    # y-axis settings
    plt.ylim(-0.5, 0.5)

    ax.add_collection(p)

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

if __name__ == "__main__":
    # read in config file
    filename = 'parser-settings.ini'
    brg_names = read_config(filename)

    # read in SHAFT.OUT and config file
    model, output, brgs, inf = read_data()

    # output to csv
    filename = 'parser-output.csv'
    output_csv(filename, model, output, brgs, inf)

    # create plots
    fileprefix = 'parser-output-'
    create_output_plots(fileprefix, output, brgs)

    # create model graphic
    filename = 'parser-model.png'
    create_model_plot(filename, model, output, brgs)





