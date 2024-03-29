# FX Rates script
## :thought_balloon: Functionalities:

* Reads data from [NBP API](https://api.nbp.pl) for the last 90 days
* Saves it to database
* Lists data
* Saves data to file
* For listing and saving data it is possible to select a subset of currencies to work with
* Calculates some stats
* Can be run daily to update a file with data 

Reflection on decisions taken during implementation can be found in [decision log](decision_log.md)

## :wrench: Installation

* Clone repo
* `pip install -r requirements`
* Create `db_config.json` file based on `sample_db_config.json` with access data to your database

## :blue_book:  Usage
```
usage: main.py [-h] [--log-level {DEBUG,INFO,WARNING,ERROR}] [--download] [--list] [--save] [--stats] [--rates {EUR/PLN,USD/PLN,CHF/PLN,EUR/USD,CHF/USD} [{EUR/PLN,USD/PLN,CHF/PLN,EUR/USD,CHF/USD} ...]] [--schedule]

FX Rates

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR}
                        Set the logging level (default: INFO)
  --download            Download the data from NBP API and store it in database
  --list                Output the rate data
  --save                Save the rate data to a file
  --stats               Calculate statistics for rates
  --rates {EUR/PLN,USD/PLN,CHF/PLN,EUR/USD,CHF/USD} [{EUR/PLN,USD/PLN,CHF/PLN,EUR/USD,CHF/USD} ...]
                        List of FX rates to work with - works with "--list", "--save" and "--stats" switches. All rates will be used when not specified.
  --schedule            Schedule execution of the download and save (with all other parameters in force) to run daily at 12:00 PM

```

### Examples
* Get data to database only `main.py --download`
* List data to terminal for EUR/PLN rate only `main.py --list --rates EUR/PLN`
* Show statistics for EUR/USD and CHF/USD and save raw data for these two to a file: `main.py --stats --rates EUR/USD CHF/USD --save`
* Schedule daily execution of download and saving to file for USD/PLN: `main.py --schedule --rates USD/PLN`