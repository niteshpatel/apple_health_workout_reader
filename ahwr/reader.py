import csv
import os
from xml.etree.ElementTree import iterparse

WORKOUT_RECORD_KEYS = [
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
]


def read_workout_and_heart_rate_records(f):
    for event, elem in iterparse(f, events=('end',)):
        if elem.tag in ('Workout', 'Record'):
            yield elem.attrib


def enrich_records_with_heart_rate(records):
    return records


def write_enriched_records_to_csv(records, f):
    try:
        first_record = next(records)
    except StopIteration:
        return

    writer = csv.DictWriter(f, fieldnames=WORKOUT_RECORD_KEYS, extrasaction='ignore')
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
