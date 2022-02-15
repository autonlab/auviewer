export default class Fetcher {
    static requestInitialEvaluatorPayload (project_id: number, callback: (data: any) => void) {
        Fetcher._makeRequest(callback, 'initial_evaluator_payload', {
            project_id: project_id,
        });
    }

    static requestPossibleLabelers(project_id: number, callback: (data: any) => void) {
        Fetcher._makeRequest(callback, 'get_labelers', {
            project_id: project_id,
        });
    }

    static requestPossibleLabels(project_id: number, callback: (data: any) => void) {
        Fetcher._makeRequest(callback, 'get_labels', {
            project_id: project_id,
        });
    }

    static createAnnotation = function(project_id: number, file_id: number, left: number, right: number, series_id: string, label: string, pattern_id: number | undefined, callback: (data: any) => void) {
        Fetcher._makeRequest(callback, 'create_annotation', {
            project_id: project_id,
            file_id: file_id,
            xl: left,
            xr: right,
            /*yt: ,
            yb: ,*/
            sid: series_id,
            label: label,
            pattern_id: pattern_id
        });
    }



    private static _makeRequest (callback: (data: any) => void, url: string, pathParams: object) {
        console.log(pathParams);
        // Instantiate a new HTTP request object
        const req = new XMLHttpRequest();
        req.onreadystatechange = Fetcher._callbackCaller(callback);

        const path: string = Fetcher._buildPathWithParams(url, pathParams);
        console.log(path);
        req.open("GET", path, true);
        req.send();
    }

    private static _callbackCaller (callback: (data: any) => void) : () => void {
        return function() {
            /* @ts-ignore */
            if (this.readyState === 4 && this.status === 200) {

                // JSON-decode the response
                let data = {};
                /* @ts-ignore */
                if (this.responseText.length > 0) {
                    /* @ts-ignore */
                    data = JSON.parse(this.responseText);
                }


                // Call the callback with data
                if (typeof callback === 'function') {
                    const t0 = performance.now();
                    callback(data);
                    const tt = performance.now() - t0;
                } else {
                    console.log("Important: Callback not provided to request handler.");
                }

            }
        }

    }

    private static _buildPathWithParams (path: string, params: any) : string {
        // Assemble the parameters on the path
        const keys = Object.keys(params);
        for (let i = 0; i < keys.length; i++) {
            if (i === 0) {
                path += '?';
            } else {
                path += '&';
            }
            if (params[keys[i]] != null && params[keys[i]].constructor === Array) {
                for (let j = 0; j < params[keys[i]].length; j++) {
                    if (j !== 0) {
                        path += '&';
                    }
                    path += keys[i]+ '[]=' + encodeURIComponent(params[keys[i]][j]);
                }
            } else if (params[keys[i]] || params[keys[i]] === 0) {
                path += keys[i] + '=' + encodeURIComponent(params[keys[i]]);
            } else {
                path += keys[i] + '='
            }
        }

        return path;
    }
    

}