from retrieve_era5 import retrieve_era5
from process_era5 import process_era5
from combine_weather import combine_weather


def main():
    retrieve_era5()
    process_era5()
    combine_weather()

if __name__ == '__main__':
    main()
