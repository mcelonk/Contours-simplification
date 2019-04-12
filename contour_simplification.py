import arcpy, sys, os, copy
from arcpy.sa import *
arcpy.env.overwriteOutput = 1
#Check the Spatial extension
arcpy.CheckOutExtension("Spatial")
#Check number of parameters
if len(sys.argv) < 4:
    print "ERROR: not enough input arguments"
    exit(-1)

#Set inputs/outputs nad workspace
input = sys.argv[1]
output = sys.argv[2]
contour = sys.argv[3]
arcpy.env.workspace = os.getcwd()

#Selection how will filter calculate
"""""
If you choose 0 filter will calculate only if kernel matrix does not contain null
If you choose 1 filter will calculate if at least one value in kenel matrix is not null
"""""
error = True
while error:
    na = raw_input('Choose 0 for ignore null values or choose 1 for usage of null values: ')
    try:
        na = int(na)
        if (na == 1) or (na == 0):
            error = False
        else:
            print ("Wrong parameter!")
    except ValueError:
        print("Invalid input!")

error = True

# Input for interval between contours in meters
while error:
    nc = raw_input('Choose a positive contour interval in integer: ')
    try:
        interval = int(nc)
        error = False
        if interval <= 0:
            error = True
            print ("Negative number or zero, repeat input!")
    except ValueError:
        print("Invalid number, repeat input!")

#Reclassification of high values
"""""
This step will change all TPI values higher then chosen number. Ideal numbers are between 0 and 3. If 0 is used the
result will be only Gauss filter 5x5. User can try higher number but if is chosen number equal or higher than Maximum 
of TPI, reclassification will not be done and will be used unchanged TPI raster.
Higher number will change values too much for example create negative values
or create "pyramids" around high values and those values are several times larger than input values. 
"""""
error = True
while error:
    nb = raw_input('Choose a number for reclassification: ')
    try:
        number = float(nb)
        error = False
        if interval < 0:
            error = True
            print ("Negative number, repeat input!")
    except ValueError:
        print("Invalid number, repeat input!")

#Delete existing output
if arcpy.Exists(output):
    arcpy.Delete_management(output)


#Change input to raster, Set coordination system, get null values
raster = arcpy.Raster(input)
dsc = arcpy.Describe(raster)
coord_sys = dsc.spatialReference
no_data = raster.noDataValue
#Find min coordination of the raster
mx = raster.extent.XMin
my = raster.extent.YMin


#Create matrix from raster values
array = arcpy.RasterToNumPyArray(raster)

#Gaussian filter 3x3 kernel
print "Calculating Gauss filter 3x3"
gauss_small_array = array.astype(float)
gauss_small_array[:, :] = float(-9999)
if na == 1:
    n = [0 for i in range(8)]
    for i in range(1, len(array[:, 1])-1):
        for j in range(1, len(array[1, :])-1):
            x = array[i, j]
            value = 0
            count = 0
            n[0] = array[i - 1, j - 1]
            n[1] = array[i - 1, j]
            n[2] = array[i - 1, j + 1]
            n[3] = array[i, j - 1]
            n[4] = array[i, j + 1]
            n[5] = array[i + 1, j - 1]
            n[6] = array[i + 1, j]
            n[7] = array[i + 1, j + 1]
            for k in range(0, 8, 1):
                if n[k] != no_data:
                    if (k == 1) or (k == 3) or (k == 4) or (k == 6):
                        count +=1
                        value += n[k]
                    count += 1
                    value += n[k]
            if x != no_data:
                count +=4
                value += 4*x
            if count > 0:
                c = float(value)/float(count)
                gauss_small_array[i, j] = c


else:
    n = [0 for i in range(8)]
    for i in range(1, len(array[:, 1]) - 1):
        for j in range(1, len(array[1, :]) - 1):
            value = 0
            x = array[i, j]
            if x == no_data:
                continue
            else:
                value += 4*x
            n[0] = array[i - 1, j - 1]
            if n[0] == no_data:
                continue
            else:
                value += n[0]
            n[1] = array[i - 1, j]
            if n[1] == no_data:
                continue
            else:
                value += 2*n[1]
            n[2] = array[i - 1, j + 1]
            if n[2] == no_data:
                continue
            else:
                value += n[2]
            n[3] = array[i, j - 1]
            if n[3] == no_data:
                continue
            else:
                value += 2*n[3]
            n[4] = array[i, j + 1]
            if n[4] == no_data:
                continue
            else:
                value += 2*n[4]
            n[5] = array[i + 1, j - 1]
            if n[5] == no_data:
                continue
            else:
                value += n[5]
            n[6] = array[i + 1, j]
            if n[6] == no_data:
                continue
            else:
                value += 2*n[6]
            n[7] = array[i + 1, j + 1]
            if n[7] == no_data:
                continue
            else:
                value += n[7]

            c = float(value) / 16
            gauss_small_array[i, j] = c

#Convert array to Gauss filter 3x3
raster_gaus_small = arcpy.NumPyArrayToRaster(gauss_small_array, arcpy.Point(mx,my),raster.meanCellWidth,raster.meanCellHeight)
raster_gaus_small = SetNull(raster_gaus_small, raster_gaus_small, "VALUE = -9999")
arcpy.DefineProjection_management(raster_gaus_small, coord_sys)

#Gaussian filter 5x5 kernel
print "Calculating Gauss filter 5x5"
gauss_big_array = array.astype(float)
gauss_big_array[:, :] = float(-9999)

if na == 1:
    n = [0 for i in range(24)]
    for i in range(1, len(array[:, 1])-2): #tady muze byt chyba nebo to muze byt nekde pri definici pole
        for j in range(1, len(array[1, :])-2): #tim padem asi i tady
            x = array[i, j]
            value = 0
            count = 0
            n[0] = array[i - 1, j - 1]
            n[1] = array[i - 1, j]
            n[2] = array[i - 1, j + 1]
            n[3] = array[i, j - 1]
            n[4] = array[i, j + 1]
            n[5] = array[i + 1, j - 1]
            n[6] = array[i + 1, j]
            n[7] = array[i + 1, j + 1]
            n[8] = array[i - 2, j - 2]
            n[9] = array[i - 2, j - 1]
            n[10] = array[i - 2, j]
            n[11] = array[i - 2, j + 1]
            n[12] = array[i - 2, j + 2]
            n[13] = array[i - 1, j - 2]
            n[14] = array[i - 1, j + 2]
            n[15] = array[i, j - 2]
            n[16] = array[i, j + 2]
            n[17] = array[i + 1, j - 2]
            n[18] = array[i + 1, j + 2]
            n[19] = array[i + 2, j - 2]
            n[20] = array[i + 2, j + 1]
            n[21] = array[i + 2, j]
            n[22] = array[i + 2, j + 1]
            n[23] = array[i + 2, j + 2]

            for k in range(0, 24, 1):
                if n[k] != no_data:
                    if (k == 0) or (k == 2) or (k == 5) or (k == 7):
                        count += 15
                        value += 15*n[k]
                    if (k == 1) or (k == 3) or (k == 4) or (k == 6):
                        count += 23
                        value += 23*n[k]
                    if (k == 10) or (k == 15) or (k == 16) or (k == 21):
                        count += 5
                        value += 5*n[k]
                    if (k == 9) or (k == 11) or (k == 13) or (k == 14) or (k == 17) or (k == 18) or (k == 20) or (k == 22):
                        count += 3
                        value += 3*n[k]
                    count += 1
                    value += n[k]
            if x != no_data:
                count += 36
                value += 36*x
            if count > 0:
                c = float(value)/float(count)
                gauss_big_array[i, j] = c


else:
    n = [0 for i in range(24)]
    for i in range(1, len(array[:, 1]) - 2):
        for j in range(1, len(array[1, :]) - 2):
            value = 0
            x = array[i, j]
            if x == no_data:
                continue
            else:
                value += 36*x

            n[0] = array[i - 1, j - 1]
            if n[0] == no_data:
                continue
            else:
                value += 16 * n[0]
            n[1] = array[i - 1, j]
            if n[1] == no_data:
                continue
            else:
                value += 24 * n[1]
            n[2] = array[i - 1, j + 1]
            if n[2] == no_data:
                continue
            else:
                value += 16 * n[2]
            n[3] = array[i, j - 1]
            if n[3] == no_data:
                continue
            else:
                value += 24 * n[3]
            n[4] = array[i, j + 1]
            if n[4] == no_data:
                continue
            else:
                value += 24 * n[4]
            n[5] = array[i + 1, j - 1]
            if [5] == no_data:
                continue
            else:
                value += 16 * n[5]
            n[6] = array[i + 1, j]
            if n[6] == no_data:
                continue
            else:
                value += 24 * n[6]
            n[7] = array[i + 1, j + 1]
            if n[7] == no_data:
                continue
            else:
                value += 16 * n[7]

            n[8] = array[i - 2, j - 2]
            if n[8] == no_data:
                continue
            else:
                value += n[8]
            n[9] = array[i - 2, j - 1]
            if n[9] == no_data:
                continue
            else:
                value += 4 * n[9]
            n[10] = array[i - 2, j]
            if n[10] == no_data:
                continue
            else:
                value += 6 * n[10]
            n[11] = array[i - 2, j + 1]
            if n[11] == no_data:
                continue
            else:
                value += 4 * n[11]
            n[12] = array[i - 2, j + 2]
            if n[12] == no_data:
                continue
            else:
                value += n[12]
            n[13] = array[i - 1, j - 2]
            if n[13] == no_data:
                continue
            else:
                value += 4 * n[13]
            n[14] = array[i - 1, j + 2]
            if n[14] == no_data:
                continue
            else:
                value += 4 * n[14]
            n[15] = array[i, j - 2]
            if n[15] == no_data:
                continue
            else:
                value += 6 * n[15]
            n[16] = array[i, j + 2]
            if n[16] == no_data:
                continue
            else:
                value += 6 * n[16]
            n[17] = array[i + 1, j - 2]
            if n[17] == no_data:
                continue
            else:
                value += 4 * n[17]
            n[18] = array[i + 1, j + 2]
            if n[18] == no_data:
                continue
            else:
                value += 4 * n[18]
            n[19] = array[i + 2, j - 2]
            if n[19] == no_data:
                continue
            else:
                value += n[19]
            n[20] = array[i + 2, j + 1]
            if n[20] == no_data:
                continue
            else:
                value += 4 * n[20]
            n[21] = array[i + 2, j]
            if n[21] == no_data:
                continue
            else:
                value += 6 * n[21]
            n[22] = array[i + 2, j + 1]
            if n[22] == no_data:
                continue
            else:
                value += 4 * n[22]
            n[23] = array[i + 2, j + 2]
            if n[23] == no_data:
                continue
            else:
                value += n[23]

            c = float(value) / 256
            gauss_big_array[i, j] = c

#Convert array to Gauss filter raster 5x5
raster_gaus_big = arcpy.NumPyArrayToRaster(gauss_big_array, arcpy.Point(mx,my),raster.meanCellWidth,raster.meanCellHeight)
raster_gaus_big = SetNull(raster_gaus_big, raster_gaus_big, "VALUE = -9999")
arcpy.DefineProjection_management(raster_gaus_big, coord_sys)


#Create TPI raster
print "Calculating TPI values"
copy_array = array.astype(float)
copy_array[:, :] = float(-9999)

n = [0 for i in range(8)]
c_max = 0

for i in range(1, len(array[:, 1])-1):
    for j in range(1, len(array[1, :])-1):
        x = array[i, j]
        value = 0
        count = 0
        if x != no_data:
            n[0] = array[i - 1, j - 1]
            n[1] = array[i - 1, j]
            n[2] = array[i - 1, j + 1]
            n[3] = array[i, j - 1]
            n[4] = array[i, j + 1]
            n[5] = array[i + 1, j - 1]
            n[6] = array[i + 1, j]
            n[7] = array[i + 1, j + 1]
            for k in range(0, 8, 1):
                if n[k] != no_data:
                    count += 1
                    value += n[k]
            if count > 0:
                c = abs(float(x)-float(value)/float(count))
                c_max = max(c_max,c)
                copy_array[i, j] = c

#Reclassification of TPI by choosen number at the start of the script
print "Reclasification of TPI values"
if number < c_max:
    for i in range(1, len(copy_array[:, 1])-1):
        for j in range(1, len(copy_array[1, :])-1):
            x = copy_array[i, j]
            x = min(x,number)
            copy_array[i, j] = x

#Convert array to reclassified TPI raster
TPI = arcpy.NumPyArrayToRaster(copy_array, arcpy.Point(mx,my),raster.meanCellWidth,raster.meanCellHeight)
TPI = SetNull(TPI, TPI, "VALUE = -9999")
arcpy.DefineProjection_management(TPI, coord_sys)

#Calculation of final raster
result = TPI * raster_gaus_small + (1 - TPI) * raster_gaus_big
arcpy.DefineProjection_management(result, coord_sys)

#Exporting result raster
arcpy.CopyRaster_management(result, output)

#Creation of contours
arcpy.Contour_3d(result, contour, interval, 0)

print "Done!"