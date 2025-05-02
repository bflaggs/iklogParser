######################################
# Description of file and file usage #
######################################

# Parses Auger iklog files for T3 requests containing Lety Jr. (local station 97)
# Run in the terminal via command:
# python3 ikLogParser.py <input_iklog_file_path> <output_path>

######################
# End of description #
######################

import sys

def GetT3RequestInfo(string, delimiter=None):
    """
    Groups a T3 request by the relevant info.
    Saves output as a list of strings grouped by relevance.

    Parameters
    ----------
    string : str
        T3 request info to be separated
    delimiter : str
        Character that separates the relevant T3 information.

    Returns
    -------
    seaprated : list
        List of separated T3 information. Saved as a list of strings.
    """
    separated = []
    entry = []
    inside_brace = False

    for i in range(len(string)):
        if string[i] == "{":
            inside_brace = True
            entry.append(string[i])
        elif string[i] == "}":
            inside_brace = False
            entry.append(string[i])
        elif string[i] == delimiter and inside_brace == False:
            separated.append("".join(entry))
            entry = []
        else:
            entry.append(string[i])

    if len(entry) != 0:
        separated.append("".join(entry))

    return separated

def OrganizeT3Info(t3request):
    """
    Organizes T3 request into a dictionary for easy access.

    Parameters
    ----------
    t3request : list
        List of T3 request information separated by relevance. Output of GetT3RequestInfo().

    Returns
    -------
    info : dict
        Dictionary of T3 request information. Dictionary values saved in correct data formats (str or int).
    """
    info = {}
    for string in t3request:
        if "=" in string:
            key, value = string.split("=", 1)
            value = value.strip()

            if value.startswith("{") and value.endswith("}"):
                value = value[1:-1].strip()
                value_list = value.split(" ")

                # Convert strings to ints
                value = list(map(int, value_list))

            elif value.startswith('"') and value.endswith('"'):
                value = str(value)
            else:
                # Convert to float first to fix error when value is near zero (i.e. 2.XXXe-8 or something) 
                value = int(float(value))

            info[key] = value

    return info

def GetLetyInfo(t3info, LetyID):
    """
    Saves the necessary T3 information for Lety Jr. into a list.

    Parameters
    ----------
    t3info : dict
        Dictionary of T3 request information. Output of OrganizeT3Info().
    LetyID : int
        Local station ID of Lety Jr. Should always be 97.

    Returns
    -------
    letyData : list
        List of needed information for crossmatching Lety Jr. T3 requests with SKALA events.
        gpsSec      - GPS second of T3 request
        gpsMicroSec - GPS microsecond of T3 request
        offset      - Offset in GPS microseconds of the T3 request at Lety Jr. (must add to gpsMicroSec)
        window      - Uncertainty window in GPS microseconds of the Lety Jr. T3 request (0 = Lety has T2 that participated in the trigger)
    """
    data = OrganizeT3Info(t3info)

    ind = data["addresses"].index(int(LetyID))
    offset = data["offsets"][ind]
    window = data["window"][ind]
    gpsSec = data["refSecond"]
    gpsMicroSec = data["refuSecond"]

    letyData = [gpsSec, gpsMicroSec, offset, window]

    return letyData

def ParseIkLog(inputFile, outputFilepath, LetyID=97):
    """
    Parses the daily IkLog file for T3 requests containing Lety Jr.
    Will save parsed data in a text file.

    Parameters
    ----------
    inputFile : str
        Absolute path + filename of daily IkLog file to parse.
    outputFilepath : str
        Absolute path of where to save Lety T3 request data.
    LetyID : int
        Local station ID of Lety Jr. Should always be 97.

    Returns
    -------
    LetyT3Requests_YYYY_MM_DD.txt : Text file
        Text file containing Lety Jr. T3 request info. One line contains info for one T3 request. Info is as follows...
        gpsSec      - GPS second of T3 request
        gpsMicroSec - GPS microsecond of T3 request
        offset      - Offset in GPS microseconds of the T3 request at Lety Jr. (must add to gpsMicroSec)
        window      - Uncertainty window in GPS microseconds of the Lety Jr. T3 request (0 = Lety has T2 that participated in the trigger)
    """
    # Make output file. Get date from input IkLog file.
    splt = inputFile.split("_")
    filedate = splt[1] + "_" + splt[2] + "_" + splt[3]
    
    if outputFilepath[-1] == "/":
        outFile = outputFilepath + "LetyT3Requests_" + filedate + ".txt"
    else:
        outFile = outputFilepath + "/LetyT3Requests_" + filedate + ".txt"

    fileout = open(outFile, "w")
    fileout.write("#gpsSec, gpsMicroSec, offset, window\n")
    
    # letyNum to be used for debugging purposes/T3 request rate calculations if needed
    letyNum = 0
    filein = open(inputFile, "r")
    for iline, line in enumerate(filein):
        cols = line.strip().split("|")

        # Skip data line if it is not in expected format
        if len(cols) != 6:
            continue

        # If the message is an IkT3 request (probably safer to do this then parse by column number...)
        if "IkT3" not in cols:
            continue
        else:
            trig = cols[1]
            message = cols[3]
            t3string = cols[4]

            t3info = GetT3RequestInfo(t3string, delimiter=" ")

            # Parse for Lety participation in T3, if no then skip T3 request
            address_entry = next((string for string in t3info if string.startswith("addresses=")), "")
            if address_entry == "":
                continue
            else:
                addresses = address_entry.split("=")[1].strip("{}").split(" ")
                if str(LetyID) not in addresses:
                    continue
                else:
                    letyT3 = GetLetyInfo(t3info, LetyID)
                    letyNum += 1
                    fileout.write(str(letyT3[0]) + ", " + str(letyT3[1]) + ", " + str(letyT3[2]) + ", " + str(letyT3[3]) + "\n")
    fileout.close()
    filein.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("ERROR: Usage must be --> python3 ikLogParser.py <input_file_path> <output_path>")
        sys.exit(1)

    input_file_path = sys.argv[1]
    output_path = sys.argv[2]

    # If need for a different local station in the future, change 97 to necessary LS ID
    ParseIkLog(input_file_path, output_path, LetyID=97)