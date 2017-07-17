import os
import time
#import cPickle
import datetime
import logging
import flask
import werkzeug
import optparse
import tornado.wsgi
import tornado.httpserver
import numpy as np
import pandas as pd
from PIL import Image
#import cStringIO as StringIO
from io import StringIO
import urllib

import ammartask

REPO_DIRNAME = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
HTML_FOLDER = 'http://127.0.0.1:8000/AMM_Uploads/'
UPLOAD_FOLDER = os.path.join(REPO_DIRNAME, 'AMM_Uploads')
ALLOWED_HTML_EXTENSIONS = set(['htm','html'])

#print (REPO_DIRNAME)

# Obtain the flask app object
app = flask.Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return flask.render_template('index.html', has_result=False)

@app.route('/convert_url', methods=['GET'])
def convert_url():
    ammurl = flask.request.args.get('ammurl', '')
    try:
        #string_buffer = StringIO(
        #    urllib.request.urlopen(ammurl).read())
        #image = caffe.io.load_image(string_buffer)
        html = urllib.request.urlopen(ammurl)
        app.clf.input_file = ammurl

    except Exception as err:
        # For any exception we encounter in reading the image, we will just
        # not continue.
        logging.info('URL AMM open error: %s', err)
        return flask.render_template(
            'index.html', has_result=True,
            result=(False, 'Cannot open AMM from URL.')
        )

    logging.info('AMM: %s', ammurl)
    result = app.clf.getTasks()
    return flask.render_template(
        'index.html', has_result=True, result=result, ammsrc=ammurl.replace(' ','%20'))


@app.route('/convert_upload', methods=['POST'])
def convert_upload():
    try:
        # We will save the file to disk for possible data collection.
        ammfile = flask.request.files['ammfile']
        print(ammfile)
        filename_ = str(datetime.datetime.now()).replace(' ', '_').replace(':','') + \
            werkzeug.secure_filename(ammfile.filename)
        print(filename_)
        filename = os.path.join(UPLOAD_FOLDER, filename_)
        print(filename)
        ammfile.save(filename)
        print("save")
        logging.info('Saving to %s.', filename)
        app.clf.input_file = filename
        #image = exifutil.open_oriented_im(filename)

    except Exception as err:
        logging.info('Uploaded AMM open error: %s', err)
        return flask.render_template(
            'index.html', has_result=True,
            result=(False, 'Cannot open uploaded AMM.')
        )

    result = app.clf.getTasks()
    return flask.render_template(
        'index.html', has_result=True, result=result,
        ammsrc=HTML_FOLDER+filename_
    )

def allowed_file(filename):
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1] in ALLOWED_HTML_EXTENSIONS
    )

def start_tornado(app, port=5000):
    http_server = tornado.httpserver.HTTPServer(
        tornado.wsgi.WSGIContainer(app))
    http_server.listen(port)
    print("Tornado server starting on port {}".format(port))
    tornado.ioloop.IOLoop.instance().start()

class AMMARTaskConvertor(object):
    default_args = {
        'input_file' : ('{}/A330 Wheel.htm'.format(REPO_DIRNAME)),
        'output_file' : ('{}/amm-artask.txt'.format(REPO_DIRNAME)),
        'create_individual_task_output' : False
    }
    for key, val in default_args.items():
        if not os.path.exists(val):
            raise Exception(
                "File for {} is missing. Should be at: {}".format(key, val))

    def __init__(self, input_file, output_file, create_individual_task_output):
        self.input_file = input_file
        self.output_file = output_file
        self.create_individual_task_output = create_individual_task_output

    def getTasks(self):
        try: 
            starttime = time.time()
            self.tasks =  ammartask.getTasks(self.input_file,self.output_file,self.create_individual_task_output)
            endtime = time.time()
            return (True, self.tasks, '%.3f' % (endtime - starttime))
        except Exception as err:
            logging.info('Conversion error: %s', err)
            return (False, 'Something went wrong when converting the '
                           'AMM. Maybe try another one?')


def start_from_terminal(app):
    """
    Parse command line options and start the server.
    """
    parser = optparse.OptionParser()
    parser.add_option(
        '-d', '--debug',
        help="enable debug mode",
        action="store_true", default=False)
    parser.add_option(
        '-p', '--port',
        help="which port to serve content on",
        type='int', default=5000)

    opts, args = parser.parse_args()

    # Initialize classifier + warm start by forward for allocation
    app.clf = AMMARTaskConvertor(**AMMARTaskConvertor.default_args)
    #app.clf.getTasks();

    if opts.debug:
        app.run(debug=True, host='127.0.0.1', port=opts.port)
    else:
        start_tornado(app, opts.port)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    start_from_terminal(app)