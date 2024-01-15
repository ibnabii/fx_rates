# Fetching Currency Data:
## Utilizing the website https://api.nbp.pl/ and Python, retrieve exchange rates for EUR/PLN, USD/PLN, and CHF/PLN for the last 90 days. 

* Assumption: I will work with mean rates (ie. one rate per day per currency pair.
* NBP API allows selection of data range by either count or within selected period. Rates are not published for some dates (eg. weekends), so I will stick explicitly to requirement, ie download data for the last 90 days (which means number of rates will be lower than 90)   

# Add:
## Implement functionality for the script to run daily at 12:00 PM and automatically save the data to the "all_currency_data.csv" file. Ensure that each script execution overwrites the file only with new entries.

* 'Overwrites the file only with new entries' - so after each script execution it will contain data for the last 90 days only. 