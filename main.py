import math
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import mcschematic


#creaking is for its own eye lvl, bottom for where you want the points to be (above/below)
def create_points(angles, shift_x=0, shift_y=0, creaking=0, bottom=1):
    all_points = []
    for angle in angles:
        angle = angle + CREAKING_FOV/180*math.pi*bottom # + normal - for bottom
        
        if angle > 2*math.pi:
            angle -= 2*math.pi

        if angle < 0:
            angle += 2*math.pi

        if handle_axes(angle):
            continue

        possible_points = []
        list_points_in_range = []
        y_slope = math.tan(angle)

        for radius in range(int((shift_x + 1)//1), math.ceil(MAX_RADIUS + shift_x)):         
            possible_points.append((radius - shift_x, math.floor((radius - shift_x)*y_slope + shift_y - creaking) - shift_y + creaking))
            possible_points.append((radius - shift_x, math.ceil((radius - shift_x)*y_slope + shift_y - creaking) - shift_y + creaking))
        
        for x, y in possible_points:
            x, y = fix_signs(x, y, angle)
            points_in_range(x, y, angle, list_points_in_range)

        # fallback
        if list_points_in_range == []:
            for radius in range(MAX_RADIUS):
                possible_points.append(((shift_x + 1)//1 - shift_x, radius - shift_y + creaking))
                possible_points.append((shift_x//1 - shift_x, radius - shift_y + creaking))

        for x, y in possible_points:
            x, y = fix_signs(x, y, angle)
            points_in_range(x, y, angle, list_points_in_range)     

        if list_points_in_range == []:
            print("error")

        x, y, angle_error = best_angle(list_points_in_range)
        all_points.append((int(round(x + shift_x)), int(round(y + shift_y - creaking))))

        for x, y in possible_points:
            x, y = fix_signs(x, y, angle)
            points_in_range(x, y, angle, list_points_in_range)

    print(all_points)
    return all_points


def handle_axes(angle, err=1e-09):
    if math.isclose(angle, 0, rel_tol=err):
        all_points.append((AVR_RADIUS, 0))
    elif math.isclose(angle, 0.5*math.pi, rel_tol=err):
        all_points.append((0, AVR_RADIUS))
    elif math.isclose(angle, math.pi, rel_tol=err):
        all_points.append((-AVR_RADIUS, 0))
    elif math.isclose(angle, 1.5*math.pi, rel_tol=err):
        all_points.append((0, -AVR_RADIUS))
    else:
        return False
    return True


def fix_signs(x, y, angle):
    x, y = abs(x), abs(y)

    if 0.5*math.pi < angle < math.pi:
        x, y = -x, y
    elif math.pi < angle < 1.5*math.pi:
        x, y = -x, -y
    elif 1.5*math.pi < angle:
        x, y = x, -y

    return x, y


def euc_dist(x, y):
    return (x**2 + y**2)**(1/2)


def points_in_range(x, y, angle, list_points_in_range):
    if MIN_RADIUS <= euc_dist(x, y) <= MAX_RADIUS:
        lowered_angle = angle
        if angle >= math.pi:
            lowered_angle = 2*math.pi - angle
        list_points_in_range.append((x, y, abs(abs(math.atan2(y, x)) - lowered_angle)))


def best_angle(list_points_in_range):
    min_index = min(enumerate(list_points_in_range), key=lambda x: x[1][2])[0]
    angle_error = list_points_in_range[min_index][2]
    best_angle = (0, 0, math.inf)

    for angle_number in range(len(list_points_in_range)):
        if math.isclose(list_points_in_range[angle_number][2], angle_error):
            x, y, angle_error = list_points_in_range[angle_number]
            if abs(euc_dist(x, y) - AVR_RADIUS) < abs(euc_dist(best_angle[0], best_angle[1]) - AVR_RADIUS):
                best_angle = x, y, angle_error

    return best_angle


def display(all_points):
    img = np.zeros((2*MAX_RADIUS + 1, 2*MAX_RADIUS + 1))
    for point in all_points:
        x, z = point
        img[-z + MAX_RADIUS, x + MAX_RADIUS] = 1
    
    img[MAX_RADIUS, MAX_RADIUS] = 1

    if not center:
        img[MAX_RADIUS+1, MAX_RADIUS] = 1
        img[MAX_RADIUS, MAX_RADIUS+1] = 1
        img[MAX_RADIUS+1, MAX_RADIUS+1] = 1

    plt.imshow(img, cmap='viridis', interpolation='none')

    tick_range = np.arange(-MAX_RADIUS, MAX_RADIUS + 1)

    plt.xticks(tick_range + MAX_RADIUS, tick_range)
    plt.yticks(tick_range + MAX_RADIUS, -tick_range)

    plt.gca().set_xticks(np.arange(-0.5, 2*MAX_RADIUS), minor=True)
    plt.gca().set_yticks(np.arange(-0.5, 2*MAX_RADIUS), minor=True)
    plt.grid(which='minor', color='white', linestyle='-', linewidth=0.5)
    plt.gca().set_aspect('equal')
    plt.show()


def place_blocks(horizontal=True):
    schematic.setBlock((0, 0, 0), "minecraft:lime_stained_glass")

    if not center:
        schematic.setBlock((1, 0, 0), "minecraft:lime_stained_glass")
        schematic.setBlock((0, 0, 1), "minecraft:lime_stained_glass")
        schematic.setBlock((1, 0, 1), "minecraft:lime_stained_glass")

    if horizontal:
        for x, y in all_points: # placeholder
            for value in [[0, -1, 0], [1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1], [1, 1, 0], [-1, 1, 0], [0, 1, 1], [0, 1, -1]]:
                i, j, k = value
                schematic.setBlock((x + i, j, y + k), "minecraft:glass")

            schematic.setBlock((x, 0, y), "minecraft:medium_amethyst_bud[waterlogged=true]")

    else:
        for x, y in all_points: # placeholder
            for value in [[0, 0, 0], [1, 1, 0], [-1, 1, 0], [0, 1, 1], [0, 1, -1], [1, 2, 0], [-1, 2, 0], [0, 2, 1], [0, 2, -1]]:
                i, j, k = value
                schematic.setBlock((x + i, y + j, k), "minecraft:glass")

            schematic.setBlock((x, y + 1, 0), "minecraft:medium_amethyst_bud[waterlogged=true]")

 
def save_schematic():
    roaming_dir = os.path.expandvars(r'%APPDATA%')
    schematic_dir = os.path.join(roaming_dir, r".minecraft\schematics")
    file_name = 'Tracker'

    if os.path.exists(schematic_dir):
        schematic.save(schematic_dir, file_name, mcschematic.Version.JE_1_20_1)
        print(f"File saved: {os.path.join(schematic_dir, file_name)}")
    else:
        current_directory = os.path.dirname(sys.argv[0])
        schematic.save(current_directory, file_name, mcschematic.Version.JE_1_20_1)
        print(f"File saved: {os.path.join(current_directory, file_name)}]")


######################################################################
######################################################################

MIN_RADIUS = 15
MAX_RADIUS = 32 - 1
AVR_RADIUS = math.floor((MAX_RADIUS + MIN_RADIUS)/2)
PLAYER_EYE_LVL = 1.62
AVR_CREAKING_EYE_LVL = 2.3 + 4/16 + (4/16)/2 # eye lvl + medium amethyst bud + swim bonus/2 for average
CREAKING_FOV = 60 # yes this is correct, wiki says 70 but its 60 from tests and source code

resolution = (16, 16)
pixel_size = 2
screen_distance = 32 # if standing in the middle of the block its n + 0.5
center = True if math.isclose(screen_distance % 1, 0.5, abs_tol=1e-7) else False

######################################################################
######################################################################

schematic = mcschematic.MCSchematic()

# Horizontal
print(2*math.atan(pixel_size*resolution[0]/2/screen_distance)*180/math.pi)

angles = []
for i in range(0, resolution[0] - 1):
    angles.append(math.atan(pixel_size*(resolution[0]/2 - i - 1)/screen_distance))

print([angle/math.pi*180 for angle in angles])

all_points = create_points(angles, 0.5, 0.5)
display(all_points)
place_blocks(True)

# Vertical
print((math.atan((pixel_size*resolution[1]/2 - 2 + PLAYER_EYE_LVL)/screen_distance) +
       math.atan((pixel_size*resolution[1]/2 + 2 - PLAYER_EYE_LVL)/screen_distance))*180/math.pi)

angles = []
for i in range(0, resolution[1] - 1):
    angles.append(math.atan((pixel_size*(resolution[1]/2 - i - 1) - 2 + PLAYER_EYE_LVL)/screen_distance))

print([angle/math.pi*180 for angle in angles])

all_points = create_points(angles, 0.5, 0.5 + PLAYER_EYE_LVL, AVR_CREAKING_EYE_LVL, -1)
display(all_points)
place_blocks(True)


save_schematic()
