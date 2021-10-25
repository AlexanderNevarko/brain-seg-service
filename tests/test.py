from utils import dicom_to_nifti, preprocess_nifti


def test_init():
    try:
        dicom_to_nifti('SE000001', 'initial.nii.gz')
        preprocess_nifti('initial.nii.gz', 'final.nii.gz')
    except Exception as e:
        return e
    return 'Sucess'


def main():
    print(f'Init test: {test_init()}')

if __name__ == '__main__':
    main()
