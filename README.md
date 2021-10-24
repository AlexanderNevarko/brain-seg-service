# brain-seg-service
Project for Neuroimaging and Machine Learning in Biomedicine course at Skoltech.

``preprocess.py``: script for ``*.dcm`` files preprocessing:
1) Conversion from  ``*.dcm`` to ``*.nii.gz`` with ``dcm2niix``
2) ``HD-BET`` for skull stripping
3) ``ANTsPy`` for normalisation 

usage: ``python preprocess.py [-h] [-s DICOM_DIR]
                                               [-d DEST_DIR]
                                               [-m {fast,accurate}]``

optional arguments:


  ``-s DICOM_DIR, --source DICOM_DIR
                        Path to source directory with DICOM files``

  ``-d DEST_DIR, --dest DEST_DIR
                        Path to destination directory with intermediate and final NIFTI files``

  ``-m {fast,accurate}, --skullstripping {fast,accurate}
                        Skull stripping mode``

Resulting file is stored at path ``DEST_DIR/'warpedfixout.nii.gz`` in working directory