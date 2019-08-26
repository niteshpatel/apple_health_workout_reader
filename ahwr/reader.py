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
    for event, elem in iterparse(f, events=('end',)):
        if elem.tag in ('Workout', 'Record'):
            yield elem.attrib


def enrich_records_with_heart_rate(records):
    workouts = []
    heart_rates = {}

    for record in records:
        if record.get('workoutActivityType'):
            workouts.append(record)

        if record.get('type') == 'HKQuantityTypeIdentifierHeartRate':
            dt = datetime.datetime.strptime(record.get('startDate'), _DATETIME_FORMAT)
            heart_rates[dt] = record

    for workout in workouts:
        matching_heart_rates = []
        workout_start = datetime.datetime.strptime(workout['startDate'], _DATETIME_FORMAT)
        workout_end = datetime.datetime.strptime(workout['endDate'], _DATETIME_FORMAT)

        for heart_rate_dt in heart_rates:
            if workout_start < heart_rate_dt < workout_end:
                matching_heart_rates.append(heart_rates[heart_rate_dt])

        if matching_heart_rates:
            workout['HeartRate_unit'] = 'count/min'
            heart_rate_values = [int(heart_rate['value']) for heart_rate in matching_heart_rates]

            workout['HeartRate_average'] = str(int(sum(heart_rate_values) / len(heart_rate_values)))
            workout['HeartRate_min'] = str(min(heart_rate_values))
            workout['HeartRate_max'] = str(max(heart_rate_values))

        yield workout


def write_enriched_records_to_csv(records, f):
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
