import math
import socketio
import time

def main():
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

    @sio.event
    def push_template(data):
        print('rcvd push_template', data)

    sio.connect('http://localhost:8001')

    # sio.emit('add_annotations', [
    #     [123, 'something']
    #     ])

    ###############################################
    # add ability to zoom, concept of a reset
    # add ability to define buffer size in # of points or length of time
    # demarcation adding those as a data set like the rest

    while True:

        # Prompt user to choose
        choice = input("Type 'r' to send realtime sample data, 't' to send sample template signals, 'q' to quit: ")

        if choice == 't':

            sio.emit('push_template', {

                # Optional
                'project': 'ConditionC',

                # Optional
                'interface': '',

                # Template may be:
                #   - object (will be jsonified by server), or
                #   - string (server will assume it's already jsonified).
                'template': {
                    "series": {
                        "numerics/HR.HR/data": {
                            "color": "blue"
                        }
                    }
                }
            })

            print("Sent a push template.")

        elif choice == 'r':

            print("Sending realtime data...")

            f = 2.5 # Oscillations per second
            interval = 0.1 # Time interval in seconds
            a = 1 # Amplitude
            n = 0 # Loop iteration

            while True:

                t = n * interval

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
                            t + (1 / 2 * interval)
                        ],
                        'values': [
                            a * math.sin(f/2 * t),
                            a * math.sin(f/2 * (t + (1 / 2 * interval)))
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
                            t + (1 / 2 * interval)
                        ],
                        'values': [
                            a * math.sin(f / 2 * t),
                            a * math.sin(f / 2 * (t + (1 / 2 * interval)))
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
                            t + (1 / 2 * interval)
                        ],
                        'values': [
                            a * math.sin(f / 2 * t),
                            a * math.sin(f / 2 * (t + (1 / 2 * interval)))
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
                # input("Press enter for next...")

        elif choice == 'q':
            quit()

if __name__ == '__main__':
    main()
