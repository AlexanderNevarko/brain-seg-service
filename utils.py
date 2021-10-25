import os
from pathlib import Path
import subprocess
import zipfile
import shutil
import tempfile
import logging
import GPUtil
import sys
import ants
import dicom2nifti


def dicom_to_nifti(dicom_path: str, nifti_path: str, verbose=True) -> None:
    # Конвертирует dicom в nifti и сохраняет по указанному пути
    if not Path(dicom_path).is_dir():
        raise ValueError('dicom_path should be directory')

    logging.basicConfig(filename='preprocessing.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
    if verbose:
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info('dicom_to_nifti started')

    tmp_path = tempfile.mkdtemp()
    dicom2nifti.convert_directory(
        dicom_path, tmp_path, compression=True
    )
    nifti_path_tmp = os.listdir(tmp_path)[0]
    nifti_path_tmp = os.path.join(tmp_path, nifti_path_tmp)
    if Path(nifti_path).suffix == '.gz' and Path(nifti_path).with_suffix('').suffix == '.nii':
        os.replace(nifti_path_tmp, nifti_path)
    elif Path(nifti_path).suffix == '.nii':
        os.replace(nifti_path_tmp, nifti_path + '.gz')
    else:
        os.replace(nifti_path_tmp, nifti_path + '.nii.gz')
    shutil.rmtree(tmp_path)
    logging.info(f'Conversion successful; result saved to {nifti_path}')


def preprocess_nifti(src_path: str, dest_path: str, skull_mode='fast', verbose=True) -> None:
    # Препроцессит nifti файл (skullstripping и прочее) и сохраняет по указанному пути
    if skull_mode not in {'fast', 'accurate'}:
        raise ValueError('skull_mode should be in {\'fast\', \'accurate\'}')
    if Path(src_path).suffix != '.gz' or Path(src_path).with_suffix('').suffix != '.nii':
        raise ValueError('src_path should have .nii.gz extension')

    logging.basicConfig(filename='preprocessing.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
    if verbose:
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info('preprocess_nifti started')

    # Reorientation to RAS
    temp_path = tempfile.mkdtemp()
    reoriented_path = os.path.join(temp_path, str(Path(src_path).with_suffix('').with_suffix('')) + '_reor.nii.gz')
    img = ants.image_read(src_path, dimension=3)
    img_reor = ants.reorient_image2(img, orientation='RAS')
    ants.image_write(img_reor, reoriented_path)
    logging.info(f'Reorientation to RAS successful; result saved to {reoriented_path}')

    # Skull stripping
    if len(GPUtil.getAvailable()):
        device = str(GPUtil.getAvailable()[0])
    else:
        device = 'cpu'
    popen1 = subprocess.Popen(
        ['hd-bet', '-i', reoriented_path, '-device', device, '-mode', skull_mode, '-tta', '0'],
        stdout=subprocess.PIPE
    )
    logging.info(' '.join(popen1.args))
    out, err = popen1.communicate()
    _ = popen1.wait()
    stripped_path = os.path.join(temp_path, str(Path(src_path).with_suffix('').with_suffix('')) + '_reor_bet.nii.gz')

    logging.info(f'OUT: {out.decode()}')
    logging.info(f'Skull stripping successful; result saved to {stripped_path}')

    # Normalization
    fixed_path = os.path.join(temp_path, 'mni.nii.gz')
    if not os.path.isfile(fixed_path):
        logging.info('Fixed file absent in temp_path; downloading')
        popen2 = subprocess.Popen(
            ['wget', 'https://www.dropbox.com/s/qjjewijr3i7c3sc/mni.nii.gz?dl=0', '-O', os.path.abspath(fixed_path)]
        )
        _ = popen2.communicate()
        _ = popen2.wait()
    else:
        logging.info('Fixed file exists')
    fixed_img = ants.image_read(fixed_path)
    moving_img = ants.image_read(stripped_path)
    res_img = ants.registration(
        fixed_img,
        moving_img,
        type_of_transform='antsRegistrationSyNQuick[r]',
        random_seed=42
    )
    warpedmovout_path = os.path.join(temp_path, 'warpedmovout.nii.gz')
    warpedfixout_path = os.path.join(temp_path, 'warpedfixout.nii.gz')
    ants.image_write(res_img['warpedmovout'], warpedmovout_path)
    ants.image_write(res_img['warpedfixout'], warpedfixout_path)

    if Path(dest_path).suffix == '.gz' and Path(dest_path).with_suffix('').suffix == '.nii':
        os.replace(warpedfixout_path, dest_path)
    elif Path(dest_path).suffix == '.nii':
        os.replace(warpedfixout_path, dest_path + '.gz')
    else:
        os.replace(warpedfixout_path, dest_path + '.nii.gz')

    shutil.rmtree(temp_path)
    logging.info(f'Preprocessing finished; result saved to {dest_path}')
