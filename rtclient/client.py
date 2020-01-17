import math
import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print("I'm connected!")
    print('my sid is', sio.sid)

@sio.event
def connect_error():
    print("The connection failed!")

@sio.event
def disconnect():
    print("I'm disconnected!")

@sio.event
def message(data):
    print('received msg', data)

sio.connect('http://localhost:8001')

# # Send new data to server
# sio.emit('add_data', {
#     'Sample': {
#         'times': [5, 10, 15, 20],
#         'values': [99.2, 98.5, 97.6, 94]
#     },
#     'HR.HR': {
#         'times': [7, 9, 12, 16],
#         'values': [85, 91, 99, 120]
#     }
# })

n = 0

# Oscillations per second
f = 2.5;

# Time interval in seconds
interval = 0.1

# Amplitude
a = 1

while True:

    t = n * interval

    # sio.emit('add_data', {
    #     'Sample': {
    #         'times': [
    #             t,
    #             t+(1/5*interval),
    #             t+(2/5*interval),
    #             t+(3/5*interval),
    #             t+(4/5*interval)
    #         ],
    #         'values': [
    #             a*math.sin(f*t),
    #             a*math.sin(f*(t+(1/5*interval))),
    #             a*math.sin(f*(t+(2/5*interval))),
    #             a*math.sin(f*(t+(3/5*interval))),
    #             a*math.sin(f*(t+(4/5*interval)))
    #         ]
    #     }
    # })

    sio.emit('add_data', {
        'Signal 1': {
            'times': [
                t,
                t + (1 / 5 * interval),
                t + (2 / 5 * interval),
                t + (3 / 5 * interval),
                t + (4 / 5 * interval)
            ],
            'values': [
                a * math.sin(f * t),
                a * math.sin(f * (t + (1 / 5 * interval))),
                a * math.sin(f * (t + (2 / 5 * interval))),
                a * math.sin(f * (t + (3 / 5 * interval))),
                a * math.sin(f * (t + (4 / 5 * interval)))
            ]
        },
        'Signal 2': {
            'times': [
                t,
                t + (1 / 2 * interval)#,
                # t + (2 / 5 * interval),
                # t + (3 / 5 * interval),
                # t + (4 / 5 * interval)
            ],
            'values': [
                a * math.sin(f/2 * t),
                a * math.sin(f/2 * (t + (1 / 2 * interval)))#,
                # a * math.sin(f*1.2 * (t + (2 / 5 * interval))),
                # a * math.sin(f*1.2 * (t + (3 / 5 * interval))),
                # a * math.sin(f*1.2 * (t + (4 / 5 * interval)))
            ]
        },
        'Signal 3': {
            'times': [
                t,
                t + (1 / 4 * interval),
                t + (2 / 4 * interval),
                t + (3 / 4 * interval)
            ],
            'values': [
                a * math.sin(f*1.4 * t),
                a * math.sin(f*1.4 * (t + (1 / 4 * interval))),
                a * math.sin(f*1.4 * (t + (2 / 4 * interval))),
                a * math.sin(f*1.4 * (t + (3 / 4 * interval)))
            ]
        },
        'Signal 4': {
            'times': [
                t,
                t + (1 / 5 * interval),
                t + (2 / 5 * interval),
                t + (3 / 5 * interval),
                t + (4 / 5 * interval)
            ],
            'values': [
                a * math.sin(f * t),
                a * math.sin(f * (t + (1 / 5 * interval))),
                a * math.sin(f * (t + (2 / 5 * interval))),
                a * math.sin(f * (t + (3 / 5 * interval))),
                a * math.sin(f * (t + (4 / 5 * interval)))
            ]
        },
        'Signal 5': {
            'times': [
                t,
                t + (1 / 2 * interval)  # ,
                # t + (2 / 5 * interval),
                # t + (3 / 5 * interval),
                # t + (4 / 5 * interval)
            ],
            'values': [
                a * math.sin(f / 2 * t),
                a * math.sin(f / 2 * (t + (1 / 2 * interval)))  # ,
                # a * math.sin(f*1.2 * (t + (2 / 5 * interval))),
                # a * math.sin(f*1.2 * (t + (3 / 5 * interval))),
                # a * math.sin(f*1.2 * (t + (4 / 5 * interval)))
            ]
        },
        'Signal 6': {
            'times': [
                t,
                t + (1 / 4 * interval),
                t + (2 / 4 * interval),
                t + (3 / 4 * interval)
            ],
            'values': [
                a * math.sin(f * 1.4 * t),
                a * math.sin(f * 1.4 * (t + (1 / 4 * interval))),
                a * math.sin(f * 1.4 * (t + (2 / 4 * interval))),
                a * math.sin(f * 1.4 * (t + (3 / 4 * interval)))
            ]
        },
        'Signal 7': {
            'times': [
                t,
                t + (1 / 5 * interval),
                t + (2 / 5 * interval),
                t + (3 / 5 * interval),
                t + (4 / 5 * interval)
            ],
            'values': [
                a * math.sin(f * t),
                a * math.sin(f * (t + (1 / 5 * interval))),
                a * math.sin(f * (t + (2 / 5 * interval))),
                a * math.sin(f * (t + (3 / 5 * interval))),
                a * math.sin(f * (t + (4 / 5 * interval)))
            ]
        },
        'Signal 8': {
            'times': [
                t,
                t + (1 / 2 * interval)  # ,
                # t + (2 / 5 * interval),
                # t + (3 / 5 * interval),
                # t + (4 / 5 * interval)
            ],
            'values': [
                a * math.sin(f / 2 * t),
                a * math.sin(f / 2 * (t + (1 / 2 * interval)))  # ,
                # a * math.sin(f*1.2 * (t + (2 / 5 * interval))),
                # a * math.sin(f*1.2 * (t + (3 / 5 * interval))),
                # a * math.sin(f*1.2 * (t + (4 / 5 * interval)))
            ]
        },
        'Signal 9': {
            'times': [
                t,
                t + (1 / 4 * interval),
                t + (2 / 4 * interval),
                t + (3 / 4 * interval)
            ],
            'values': [
                a * math.sin(f * 1.4 * t),
                a * math.sin(f * 1.4 * (t + (1 / 4 * interval))),
                a * math.sin(f * 1.4 * (t + (2 / 4 * interval))),
                a * math.sin(f * 1.4 * (t + (3 / 4 * interval)))
            ]
        },

    })

    n = n + 1

    time.sleep(interval)
    #input("Press enter for next...")