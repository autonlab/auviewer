from flask import Flask
from flask_socketio import SocketIO
from file import File

# Instantiate a file
f = File(None)

app = Flask(__name__, static_folder='/zfsauton2/home/gwelter/code/medview/rtserver/')
app.config['SECRET_KEY'] = 'secret!'
app.config['SERVER_NAME'] = 'localhost:8001'

socketio = SocketIO(app)

@socketio.on('json')
def handle_json(json):
    print('received: json')
    print('type', type(json))
    print('json msg inc:', json)
    
@socketio.on('add_data')
def handle_add_data(json):

    print('received: add_data')
    print('msg inc:', json)

    try:
        f.addSeriesData(json)

    except Exeption as e:
        # TODO(gus): Report an error in a websocket response
        pass
    
@app.route('/')
def root():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    socketio.run(app)