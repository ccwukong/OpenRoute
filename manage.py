import click
import pandas as pd
import requests
import json
import os
import sys
from openpyxl import Workbook
from openroute.grouping import LocationGrouping, DriverGrouping
from openroute.optimize import Routing
from openroute.models import Driver, Location, Coordinates, GeoArea
from decimal import Decimal


@click.command()
@click.option('--file', help='The absolute path of setting.json file')
def cli(file):
    if not file:
        print('Error. No schema file provided.')
    else:
        try:
            with open(file) as setting_file:
                print('Loading setting file...')
                settings = json.load(setting_file)
                print('Setting file loaded.')

                print('Reading driver data...')
                drivers = settings.get('drivers')
                print('Driver data loaded.')

                print('Reading location data...')
                df = pd.read_excel(settings.get('inputFile'))
                # df['sort'] = df['delivery_time_window'].str.extract('(\d+)',
                #                                                     expand=False).astype(int)
                # df.sort_values('sort', inplace=True, ascending=True)
                # df = df.drop('sort', axis=1)
                print('Location data loaded.')

                locations = {}
                for _, row in df.iterrows():
                    pickup_address = row['pickup_location_address']
                    pickup_window = tuple(
                        map_time_to_seconds(row['pickup_time_window']))

                    if pickup_address in locations:
                        new_item = {'address': row['delivery_address'],
                                    'coordinates':
                                        map_address_to_coordinates(
                                            row['delivery_address'],
                                            settings.get('googleAPIKey'))
                                        if settings.get('addressType') == 'address' else
                                        map_str_to_coordinates(
                                            row['delivery_address']),
                                    'delivery_window':
                                        map_time_to_seconds(
                                            row['delivery_time_window']),
                                    'capacity': row['capacity'],
                                    'order_time': 0,
                                    'ref': str(row['customer_order_number'])}
                        if pickup_window in locations[pickup_address]:
                            locations[pickup_address]
                            [pickup_window].append(new_item)
                        else:
                            locations[pickup_address][pickup_window] = [{
                                'address': pickup_address,
                                'coordinates':
                                    map_address_to_coordinates(
                                        pickup_address,
                                        settings.get('googleAPIKey'))
                                    if settings.get('addressType') == 'address'
                                    else map_str_to_coordinates(
                                        pickup_address),
                                'delivery_window':
                                    map_time_to_seconds(
                                        row['pickup_time_window']),
                                'capacity': 0,
                                'order_time': 0
                            }]
                            locations[pickup_address]
                            [pickup_window].append(new_item)
                    else:
                        locations[pickup_address] = {}

                        locations[pickup_address][pickup_window] = [{
                            'address': pickup_address,
                            'coordinates':
                                map_address_to_coordinates(
                                    pickup_address,
                                    settings.get('googleAPIKey'))
                                if settings.get('addressType') == 'address'
                                else map_str_to_coordinates(pickup_address),
                            'delivery_window':
                                map_time_to_seconds(row['pickup_time_window']),
                            'capacity': 0,
                            'order_time': 0
                        }]

                        locations[pickup_address][pickup_window].append({
                            'address': row['delivery_address'],
                            'coordinates':
                                map_address_to_coordinates(
                                    row['delivery_address'],
                                    settings.get('googleAPIKey'))
                                if settings.get('addressType') == 'address'
                                else map_str_to_coordinates(
                                    row['delivery_address']),
                            'delivery_window':
                                map_time_to_seconds(
                                    row['delivery_time_window']),
                            'capacity': row['capacity'],
                            'order_time': 0,
                            'ref': str(row['customer_order_number'])
                        })

                schedules = DriverGrouping().group_drivers_by_time_slot(
                    drivers=[Driver(id=item.get('id'),
                                    time_slots=item.get('time_slots'),
                                    capacity=item.get('capacity'),
                                    speed=item.get('speed')) for
                             item in drivers])

                data, not_found = LocationGrouping().group_locations(
                    locations,
                    schedules,
                    settings.get('mergeIdentical'))

                for key, val in data.items():
                    for k, v in val.items():
                        if len(v.get('locations')) < 2:
                            data[key][k]['locations'] = []

                print('Start route optimization...')
                book = Workbook()
                sheet = book.active

                inhouse = []
                public = []
                for pickup_address, pickup_windows in data.items():
                    for pickup_window, obj in pickup_windows.items():
                        locs = obj.get('locations')
                        driver_ids = obj.get('driver_ids')
                        while locs and driver_ids:
                            driver = None
                            for item in drivers:
                                if item.get('id') == driver_ids[0]:
                                    driver = item
                                    break

                            # find the indices for all filtered
                            # locations in data object
                            filtered_indices = []
                            for k, v in enumerate(locs):
                                if v.capacity <= driver.get('capacity'):
                                    filtered_indices.append(k)

                            indices = Routing(
                                locations=[loc for loc in locs if
                                           loc.capacity <=
                                           driver.get('capacity')],
                                num_vehicles=len(locs)).generate_routes(
                                    vehicle_capacity=driver.get('capacity'),
                                    speed=driver.get('speed'),
                                    service_time_unit=settings['serviceTime'])

                            if len(indices) == 0:
                                break
                            else:
                                # remove driver from available driver list
                                # only if a route has been built
                                driver_id = driver_ids.pop(0)

                                routes = []
                                for item in indices[0]:
                                    if ';' in locs[filtered_indices[item]].ref:
                                        for sub_item in locs[filtered_indices[item]].ref.split(';'):
                                            itm_info = sub_item.split(',')
                                            routes.append(Location(
                                                coordinates=Coordinates(
                                                    locs[filtered_indices[item]].coordinates[0],
                                                    locs[filtered_indices[item]].coordinates[1]),
                                                address=locs[filtered_indices[item]].address,
                                                delivery_window=locs[filtered_indices[item]].delivery_window,
                                                capacity=float(itm_info[1]),
                                                ref=itm_info[0]))
                                    else:
                                        routes.append(locs[filtered_indices[item]])

                                    if filtered_indices[item] != 0:
                                        locs[filtered_indices[item]] = None
                                inhouse.append({driver_id: routes})
                                locs = list(filter(lambda x: x is not None, locs))
                                #sheet.append(tuple([str(item.to_json()) for item in routes]))

                        obj['locations'] = locs if len(locs) > 1 else [] 
                book.save(settings.get('outputFile'))

                # #There might be drivers and locations left over due to the merge identical, check again
                # for pickup_address, pickup_windows in data.items():
                #     for pickup_window, obj in pickup_windows.items():
                #         locs = obj.get('locations')

                #         #we have a merged location with capacity 20 here, thus the driver ID 7 is left over
                #         print([item.to_json() for item in locs])
                #         print(obj.get('driver_ids'))

                if settings['publicDriver']['required']:
                    print('Using public drivers...')
                    for pickup_address, pickup_windows in data.items():
                        for pickup_window, obj in pickup_windows.items():
                            locs = obj.get('locations')

                            if locs:
                                indices = Routing(
                                    locations=locs,
                                    num_vehicles=len(locs)).generate_routes(
                                        vehicle_capacity=settings['publicDriver']['specification']['capacity'],
                                        speed=settings['publicDriver']['specification']['speed'],
                                        service_time_unit=settings['serviceTime'])
                                if len(indices) == 0:
                                    break
                                else:
                                    for idx_list in indices:
                                        routes = []

                                        for item in idx_list:
                                            if ';' in locs[item].ref:
                                                for sub_item in locs[item].ref.split(';'):
                                                    itm_info = sub_item.split(',')
                                                    routes.append(
                                                        Location(
                                                            coordinates=Coordinates(locs[item].coordinates[0],
                                                                                    locs[item].coordinates[1]),
                                                            address=locs[item].address,
                                                            delivery_window=locs[item].delivery_window,
                                                            capacity=float(itm_info[1]),
                                                            ref=itm_info[0]))
                                            else:
                                                routes.append(locs[item])
                                            if item != 0:
                                                locs[item] = None

                                        #sheet.append(tuple([str(item.to_json()) for item in routes]))
                                        public.append(routes)
                                    locs = list(filter(lambda x: x is not None, locs))
                                    obj['locations'] = locs if len(locs) > 1 else []

                Routing.merge_routes(inhouse_routes=inhouse,
                                     public_routes=public,
                                     drivers=drivers)

                sheet.append(tuple(['In-House drivers']))
                for item in inhouse:
                    for k, v in item.items():
                        sheet.append(tuple(['Driver ID: ' + str(k)]))
                        sheet.append(tuple([str(item.to_json()) for item in v]))

                sheet.append(tuple(['']))
                sheet.append(tuple(['Public drivers']))
                for route in public:
                    sheet.append(tuple([str(item.to_json()) for item in route]))                    

                sheet.append(tuple(['']))
                sheet.append(tuple(['Unmatched addresses']))
                sheet.append(tuple([item for item in not_found]))

                sheet.append(tuple(['']))
                sheet.append(tuple(['Unutilized drivers']))
                for pickup_address, pickup_windows in data.items():
                    for pickup_window, obj in pickup_windows.items():
                        for item in drivers:
                            if item.get('id') in obj.get('driver_ids'):
                                item['time_slots'] = [[map_seconds_to_time(ts[0]),
                                                       map_seconds_to_time(ts[1])] for ts in item['time_slots']]                             
                                sheet.append(tuple([json.dumps(item)]))

                book.save(settings.get('outputFile'))
                print('Done routing optimization.')
        except Exception as e:
            import traceback
            traceback.print_exc()
            print('Error. Unable to load the setting file.')
            sys.exit()


def map_address_to_coordinates(address, key):
    url = 'https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}'.format(
        address.replace('\n', ' '), key)
    response = requests.get(url)
    content = json.loads(response.__dict__['_content'])
    if content.get('results'):
        loc = content['results'][0]['geometry']['location']
        return [loc.get('lat'), loc.get('lng')]
    else:
        return [0, 0]


def map_str_to_coordinates(geocode):
    tmp = geocode.split(',')
    return [float(tmp[0]), float(tmp[1])]


def map_time_to_seconds(time):
    window = time.split('-')
    start = window[0].split(':')
    end = window[1].split(':')
    return [int(start[0])*3600+int(start[1])*60, int(end[0])*3600+int(end[1])*60]


def map_seconds_to_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '%02d:%02d' % (h, m) 


if __name__ == '__main__':
    cli()
