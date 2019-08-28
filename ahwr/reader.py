import csv
import datetime
import os
from xml.etree.ElementTree import iterparse

_OUTPUT_COLUMNS = [
    'workoutActivityType',
    'duration',
    'durationUnit',
    'totalDistance',
    'totalDistanceUnit',
    'totalEnergyBurned',
    'totalEnergyBurnedUnit',
    'sourceName',
    'sourceVersion',
    'creationDate',
    'startDate',
    'endDate',
    'HeartRate_unit',
    'HeartRate_average',
    'HeartRate_min',
    'HeartRate_max',
]

_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S %z'


def read_workout_and_heart_rate_records(f):
    """
    Yield Workout and HeartRate records data as dicts.

    :param f: xml file handle
    """
    for event, elem in iterparse(f, events=('end',)):
        if elem.tag in ('Workout', 'Record'):
            yield elem.attrib


def enrich_records_with_heart_rate(records):
    """
    Given an iterable of Workout and HeartRate records, enrich the Workout records with the associated HeartRate data.

    :param records: iterable of Workout and HeartRate records.
    """
    workouts = []
    heart_rates = []

    for record in records:
        if record.get('workoutActivityType'):
            workouts.append(record)

        if record.get('type') == 'HKQuantityTypeIdentifierHeartRate':
            record['startDateParsed'] = datetime.datetime.strptime(record.get('startDate'), _DATETIME_FORMAT)
            heart_rates.append(record)

    heart_rates = sorted(heart_rates, key=lambda n: n['startDateParsed'])
    heart_rates_index = 0

    workouts = sorted(workouts, key=lambda n: datetime.datetime.strptime(n['startDate'], _DATETIME_FORMAT))
    for workout in workouts:
        matching_heart_rates, heart_rates_index = get_matching_heart_rates(heart_rates, heart_rates_index, workout)
        if matching_heart_rates:
            workout['HeartRate_unit'] = 'count/min'
            workout['HeartRate_average'] = str(int(sum(matching_heart_rates) / len(matching_heart_rates)))
            workout['HeartRate_min'] = str(min(matching_heart_rates))
            workout['HeartRate_max'] = str(max(matching_heart_rates))

        yield workout


def get_matching_heart_rates(heart_rates, heart_rates_index, workout):
    """
    Return matching HeartRate records for the given workout.

    The heart_rates items are sorted, and so the heart_heart_rates_index field
    determines where to start the search from.  Once we find the last matching
    item, we return the pointer to the calling method so that it can be
    passed back in at a later time to resume the search at the last location
    we looked at.  This is an optimisation that ensures O(2N) complexity for
    the matching process (as long as the workout records are sorted).

    :param heart_rates: An iterable of HeartRate records
    :param heart_rates_index: A pointer to start scanning HeartRate records from
    :param workout: Workout record for which to find matches
    :return: Matching HeartRate records
    """
    workout_start = datetime.datetime.strptime(workout['startDate'], _DATETIME_FORMAT)
    workout_end = datetime.datetime.strptime(workout['endDate'], _DATETIME_FORMAT)

    matching_heart_rates = []
    while heart_rates_index < len(heart_rates):
        hr = heart_rates[heart_rates_index]
        if hr['startDateParsed'] < workout_start:
            heart_rates_index += 1
            continue
        elif hr['startDateParsed'] <= workout_end:
            matching_heart_rates.append(int(hr['value']))
            heart_rates_index += 1
        else:
            break
    return matching_heart_rates, heart_rates_index


def write_enriched_records_to_csv(records, f):
    """
    Write the enriched workout records to a CSV file handle.

    :param records: Enriched Workout records
    :param f: file handle to write to
    """
    try:
        first_record = next(records)
    except StopIteration:
        return

    writer = csv.DictWriter(f, fieldnames=_OUTPUT_COLUMNS, extrasaction='ignore')
    writer.writeheader()
    writer.writerow(first_record)

    for record in records:
        writer.writerow(record)


def convert_apple_health_xml_to_csv(apple_health_xml_f, output_csv_f):
    """
    Read Workout and HeartRate records from an Apple Health XML Export and write out as a CSV file.

    The output will consist of one row per Workout record, with extra columns added containing
    the min, max, and average HeartRate for the Workout.

    :param apple_health_xml_f:
    :param output_csv_f:
    """
    records = read_workout_and_heart_rate_records(apple_health_xml_f)
    enriched = enrich_records_with_heart_rate(records)
    write_enriched_records_to_csv(enriched, output_csv_f)


if __name__ == '__main__':
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(title='Select Apple Health export.xml file')
    output_dir = filedialog.askdirectory(title='Select folder to save exported CSV')

    if file_path and output_dir:
        with open(file_path) as apple_health_xml_f:
            with open(os.path.join(output_dir, 'output.csv'), 'w', newline='') as output_csv_f:
                convert_apple_health_xml_to_csv(apple_health_xml_f, output_csv_f)
