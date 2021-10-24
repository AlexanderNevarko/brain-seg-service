from datetime import datetime
import os
from flask import Flask
from flask import render_template
import random
import string
import shutil
from flask import Flask, flash, request, redirect, url_for
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from utils import *
import atexit

RUNS_FOLDER = "runs/"
DEFAULT_MODEL_PATH = "static/models/model.pkl"
ALLOWED_DATA_EXTENSIONS = {"png"}
ALLOWED_MODEL_EXTENSIONS = {"png"}

app = Flask(__name__)
app.config["RUNS_FOLDER"] = RUNS_FOLDER
app.config["DEFAULT_MODEL_PATH"] = DEFAULT_MODEL_PATH


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data, model = request.files["data-upload"], request.files["model-upload"]
        if type(data) == FileStorage:
            data = [data]
        use_default_model = (
            request.form.get(
                "model-select", "default model") == "default model"
        )
        data_ready = check_files(data, ALLOWED_DATA_EXTENSIONS)
        if not use_default_model:
            model_ready = check_file(
                request.files["model-upload"], ALLOWED_MODEL_EXTENSIONS
            )
        else:
            model_ready = True
        if not (data_ready and model_ready):
            return render_template(
                "index.html",
                **{
                    error_arg: "Wrong file format."
                    for ready, error_arg in [
                        (model_ready, "modelError"),
                        (data_ready, "dataError"),
                    ]
                    if not ready
                }
            )

        run = Run(app)
        run.add_data(data)
        run.add_model(model, use_default_model)

        # run.do_stuff()
        run.cleanup()
        return render_template("index.html", success="Success")

    return render_template("index.html")
