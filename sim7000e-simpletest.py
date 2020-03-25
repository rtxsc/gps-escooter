from os import system
import serial
import subprocess
from time import sleep
# from ISStreamer.Streamer import Streamer

# BUCKET_NAME = "movv-project"
# BUCKET_KEY = "SMMSQAMKS9Y9"
# ACCESS_KEY = "ist_PxI02ioOp4KEOeDtd2VfPyWpDdEZ82h6"

SECONDS_BETWEEN_READS = 1
INIT_DELAY = 2
READ_COUNT = 0
STREAM_COUNT = 0
DATA_POINT = 2 # GPS lat/lgt recorded before transmission
scooter_activated = True
scooter_moved = False

# Start PPPD
def openPPPD():
    # Check if PPPD is already running by looking at syslog output
    print("Opening PPPD...")
    output1 = subprocess.check_output("cat /var/log/syslog | grep pppd | tail -1", shell=True)
    if "secondary DNS address" not in output1 and "locked" not in output1:
        while True:
            # Start the "fona" process
            print("starting fona process...")
            subprocess.call("sudo pon fona", shell=True)
            sleep(2)
            output2 = subprocess.check_output("cat /var/log/syslog | grep pppd | tail -1", shell=True)
#             print(output2)
            if "script failed" not in output2:
                break
#     # Make sure the connection is working
    while True:
        print("Connection check...")
        output2 = subprocess.check_output("cat /var/log/syslog | grep pppd | tail -1", shell=True)
#         output3 = subprocess.check_output("cat /var/log/syslog | grep pppd | tail -3", shell=True)
#         print("Out2:{}".format(output2))
#         print("Out3:{}".format(output3))
#         if "secondary DNS address" in output2 or "DNS address" in output3:
        if "secondary DNS address" in output2:
            print("Connection is ready...Device is online...")
            return True

# Stop PPPD
def closePPPD():
    print ("\nTurning off cell connection using sudo poff fona...")
    # Stop the "fona" process
    subprocess.call("sudo poff fona", shell=True)
    # Make sure connection was actually terminated
    while True:
        output = subprocess.check_output("cat /var/log/syslog | grep pppd | tail -1", shell=True)
        if "Exit" in output:
            print("pppd is now close...")
            return True

# Check for a GPS fix
def checkForFix():
    # print ("checking for fix")
    # Start the serial connection SIM7000E
    ser=serial.Serial('/dev/ttyS0', 9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

    # Start the serial connection SIM808
    # ser=serial.Serial('/dev/ttyS0', 115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

    # Turn on the GPS
    ser.write(b"AT+CGNSPWR=1\r")
    ser.write(b"AT+CGNSPWR?\r")
    while True:
        response = ser.readline()
        if b"1" in response: # remove the whitespace before 1 for SIM7000E
            # print("GPS is ON!")
            break
    # Ask for the navigation info parsed from NMEA sentences
    ser.write(b"AT+CGNSINF\r")
    print("Getting NMEA...")
    while True:
            response = ser.readline()
            # Check if a fix was found
            if b"+CGNSINF: 1,1," in response:
                # print ("Fix found! OK!")
                # print response
                return True
            # If a fix wasn't found, wait and try again
            if b"+CGNSINF: 1,0," in response:
                sleep(5)
                ser.write(b"AT+CGNSINF\r")
                print ("Unable to find fix. still looking for fix...")
            else:
                ser.write(b"AT+CGNSINF\r")

# Read the GPS data for Latitude and Longitude
def getCoord():
    # Start the serial connection SIM7000E
    ser=serial.Serial('/dev/ttyS0', 9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

    # Start the serial connection SIM808
    # ser=serial.Serial('/dev/ttyS0', 115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

    ser.write(b"AT+CGNSINF\r")
    while True:
        response = ser.readline()
        if b"+CGNSINF: 1," in response:
            # Split the reading by commas and return the parts referencing lat and long
            array = response.split(b",")
            lat = array[3]
            # print lat
            lon = array[4]
            # print lon
            return (lat,lon)

def main_with_pppd():
    global STREAM_COUNT
    # Initialize the Initial State streamer
    # Start the program by opening the cellular connection and creating a bucket for our data
    if openPPPD():
        # print("\n\n\nOK ALRIGHT THEN! Everything looks good! Starting ISS streamer...")
        # streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY, buffer_size=20)

        # Wait long enough for the request to complete
        for c in range(INIT_DELAY):
            print ("Starting in T-minus {} second".format(INIT_DELAY-c))
            sleep(1)
        while True:
            # Close the cellular connection
            if closePPPD():
                READ_COUNT=0 # reset counter after closing connection
                sleep(1)
            # The range is how many data points we'll collect before streaming
            for i in range(DATA_POINT):
                # Make sure there's a GPS fix
                if checkForFix():
                    # Get lat and long
                    print("i = {}".format(i))
                    if getCoord():
                        READ_COUNT+=1
                        latitude, longitude = getCoord()
                        coord = "lat:" + str(latitude) + "," + "lgt:" + str(longitude)
                        print (coord)
                        # Buffer the coordinates to be streamed
                        print("Saving read #{} into buffer.".format(READ_COUNT))
                        # streamer.log("Coordinates",coord)
                        sleep(SECONDS_BETWEEN_READS) # 1 second
                    # Turn the cellular connection on every 2 reads
                    if i == DATA_POINT-1:
                        sleep(1)
                        print ("opening connection")
                        if openPPPD():
                            STREAM_COUNT+=1
                            # print ("Streaming location to Initial State")
                            # streamer.log("Read Count",str(READ_COUNT))
                            # streamer.log("Stream Count",str(STREAM_COUNT))
                            # # Flush the streaming buffer queue and send the data
                            # streamer.flush() # flush all the 4 readings to ISS
                            # print ("Streaming complete")

def main_without_pppd():
    global READ_COUNT
    # Initialize the Initial State streamer
    # Start the program by opening the cellular connection and creating a bucket for our data
    for c in range(INIT_DELAY):
        print ("Starting in T-minus {} second".format(INIT_DELAY-c))
        sleep(1)
    # streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY, buffer_size=20)
    # Wait long enough for the request to complete
    while True:
        # Make sure there's a GPS fix
        if checkForFix():
            # Get lat and long
            if getCoord():
                READ_COUNT+=1
                latitude, longitude = getCoord()
                coord = "lat:" + str(latitude) + "," + "lng:" + str(longitude)
                print (coord)
                print("Saving read #{} into buffer.\n".format(READ_COUNT))
                # Buffer the coordinates to be streamed
                # streamer.log("Coordinates",coord)
                sleep(SECONDS_BETWEEN_READS)
                # print "streaming location to Initial State"
                # Flush the streaming queue and send the data
                # streamer.flush()
                # print "streaming complete"


if __name__ == "__main__":
    main_without_pppd()
