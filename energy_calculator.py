"""Energy calculator with JSON persistence and usage comparisons. Python 3.9+."""
# Persistence means keeping info after the program exits, so you can load it next time.

import json # convert Python objects to/from text for saving and loading
import math # provides isfinite() to check for valid numbers
from pathlib import Path # helps with file paths, including cross-platform compatibility

SAVE_FILE = Path(__file__).with_name("energy_devices.json") # file path for saving and loading devices and settings


def get_number(prompt, minimum=0, maximum=math.inf, whole=False): # a function to get a number from the user and validate it against the given minimum and maximum values, and whether it should be a whole number
    while True: # starts a loop that will continue until a valid number is entered
        try:
            value = float(input(prompt)) # prompts the user for input and converts it to a float (decimal number)
            if not math.isfinite(value) or not minimum <= value <= maximum: # checks if the value is finite and within the specified range; if not, it raises a ValueError
                raise ValueError 
            if whole and not value.is_integer(): # checks if the value should be a whole number and if it is not, raises a ValueError
                raise ValueError
            return int(value) if whole else value # return means sends the answer back to whichever part of the program called the function. return the value as an integer if it should be a whole number, otherwise returns it as a float
        except ValueError: # catches invalid input, prints an explanation, and lets the loop ask again
            kind = "whole number" if whole else "number" # determines the kind of number expected based on the 'whole' parameter
            print(f"Enter a finite {kind} from {minimum} to {maximum}.") # prints an error message if the input is invalid, prompting the user to enter a valid number within the specified range


def new_settings(): # prompts the user for electricity tariff, standing charge, and reporting period in days, and returns a dictionary with these settings, you retrieve a value using its key e.g. settings["rate_per_kwh"] to get the electricity rate in £/kWh
    return {
        "rate_per_kwh": get_number("Electricity tariff (p/kWh): ") / 100, # convert pence to pounds
        "standing_charge": get_number("Standing charge (p/day; 0 to exclude): ") / 100,
        "period_days": get_number("Reporting period in days: ", 1, whole=True),
    }

def daily_kwh(device, hours=None): # calculates the daily energy consumption in kWh for a given device, optionally using a specified number of hours instead of the device's default hours. If no hours are provided, it uses the device's stored hours value. The calculation converts power from watts to kilowatts and multiplies by the number of hours and the quantity of devices.
    if hours is None:
        hours = device["hours"]
    return device["power_watts"] / 1000 * hours * device["quantity"]


def add_device(devices): # prompts the user for device details and adds a new device to the list
    name = input("Device name: ").strip()
    if not name:
        print("Device name cannot be empty.")
        return # exits the function early if the device name is empty, preventing the addition of a device with no name
    devices.append({ # adds a new device to the list with the specified details
        "name": name,
        "power_watts": get_number("Power per device (W): ", 0.01),
        "hours": get_number("Average hours used per day: ", 0, 24),
        "quantity": get_number("Number of identical devices: ", 1, whole=True),
    })
    print("Device added. Choose Save to keep your changes.")


def report(devices, settings): # this function receives both the device list and the settings dictionary.
    rate = settings["rate_per_kwh"] # creates shorter local variable names to make the calculations easier to read
    days = settings["period_days"]
    print(f"\nENERGY REPORT — {days} days; tariff {rate * 100:g} p/kWh") 
    for index, device in sorted(enumerate(devices, 1), # sorts the devices by their daily energy consumption in kWh, in descending order, and enumerates them starting from 1. The sorted function uses a lambda (unnamed) function to calculate the daily energy consumption for each device, allowing the report to display devices in order of their energy usage. So enumerate(devices, 1) pairs each device with a number, beginning at 1. sorted(...) puts those pairs in order.    
                                key=lambda item: daily_kwh(item[1]), reverse=True): # key=lambda item: daily_kwh(item[1]) tells Python to sort by each device’s daily energy use.  reverse=True puts the highest value first. item[1] means the device dictionary in the numbered pair
        energy = daily_kwh(device)
        cost = energy * rate
        print(f"{index}. {device['name']} (x{device['quantity']}, " # Square brackets retrieve a dictionary value or a list item.
              f"{device['hours']:g} h/day): {energy:.3f} kWh/day | " # :g uses a compact number format, usually avoiding unnecessary trailing zeros.
              f"£{cost:.2f}/day | £{cost * days:.2f}/period | £{cost * 365:.2f}/year")
    energy_total = sum(daily_kwh(device) for device in devices) # calculates the total daily energy consumption for all devices by summing the daily kWh of each device in the list.
    device_cost = energy_total * rate # the combined daily cost
    standing = settings["standing_charge"] # the standing charge
    print(f"Device total: {energy_total:.3f} kWh/day; £{device_cost:.2f}/day")
    print(f"Standing charge: £{standing:.2f}/day")
    print(f"Combined: £{device_cost + standing:.2f}/day | "
          f"£{(device_cost + standing) * days:.2f}/period | "
          f"£{(device_cost + standing) * 365:.2f}/year")

def comparison(devices, settings): # this function allows the user to compare the current energy usage of their devices with a proposed reduced usage. It calculates the baseline energy consumption and cost, then prompts the user to enter reduced hours for each device. It calculates the proposed energy consumption and cost based on the new hours, and displays the savings in both daily and annual terms. The function also provides a comparison of costs for different time periods, including the standing charge in both estimates.
    if not devices: # checks if the devices list is empty, and if so, prints a message and returns early, since there are no devices to compare. An empty list counts as a False value in Python, so if not devices evaluates to True when the list is empty.
        print("Add or load devices first.")
        return
    print("\nEnter reduced hours for each device; press Enter to keep its current hours.")
    baseline = sum(daily_kwh(device) for device in devices) # baseline is the current total daily energy consumption for all devices, calculated by summing the daily kWh of each device in the list.
    proposed = 0 # will accumulate the total using reduced hours. It starts at 0 and will be updated as the user enters new hours for each device.
    for device in devices:
        current = device["hours"] # stores the current hours of usage for the device, which will be displayed to the user as a reference when prompting for reduced hours.
        while True:
            answer = input(f"{device['name']} (currently {current:g} h/day), new hours: ").strip() # prompts the user to enter new hours for the device, showing the current hours as a reference. The input is stripped of leading and trailing whitespace.
            if not answer: # if the user presses Enter without typing anything, it keeps the current hours for that device. The not answer condition checks if the input is empty (i.e., the user just pressed Enter). If so, it assigns the current hours to the hours variable and breaks out of the loop to move on to the next device.
                hours = current 
                break
            try:
                hours = float(answer)
                if math.isfinite(hours) and 0 <= hours <= current: # new hours must be between zero and the current hours. The comparison is specifically for reducing usage.
                    break
            except ValueError:
                pass
            print(f"Enter hours from 0 to {current:g}, or press Enter.")
        new_energy = daily_kwh(device, hours)
        proposed += new_energy # the += means add to the existing value
        saving = (daily_kwh(device) - new_energy) * settings["rate_per_kwh"] 
        print(f"  Savings: £{saving:.2f}/day; £{saving * 365:.2f}/year")

    rate = settings["rate_per_kwh"]
    standing = settings["standing_charge"]
    before = baseline * rate + standing
    after = proposed * rate + standing
    print("\nCOMPARISON (including the same standing charge in both estimates)")
    print(f"{'Period':<16}{'Current (£)':>16}{'Reduced (£)':>16}{'Savings (£)':>16}") # <16: align text to the left within 16 spaces. >16: align text to the right within 16 spaces. >16.2f: align a number to the right and display two decimal places.
    for label, days in [("Day", 1), (f"{settings['period_days']} days", settings["period_days"]), # ("Month (30 days)", 30), takes the two values from each tuple and puts them into label and days 
                        ("Year (365 days)", 365)]:
        print(f"{label:<16}{before * days:>16.2f}{after * days:>16.2f}"
              f"{(before - after) * days:>16.2f}")
    print(f"Energy saved: {baseline - proposed:.3f} kWh/day.")
    print("This comparison does not change your saved device hours.")

def validate_data(data): # This function checks the loaded information before using it.
    """Validate the whole file before replacing the current session.""" 
    def number(value, minimum=0, maximum=math.inf, whole=False): # This helper checks existing values rather than asking the user for input.
        if type(value) not in (int, float): # checks that a value is an integer or decimal number. It rejects text such as "three" and other types.
            raise ValueError("Expected a numeric value.")
        if not math.isfinite(value) or not minimum <= value <= maximum:
            raise ValueError("Numeric value is outside its allowed range.")
        if whole and value != int(value):
            raise ValueError("Expected a whole number.")

    if not isinstance(data, dict) or data.get("version") != 1: # checks that the loaded data is a dictionary and that it has a "version" key with the value 1. If not, it raises a ValueError indicating that the save format is unsupported.
        raise ValueError("Unsupported save format.")
    settings, devices = data["settings"], data["devices"] # unpacks the settings and devices from the loaded data dictionary for further validation.
    number(settings["rate_per_kwh"]) 
    number(settings["standing_charge"])
    number(settings["period_days"], 1, whole=True)
    if not isinstance(devices, list):
        raise ValueError("Devices must be a list.")
    for device in devices:
        if not isinstance(device["name"], str) or not device["name"].strip():
            raise ValueError("A device has an invalid name.")
        number(device["power_watts"], 0.01)
        number(device["hours"], 0, 24)
        number(device["quantity"], 1, whole=True)
    return devices, settings # returns the validated devices and settings, allowing the program to use them safely after loading from a file.

def load_data(path=SAVE_FILE): # loads the saved devices and settings from a JSON file, validates the data, and returns the devices and settings. If the file does not exist or contains invalid data, it raises an appropriate error.
    data = json.loads(path.read_text(encoding="utf-8")) # reads the content of the specified JSON file, decodes it from UTF-8, and parses it into a Python dictionary using json.loads(). This allows the program to read the text and convert it to python format.
    return validate_data(data)


def save_data(devices, settings, path=SAVE_FILE): 
    data = {"version": 1, "settings": settings, "devices": devices} # groups everything into a single dictionary for saving. The "version" key is included to allow for future changes in the save format, ensuring backward compatibility.
    validate_data(data) # checks the data is valid before saving
    # Replace only after the complete JSON has been written successfully.
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path) # replaces the save file with the completed temporary file. This helps protect the previous save if writing the new file fails before completion. Each save replaces the previous saved state; it does not keep a history of saves.

def main(): # co ordinates the program flow, including loading saved data, prompting for new settings, and providing a menu for the user to add devices, generate reports, compare usage, save data, or exit the program. It handles user input and manages the overall user experience.
    print("Energy Cost Calculator")
    print("Estimates assume constant power during usage and the same usage every day.")
    devices, settings = [], None # this creates an empty device list and a settings variable set to None, which will later hold the user's electricity tariff, standing charge, and reporting period. The empty list is ready to store device information as the user adds devices.
    if SAVE_FILE.exists() and input("Load saved devices and tariff? (y/n): ").strip().lower() == "y": 
        try:
            devices, settings = load_data() # called unpacking takes the two returned values from load_data() and assigns them to the devices and settings variables. This allows the program to use the loaded data directly without needing to access the returned tuple.
            print(f"Loaded {len(devices)} devices.")
        except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
            print(f"Could not load save file: {error}")
    if settings is None: # if nothing was loaded this asks for fresh settings
        settings = new_settings()

    while True: # A colon starts an indented block, such as the body of a function, condition, or loop.
        print("\n1 Add device | 2 Report | 3 Compare reduced usage") # \n starts a new line.
        print("4 Save | 5 Load | 6 Change tariff/period | 0 Exit")
        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                add_device(devices)
            elif choice == "2": # elif means otherwise if this condition is true. It only checks this if the previous if was false. This is more efficient than checking all conditions every time.
                report(devices, settings)
            elif choice == "3":
                comparison(devices, settings)
            elif choice == "4":
                save_data(devices, settings)
                print(f"Saved to {SAVE_FILE}")
            elif choice == "5":
                if input("Replace current devices and settings with the saved file? (y/n): ").strip().lower() == "y":
                    devices, settings = load_data()
                    print(f"Loaded {len(devices)} devices.")
            elif choice == "6":
                settings = new_settings()
            elif choice == "0":
                if input("Save before exiting? (y/n): ").strip().lower() == "y":
                    save_data(devices, settings)
                return
            else:
                print("Choose one of the menu numbers.")
        except (OSError, ValueError, KeyError, TypeError, OverflowError) as error: # catches errors as follows: OSError for file issues, ValueError for invalid values, KeyError for missing dictionary keys, TypeError for wrong data types, and OverflowError for numbers that are too large. It prints a message indicating the operation failed and shows the specific error encountered.
            print(f"Operation failed: {error}")


if __name__ == "__main__": # means run the following code when this file is started directly
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nExited. Changes since your last save have not been saved.")