from unittest.mock import call, patch, Mock
import unittest
from io import StringIO

from ahwr import reader


class TestReader(unittest.TestCase):

    def test_read_file_with_no_records(self):
        # arrange
        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
            <HealthData locale="en_GB">
                <ExportDate value="2019-08-26 13:24:31 +0100"/>
            </HealthData>
            """
        f = StringIO(xml_string)

        # act
        records = reader.read_workout_and_heart_rate_records(f)

        # assert
        self.assertEqual(
            [],
            list(records)
        )

    def test_read_file_with_two_workout_records_and_one_heart_rate_record(self):
        # arrange
        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
            <HealthData locale="en_GB">
                <Workout workoutActivityType="HKWorkoutActivityTypeRunning" duration="17.51666666666667">
                    <MetadataEntry key="ExerciseIdentifier" value="2019-06-27T08:18:35.910Z0"/>
                </Workout>
                <Workout workoutActivityType="HKWorkoutActivityTypeRunning" duration="19.5">
                    <MetadataEntry key="ExerciseIdentifier" value="2019-08-22T06:41:36.191Z0"/>
                </Workout>
                <Record type="HKQuantityTypeIdentifierHeartRate" value="129">
                    <MetadataEntry key="HKMetadataKeyHeartRateMotionContext" value="0"/>
                </Record>
            </HealthData>
            """
        f = StringIO(xml_string)

        # act
        records = reader.read_workout_and_heart_rate_records(f)

        # assert
        self.assertEqual(3, len(list(records)))

    def test_read_data_returns_iterator_yielding_workouts_and_heart_rate_records(self):
        # arrange
        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
            <HealthData locale="en_GB">
                <Workout 
                        workoutActivityType="HKWorkoutActivityTypeRunning" 
                        duration="15.71666666666667" 
                        durationUnit="min" 
                        totalDistance="1.951105543625229" 
                        totalDistanceUnit="mi" 
                        totalEnergyBurned="184" 
                        totalEnergyBurnedUnit="kcal" 
                        sourceName="Polar Beat" 
                        sourceVersion="316" 
                        creationDate="2018-10-02 07:58:33 +0100" 
                        startDate="2018-10-02 06:54:12 +0100" 
                        endDate="2018-10-02 07:09:55 +0100">
                    <MetadataEntry key="ExerciseIdentifier" value="2018-10-02T06:54:12.279Z0"/>
                </Workout>
                <Record 
                        type="HKQuantityTypeIdentifierHeartRate" 
                        sourceName="Nitesh's iPhone" 
                        sourceVersion="13.0"  
                        unit="count/min" 
                        creationDate="2019-06-29 16:15:12 +0100" 
                        startDate="2019-06-29 16:15:11 +0100" 
                        endDate="2019-06-29 16:15:11 +0100" 
                        value="129">
                    <MetadataEntry key="HKMetadataKeyHeartRateMotionContext" value="0"/>
                </Record>
            </HealthData>
            """
        f = StringIO(xml_string)

        # act
        records = reader.read_workout_and_heart_rate_records(f)
        workout_record = next(records)
        heart_rate_record = next(records)

        # assert
        self.assertEqual(
            [
                {
                    'workoutActivityType': 'HKWorkoutActivityTypeRunning',
                    'duration': '15.71666666666667',
                    'durationUnit': 'min',
                    'totalDistance': '1.951105543625229',
                    'totalDistanceUnit': 'mi',
                    'totalEnergyBurned': '184',
                    'totalEnergyBurnedUnit': 'kcal',
                    'sourceName': 'Polar Beat',
                    'sourceVersion': '316',
                    'creationDate': '2018-10-02 07:58:33 +0100',
                    'startDate': '2018-10-02 06:54:12 +0100',
                    'endDate': '2018-10-02 07:09:55 +0100',
                },
                {
                    'type': 'HKQuantityTypeIdentifierHeartRate',
                    'sourceName': 'Nitesh\'s iPhone',
                    'sourceVersion': '13.0',
                    'unit': 'count/min',
                    'creationDate': '2019-06-29 16:15:12 +0100',
                    'startDate': '2019-06-29 16:15:11 +0100',
                    'endDate': '2019-06-29 16:15:11 +0100',
                    'value': '129',
                }
            ],
            [workout_record, heart_rate_record],
        )

    def test_enrich_records_with_no_matching_heart_rate_data_does_nothing(self):
        # arrange
        records = [
            {
                'workoutActivityType': 'HKWorkoutActivityTypeRunning',
                'duration': '15.71666666666667',
                'durationUnit': 'min',
                'totalDistance': '1.951105543625229',
                'totalDistanceUnit': 'mi',
                'totalEnergyBurned': '184',
                'totalEnergyBurnedUnit': 'kcal',
                'sourceName': 'Polar Beat',
                'sourceVersion': '316',
                'creationDate': '2018-10-02 07:58:33 +0100',
                'startDate': '2018-10-02 06:54:12 +0100',
                'endDate': '2018-10-02 07:09:55 +0100',
            },
            {
                'type': 'HKQuantityTypeIdentifierHeartRate',
                'sourceName': 'Nitesh\'s iPhone',
                'sourceVersion': '13.0',
                'unit': 'count/min',
                'creationDate': '2019-06-29 16:15:12 +0100',
                'startDate': '2019-06-29 16:15:11 +0100',
                'endDate': '2019-06-29 16:15:11 +0100',
                'value': '129',
            }
        ]

        # act
        enriched = reader.enrich_records_with_heart_rate(records)

        # assert
        self.assertEqual(list(records), list(enriched))

    def test_convert_no_records_to_csv(self):
        # arrange
        records = iter([])
        f = StringIO()
        # act

        reader.write_enriched_records_to_csv(records, f)

        # assert
        expected = ''
        self.assertEqual(expected, f.getvalue())

    def test_convert_two_records_to_csv(self):
        # arrange
        records = iter([
            {
                'workoutActivityType': 'HKWorkoutActivityTypeRunning',
                'duration': '15.71666666666667',
                'durationUnit': 'min',
                'totalDistance': '1.951105543625229',
                'totalDistanceUnit': 'mi',
            },
            {
                'workoutActivityType': 'HKWorkoutActivityTypeRunning',
                'duration': '29.78333333333333',
                'durationUnit': 'min',
                'totalDistance': '3.492727471566054',
                'totalDistanceUnit': 'mi',
            },
        ])
        f = StringIO()
        # act

        reader.write_enriched_records_to_csv(records, f)

        # assert
        expected = (
            'workoutActivityType,duration,durationUnit,totalDistance,totalDistanceUnit,totalEnergyBurned,totalEnergyBurnedUnit,sourceName,sourceVersion,creationDate,startDate,endDate\r\n'
            'HKWorkoutActivityTypeRunning,15.71666666666667,min,1.951105543625229,mi,,,,,,,\r\n'
            'HKWorkoutActivityTypeRunning,29.78333333333333,min,3.492727471566054,mi,,,,,,,\r\n'
        )
        self.assertEqual(expected, f.getvalue())

    def test_convert_apple_health_xml_to_csv_results_in_expected_call_to_write_enriched_records_to_csv(self):
        # arrange
        mock_read = lambda *args: 'read_workout_and_heart_rate_records({})'.format(','.join(args))
        mock_enrich = lambda *args: 'enrich_records_with_heart_rate({})'.format(','.join(args))

        mock_write_to_csv = Mock()

        input_f = 'input_f'
        output_f = 'output_f'

        # act
        with patch.object(reader, 'read_workout_and_heart_rate_records', mock_read):
            with patch.object(reader, 'enrich_records_with_heart_rate', mock_enrich):
                with patch.object(reader, 'write_enriched_records_to_csv', mock_write_to_csv):
                    reader.convert_apple_health_xml_to_csv(input_f, output_f)

        # assert
        self.assertEqual(
            [call('enrich_records_with_heart_rate(read_workout_and_heart_rate_records(input_f))', 'output_f')],
            mock_write_to_csv.mock_calls)


if __name__ == '__main__':
    unittest.main()
