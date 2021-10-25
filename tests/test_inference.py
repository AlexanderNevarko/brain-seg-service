from model.inference import Model


def test_init():
    try:
        model = Model('storage/pretrained/entire_model.pth')
    except Exception as e:
        return e
    return 'Success'


def main():
    print(f'Init test: {test_init()}')
    
    
if __name__ == '__main__':
    main()