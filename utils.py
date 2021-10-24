import string
import os
import random
from werkzeug.utils import secure_filename
from datetime import datetime
import shutil


def randomify_string(s):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(5))
    return f"{s}_{datetime.now().strftime('%d-%m-%Y-%H:%M:%S')}_{result_str}"


def is_file_allowed(filename, allowed_extension_list):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extension_list


def check_file(file, allowed_extension_list):
    return is_file_allowed(file.filename, allowed_extension_list)


def check_files(files, allowed_extension_list):
    statuses = list(map(lambda file: check_file(
        file, allowed_extension_list), files))
    return all(statuses)


class Run():
    def __init__(self, app):
        self.dir = os.path.join(
            app.config['RUNS_FOLDER'], randomify_string('run'))
        self.data_dir = os.path.join(self.dir, 'data')
        self.model_dir = os.path.join(self.dir, 'model')
        self.model_path = app.config['DEFAULT_MODEL_PATH']
        os.mkdir(self.dir)
        os.mkdir(self.data_dir)
        os.mkdir(self.model_dir)

    def cleanup(self):
        print("Running cleanup...")
        shutil.rmtree(self.dir)

    def add_model(self, model, use_default_model):
        if not use_default_model:
            self.model_path = os.path.join(
                self.model_dir, secure_filename(model.filename))
            model.save(self.model_path)

    def add_data(self, data):
        self.data_paths = []
        for i, datafile in enumerate(data):
            self.data_paths.append(os.path.join(
                self.data_dir, secure_filename(datafile.filename)))
            datafile.save(self.data_paths[-1])
