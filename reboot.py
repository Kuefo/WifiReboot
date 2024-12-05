To interact with this script using nRF Connect (for Android or iOS) or LightBlue (for iOS):
 
nRF Connect
Open nRF Connect on your smartphone.
Scan for Bluetooth devices and connect to your CircuitPython device (it should be advertising as a BLE UART service).
Once connected, go to the "UART" service and find the UART characteristic.
Write the string "reboot" to this characteristic and send it. This should trigger the reboot request.
 
LightBlue
Open LightBlue on your iPhone.
Scan for Bluetooth devices and connect to your CircuitPython device.
Explore the services and look for the UART service.
Write the string "reboot" to the appropriate characteristic to trigger the reboot request.
 
_______________________________________________________________________________________________________________________________________
import time
import os
import board
import busio
import displayio
import digitalio
from digitalio import DigitalInOut, Pull
import socketpool
import ssl
import adafruit_requests
import adafruit_displayio_sh1106
from adafruit_debouncer import Debouncer
import adafruit_ble
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
 
## WiFi credentials
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
passwd = os.getenv("CIRCUITPY_WIFI_PASSWORD")
 
## Connect to WiFi
wifi.radio.connect(ssid=ssid, password=passwd)
print("Connected with IP:", wifi.radio.ipv4_address)
 
## Set up display
displayio.release_displays()
WIDTH, HEIGHT = 130, 64  ## Display size
i2c = busio.I2C(board.SCL, board.SDA)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3c)
display = adafruit_displayio_sh1106.SH1106(display_bus, width=WIDTH, height=HEIGHT)
 
## Initialize down button
down_button_pin = DigitalInOut(board.IO18)  ## Use the correct pin for your down button
down_button_pin.pull = Pull.UP
down_button = Debouncer(down_button_pin)
 
## Set up BLE
ble = adafruit_ble.BLERadio()
uart_service = UARTService()
advertisement = ProvideServicesAdvertisement(uart_service)
 
def send_reboot_request():
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())
 
    ## Device info and API endpoint
    device_ip = os.getenv("TARGET_IP")
    device_password = os.getenv("TARGET_PASSWORD")
    url = f"http://{device_ip}/remoteReset"
    data = {'password': device_password}
 
    ## Send POST request
    response = requests.post(url, data=data)
    return response
 
while True:
    ## BLE connection handling
    if not ble.connected:
        print("Waiting for a BLE connection...")
        ble.start_advertising(advertisement)
    else:
        print("Connected via BLE")
        ble.stop_advertising()
 
        ## Check for incoming BLE data
        if uart_service.in_waiting:
            command = uart_service.read(uart_service.in_waiting)
            command = command.decode("utf-8").strip()
 
            ## Trigger reboot request when receiving a specific command (e.g., "reboot")
            if command == "reboot":
                print("Received reboot command via BLE")
                response = send_reboot_request()
                print(f"Response: {response.status_code}\n{response.text}")
                print("DONE!")
                time.sleep(10)
 
    ## Button check
    down_button.update()
    if down_button.fell:
        print("Sending reboot request...")
        response = send_reboot_request()
        print(f"Response: {response.status_code}\n{response.text}")
        print("DONE!")
        time.sleep(10)
 
    time.sleep(0.1)  ## Small delay to reduce CPU usage
