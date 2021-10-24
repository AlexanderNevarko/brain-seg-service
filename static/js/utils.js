function isSubmitReady() {
  const selectedValue = document.getElementById("model-select").value;
  var modelReady = false;
  if (selectedValue === "user's model") {
    modelReady = document.getElementById("model-upload").value.length > 0;
  } else {
    modelReady = true;
  }
  const dataReady = document.getElementById("data-upload").value.length > 0;
  return modelReady && dataReady;
}

function onFileUpload(uploadElem) {
  const readyToSubmit = isSubmitReady();
  document.getElementById("submit").disabled = !readyToSubmit;
  document.getElementById("hint").style.display = readyToSubmit ? "none" : "block";
  uploadElem.style.backgroundColor = "#eaf8ea";
  uploadElem.style.borderColor = "#42b40090";
}

function onSelectChange() {
  const readyToSubmit = isSubmitReady();
  document.getElementById("submit").disabled = !readyToSubmit;
  document.getElementById("hint").style.display = readyToSubmit ? "none" : "block";
  const selectedValue = document.getElementById("model-select").value;
  document.getElementById("model-upload").style.display =
    selectedValue === "user's model" ? "block" : "none";
}
