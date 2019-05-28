from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import datetime
import medfile

# Assemble a sample output for the file
#output = dh.assembleOutput()
print("Unpickling output.h5")
mf = medfile.File.unpickle('output.h5')
if not mf:
    print("Unpickling failed.")
    mf = medfile.File('output.h5')
    mf.prepareAllNumericSeries()
    # mf.prepareSeries('numeric', 'ECG.I')
    # mf.prepareSeries('numeric', 'HR')
    # mf.prepareSeries('numeric', 'RR')

else:
    print("Unpickled successfully.")
    # mf.numericSeries[0].downsampleSet.build(None)
    # mf.numericSeries[1].downsampleSet.build(None)
    # mf.numericSeries[2].downsampleSet.build(None)

HOST = 'localhost'
PORT_NUMBER = 8003

class Server(BaseHTTPRequestHandler):
    def do_HEAD(self):
        return

    def do_GET(self):

        query_components = parse_qs(urlparse(self.path).query)

        if len(query_components) == 2:

            # Parse the start & stop times
            start = datetime.datetime.fromtimestamp(float(query_components['start'][0])/1000)
            stop = datetime.datetime.fromtimestamp(float(query_components['stop'][0])/1000)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(mf.getRangedOutput(start, stop), "UTF-8"))

        else:

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(mf.getFullOutput(), "UTF-8"))

    def do_POST(self):
        return

httpd = HTTPServer((HOST, PORT_NUMBER), Server)

try:

    print("Starting HTTP server on "+str(HOST)+":"+str(PORT_NUMBER)+".")
    httpd.serve_forever()

except:# KeyboardInterrupt:

    print("HTTP server stopped.")
    print("Pickling.")
    mf.pickle()
    print("Done pickling.")

httpd.server_close()
