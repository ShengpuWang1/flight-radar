import pyModeS as pms
import json
import time
import folium


def slice_msgs(msgs, n=28):
    return [msgs[i:i+n] for i in range(0, len(msgs), n)]


# for decode_msg
cat = [
    ['Surface emergency vehicle', 'Error Category', 'Surface service vehicle', 'Ground obstruction', 'Ground obstruction', 'Ground obstruction', 'Ground obstruction'],
    ['Glider, sailplane', 'Lighter-than-air', 'Parachutist, skydiver', 'Ultralight, hang-glider, paraglider', 'Reserved', 'Unmanned aerial vehicle', 'Space or transatmospheric vehicle'],
    ['(less than 7000 kg)', '(between 7000 kg and 34000 kg)', '(between 34000 kg to 136000 kg)', '(high vortex aircraft)', '(larger than 136000 kg)', '(high performance and high speed)', '(rotorcraft)']
]


def decode_msg(msg):
    flight = {
        'icao': pms.adsb.icao(msg),
        'typecode': pms.adsb.typecode(msg),
        'pos_update': -1
    }
    if 1 <= flight['typecode'] <= 4:
        flight['callsign'] = pms.adsb.callsign(msg)
        ca = pms.adsb.category(msg)
        if ca == 0 or flight['typecode'] == 1:
            flight['category'] = 'No category information'
        else:
            flight['category'] = cat[flight['typecode'] - 2][ca]
    elif 5 <= flight['typecode'] <= 8:
        flight['alt'] = '0 [m]'
        parity = pms.adsb.oe_flag(msg)
        flight['msg' + str(parity)] = msg
        flight['t' + str(parity)] = int(time.time())
        flight['velocity'] = pms.adsb.surface_velocity(msg)
        flight['pos_update'] = str(parity)
    elif 9 <= flight['typecode'] <= 18 or 20 <= flight['typecode'] <= 22:
        flight['alt'] = str(pms.adsb.altitude(msg) * 0.3084) + ' [m]'
        parity = pms.adsb.oe_flag(msg)
        flight['msg' + str(parity)] = msg
        flight['t' + str(parity)] = int(time.time())
        flight['pos_update'] = str(parity)
    elif flight['typecode'] == 19:
        flight['velocity'] = pms.adsb.airborne_velocity(msg)

    del flight['typecode']
    return flight


# read msgs from new signal
file = open('msgs.txt', 'r')
msgs = slice_msgs(file.read())
file.close()
flights = []
for msg in msgs:
    try:
        flight = decode_msg(msg)
        flights.append(flight)
    except:
        pass

# load previous flight information
with open('flights_record.json', 'r') as json_file:
    flights_record = json.load(json_file)
icao_record = []
for flight_record in flights_record:
    icao_record.append(flight_record['icao'])

# update flight information
for flight in flights:
    if flight['icao'] in icao_record:
        flight_record = flights_record[icao_record.index(flight['icao'])]
        del flight['icao']
        for key in flight.keys():
            flight_record[key] = flight[key]
        flight_record['last_update'] = int(time.time())
    else:
        # initialize
        flight_record = {
            'icao': '',
            'callsign': '',
            'category': '',
            'alt': -1,
            'msg0': '',
            't0': -1,
            'msg1': '',
            't1': -1,
            'velocity': -1,
            'pos_update': -1,
            'position': [],
            'last_update': int(time.time()),
            'active': True
        }
        for key in flight.keys():
            flight_record[key] = flight[key]
        flights_record.append(flight_record)
        icao_record.append(flight_record['icao'])

# define reference position
my_lat = 47.3970
my_lon = 8.4560

# update flights location
for flight in flights_record:
    # only update position when new position message is received
    if flight['pos_update'] == -1:
        continue
    # for initial position
    elif not flight['position']:
        # only calculate initial position when both messages are received
        if len(flight['msg0']) == 0 or len(flight['msg1']) == 0:
            continue
        # calculate initial position
        if flight['alt'] == '0 [m]':
            flight['position'].append(pms.adsb.surface_position(flight['msg0'], flight['msg1'], flight['t0'], flight['t1'], my_lat, my_lon))
        else: # assume they are airborne
            flight['position'].append(pms.adsb.airborne_position(flight['msg0'], flight['msg1'], flight['t0'], flight['t1']))
    # for update position
    else:
        if flight['alt'] == '0 [m]':
            flight['position'].append(pms.adsb.surface_position_with_ref(flight['msg' + flight['pos_update']], flight['position'][-1][0], flight['position'][-1][1]))
        else: # assume all to be airborne
            flight['position'].append(pms.adsb.airborne_position_with_ref(flight['msg' + flight['pos_update']], flight['position'][-1][0], flight['position'][-1][1]))

# select located and active flights
flights_located = []
for flight in flights_record:
    if flight['position'] and flight['active']:
        flights_located.append(flight)

# draw located flights
m = folium.Map([my_lat, my_lon], zoom_start=11)
for flight in flights_located:
    folium.PolyLine(flight['position'], tooltip='hover_trajectory').add_to(m)
    folium.Marker(
        location=flight['position'][-1],
        tooltip=flight['icao']+'/'+flight['callsign'],
        popup=flight['category']+'/'+flight['alt']+'/'+str(flight['velocity']),
        icon=folium.Icon(icon='plane')
    ).add_to(m)
m.save('flights_located.html')

# reset pos_update to -1 and delete flights two minutes ago
for flight in flights_record:
    flight['pos_update'] = -1
    if flight['last_update'] <= time.time() - 900:
        flight['active'] = False
# save located flights
with open('flights_record.json', 'w') as f:
    json.dump(flights_record, f)
