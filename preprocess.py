import argparse
import os
import subprocess
import logging
import GPUtil
import sys
# import dicom2nifti
import ants


def main():
    parser = argparse.ArgumentParser('Script for *.dcm to *.nii.gz conversion')
    logging.basicConfig(filename='preprocessing.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info('Preprocessing started')
    parser.add_argument(
        '-s', '--source',
        default='dicom_dir',
        type=str,
        help='Path to source directory with DICOM files',
        required=False,
        dest='dicom_dir'
    )
    parser.add_argument(
        '-d', '--dest',
        default='output',
        type=str,
        help='Path to destination directory with intermediate and final NIFTI files',
        required=False,
        dest='dest_dir'
    )
    parser.add_argument(
        '-m', '--skullstripping',
        default='fast',
        choices=['fast', 'accurate'],
        help='Skull stripping mode',
        required=False,
        dest='skull_mode'
    )
    args = parser.parse_args()

    # DICOM to NIFTI conversion
    dicom_dir = args.dicom_dir
    dest_dir = args.dest_dir
    skull_mode = args.skull_mode
    if dicom_dir.endswith('/'):
        dicom_dir = dicom_dir[:-1]

    logging.info('dcm2niix conversion')
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)
    popen1 = subprocess.Popen(
        ['dcm2niix', '-o', f'{dest_dir}/', '-z', 'y', '-f', '%f', dicom_dir],
        stdout=subprocess.PIPE
    )
    logging.info(' '.join(popen1.args))
    popen1.wait()
    out, err = popen1.communicate()
    logging.info(f'OUT: {out.decode()}')
    # logging.info(f'ERR: {err}')

    logging.info('Reorientation & skull stripping')
    nii_path = os.path.join(dest_dir, f'{dicom_dir}.nii.gz')
    nii_reor_path = os.path.join(dest_dir, f'{dicom_dir}_reor.nii.gz')
    img = ants.image_read(nii_path, dimension=3)
    img_reor = ants.reorient_image2(img, orientation='RAS')
    ants.image_write(img_reor, nii_reor_path)
    logging.info(f'Reoriented image written to {nii_reor_path}')

    ants.image_write(img_reor, nii_reor_path)
    if len(GPUtil.getAvailable()):
        device = '0'
    else:
        device = 'cpu'
    popen2 = subprocess.Popen(
        ['hd-bet', '-i', nii_reor_path, '-device', device, '-mode', skull_mode, '-tta', '0'],
        stdout=subprocess.PIPE
    )
    logging.info(' '.join(popen2.args))
    popen2.wait()
    out, err = popen2.communicate()
    logging.info(f'OUT: {out.decode()}')
    # logging.info(f'ERR: {err}')
    nii_stripped_path = os.path.join(dest_dir, f'{dicom_dir}_reor_bet.nii.gz')

    logging.info('Normalization')
    fixed_path = os.path.join(dest_dir, 'mni.nii.gz')
    if not os.path.isfile(fixed_path):
        logging.info('Fixed file absent in dest dir; downloading')
        popen3 = subprocess.Popen(
            ['wget', 'https://www.dropbox.com/s/qjjewijr3i7c3sc/mni.nii.gz?dl=0', '-O', os.path.abspath(fixed_path)]
        )
        popen3.wait()
        popen3.communicate()
        # urlretrieve('https://www.dropbox.com/s/qjjewijr3i7c3sc/mni.nii.gz?dl=0', os.path.abspath(fixed_path))
    else:
        logging.info('Fixed file exists')
    fixed_img = ants.image_read(fixed_path)
    moving_img = ants.image_read(nii_stripped_path)
    res_img = ants.registration(
        fixed_img,
        moving_img,
        type_of_transform='antsRegistrationSyNQuick[r]',
        random_seed=42
    )
    warpedmovout_path = os.path.join(dest_dir, 'warpedmovout.nii.gz')
    warpedfixout_path = os.path.join(dest_dir, 'warpedfixout.nii.gz')
    ants.image_write(res_img['warpedmovout'], warpedmovout_path)
    ants.image_write(res_img['warpedfixout'], warpedfixout_path)
    logging.info(f'Preprocessing finished; result written to {warpedfixout_path}')


if __name__ == '__main__':
    main()

