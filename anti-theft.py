from os import system
import serial
import subprocess
from time import sleep


scooter_activated = False
scooter_moved = False
range_precision = 0.000001

# Check for a GPS fix
def checkForFix():
    print "checking for fix"
    # Start the serial connection SIM7000E
    # ser=serial.Serial('/dev/ttyS0', 9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

    # Start the serial connection SIM808
    ser=serial.Serial('/dev/ttyS0', 115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

    # Turn on the GPS
    ser.write("AT+CGNSPWR=1\r")
    ser.write("AT+CGNSPWR?\r")
    while True:
        response = ser.readline()
        if " 1" in response: # remove the whitespace before 1 for SIM7000E
            break
    # Ask for the navigation info parsed from NMEA sentences
    ser.write("AT+CGNSINF\r")
    while True:
            response = ser.readline()
            # Check if a fix was found
            if "+CGNSINF: 1,1," in response:
                # print response
                return True
            # If a fix wasn't found, wait and try again
            if "+CGNSINF: 1,0," in response:
                sleep(5)
                ser.write("AT+CGNSINF\r")
                print "Unable to find fix. still looking for fix..."
            else:
                ser.write("AT+CGNSINF\r")

# Read the GPS data for Latitude and Longitude
def getCoord():
    # Start the serial connection SIM7000E
    # ser=serial.Serial('/dev/ttyS0', 9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

    # Start the serial connection SIM808
    ser=serial.Serial('/dev/ttyS0', 115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

    ser.write("AT+CGNSINF\r")
    while True:
        response = ser.readline()
        if "+CGNSINF: 1," in response:
            # Split the reading by commas and return the parts referencing lat and long
            array = response.split(",")
            lat = array[3]
            # print lat
            lon = array[4]
            # print lon
            return (lat,lon)


def main_without_pppd():
    count = 0
    list_lat = list()
    list_lgt = list()
    # Initialize the Initial State streamer
    # Start the program by opening the cellular connection and creating a bucket for our data
    #print("Starting streamer...")
    #streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY, buffer_size=20)
    # Wait long enough for the request to complete

    while True:
        # Make sure there's a GPS fix
        if checkForFix():
            # Get lat and long
            if getCoord():
                
                #get average of 10 readings
                for i in range (3):
                    latitude, longitude = getCoord()
                    lat = float(latitude)
                    lgt = float(longitude)
                    list_lat.append(lat)
                    list_lgt.append(lgt)
                    
                    coord = "movv lat:" + str(latitude) + "," + "movv lgt:" + str(longitude)
                    print coord            
                    
#                     print ("Recorded LAT:",len(list_lat))
#                     print ("Recorded LGT:",len(list_lgt))
#                     
#                     print("sum lat",sum(list_lat))
#                     print("sum lgt",sum(list_lgt))
                    sleep(1)
                count+=1
                print("average reading {}".format(count))
                avgLat = sum(list_lat)/len(list_lat)
                avgLgt = sum(list_lgt)/len(list_lgt)
                print("avgLAT:", avgLat ,"avgLGT:",avgLgt)

                if lat < avgLat + range_precision and lat > avgLat- range_precision:
                    print("static")
                else:
                    print("move")
                    if scooter_activated:
                        print("ok")
                    else:
                        print("unauthorized usage")

if __name__ == "__main__":
    main_without_pppd()

