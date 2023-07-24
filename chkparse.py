import sys
import json

LOCATION_SIZE = 4 * 32 + 2 * 16

# put section header information into {"name", "offset"} dictionary
def readSectionHeader():
    global in_file
    data = in_file.read(8)                                 # treat <in_file> as a global
    section = {}
    section["name"] = data[:4].decode("utf-8")             # first 4 bytes is the name of this section
    section["offset"] = int.from_bytes(data[4:], "little") # last  4 bytes is the offset to the next section's address
    return section

# read an entire section's data
def readData(offset):
    global in_file
    return in_file.read(offset)

# take out an int from the front of global byte string <byte_data> with size in bytes <size>
# <byte_data> is updated to no longer contain the int16
def takeInt(size):
    global byte_data
    num = int.from_bytes(byte_data[:size], "little")
    byte_data = byte_data[size:]
    return num

# check for valid arguments
args = sys.argv[1:]
if (len(args) < 1):
    print("Usage: chkparse.py <file.chk>")
    print("Produces a <file.json> containing data from <file.chk>")
    sys.exit()

# open .chk file
in_file = open(args[0], "rb")
json_data = {}
section = readSectionHeader()

# check for a valid "magic number"
if (section["name"] != "VER "):
    print(".chk file is invalid")
    print("\"", section["name"], "\" received")
    print("\"VER \" expected")

# record "version"
#print(section)
byte_data = readData(section["offset"])
json_data["version"] = takeInt(2)

# seek until "MRGN" section is reached
while (True):
    section = readSectionHeader()
    #print(section)
    byte_data = readData(section["offset"])
    if (section["name"] == "MRGN"):
        break

# load location position and string array index data into <json_data>
json_data["locations"] = []
while (len(byte_data) >= LOCATION_SIZE):
    left   = takeInt(4)
    top    = takeInt(4)
    right  = takeInt(4)
    bottom = takeInt(4)
    string_array_index = takeInt(2)
    flags  = takeInt(2)
    # if a location exists, then its <string_array_index> will be nonzero (index 0 is reserved for the scenario name)
    if (string_array_index > 0):
        # build a location dictionary
        loc = {}
        loc["left"]   = left
        loc["top"]    = top
        loc["right"]  = right
        loc["bottom"] = bottom
        loc["string_array_index"] = string_array_index - 1 # indices in .chk seem to start at 1
        loc["flags"]  = hex(flags)
        # add it to the "locations" array
        json_data["locations"].append(loc)

# build the string array
section = readSectionHeader()
#print(section)
byte_data = readData(section["offset"])
i = section["offset"] - 1
strings = []
current_string_length = 0
while (byte_data[i] != 2 and byte_data[i] != 8): # 0x02 and 0x08 are filler bytes
    if (byte_data[i] == 0 and current_string_length > 0): # new string found
        # extract this string from <byte_data>
        current_string = byte_data[(i + 1):(i + current_string_length)].decode("utf-8")
        # add it to <strings>
        strings = [current_string] + strings
        current_string_length = 0
    i -= 1
    current_string_length += 1

# find location names and add them into <json_data>
for loc in json_data["locations"]:
    loc["name"] = strings[loc["string_array_index"]]

# done with <in_file>
in_file.close()

# write <data> to .json file
out_file = open(args[0].replace(".chk", ".json"), "w")
#json.dump(json_data, out_file)
out_file.write("{\n")
out_file.write("\t\"version\": " + str(json_data["version"]) + ",\n")
out_file.write("\t\"locations\": [")
for loc in json_data["locations"]:
    out_file.write("{\n")
    out_file.write("\t\t\t\"name\": \"" + loc["name"] + "\",\n")
    out_file.write("\t\t\t\"left\": " + str(loc["left"]) + ",\n")
    out_file.write("\t\t\t\"top\": " + str(loc["top"]) + ",\n")
    out_file.write("\t\t\t\"right\": " + str(loc["right"]) + ",\n")
    out_file.write("\t\t\t\"bottom\": " + str(loc["bottom"]) + ",\n")
    out_file.write("\t\t\t\"string_array_index\": " + str(loc["string_array_index"]) + "\n")
    if (loc == json_data["locations"][-1]):
        out_file.write("\t\t}]\n")
    else:
        out_file.write("\t\t}, ")
out_file.write("}\n")

# done with <out_file>
out_file.close()