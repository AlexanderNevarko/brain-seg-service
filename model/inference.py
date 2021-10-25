import os
import torch
import torchio
import numpy as np
import nibabel
import matplotlib.pyplot as plt

from torch.utils.data import DataLoader
from torchio import AFFINE, DATA, PATH, TYPE, STEM
from torchio.transforms import HistogramStandardization



class Model():
    def __init__(self, model_path, storage_path):
        self.device = torch.device('cuda:7') if torch.cuda.is_available() else torch.device('cpu')
        
        try:
            self.model = torch.load(model_path, map_location=self.device)
        except Exception as e:
            print(e)
            return e
        
        self.model.eval()
        self.model.to(self.device)
        self.MRI = 'MRI'
        self.storage_path = storage_path
    
    
    def read_nifty(self, img_path, transform=None):
        """
        The function creates dataset from the list of files from cunstumised dataloader.
        """
        
        subject_dict = {
            self.MRI : torchio.Image(img_path, torchio.INTENSITY)
        }
        subject = [torchio.Subject(subject_dict)]
        if transform is not None:
            dataset = torchio.SubjectsDataset(subject, transform=transform)
        else:
            dataset = torchio.SubjectsDataset(subject)
        
        patches_set = torchio.Queue(
            subjects_dataset=dataset,
            max_length=240,
            samples_per_volume=8,
            sampler=torchio.sampler.UniformSampler(64),
            shuffle_subjects=False,
            shuffle_patches=False,
        )
        dataloader = DataLoader(patches_set, 
                                batch_size=4, 
                                shuffle=False)
        
        return dataset, subject, dataloader
    
    
    def predict(self, img_path):
        # landmarks = {'MRI': os.path.join(self.storage_path, 'pretrained', 'test_landmarks.npy')}
        
        transform = None #HistogramStandardization(landmarks)
        ds, _, _ = self.read_nifty(img_path, transform)
        sample = ds[0]
        grid_sampler = torchio.inference.GridSampler(
            sample,
            patch_size=64,
            patch_overlap=20,
        )
        patch_loader = DataLoader(
            grid_sampler, batch_size=4)     
        aggregator = torchio.inference.GridAggregator(grid_sampler)
        
        self.model.eval()
        with torch.no_grad():
            for patches_batch in patch_loader:
                inputs = patches_batch[self.MRI][DATA].to(self.device)
                locations = patches_batch['location']
                logits = self.model(inputs.float())
                labels = logits.argmax(dim=1, keepdims=True)
                aggregator.add_batch(labels, locations)
            
            predictions = aggregator.get_output_tensor()
        return predictions.detach().cpu()
    
    @staticmethod
    def plot_cuts(path_to_save, results, img_size=8):
        '''
        path_to_save: path to save cuts image
        results: resulting prediction tensor from model
        img_size: size of image to plot
        '''
        img = results
        if isinstance(img, torch.Tensor):
            img = img.numpy()
            if (len(img.shape) > 3):
                img = img[0,:,:,:]
        elif isinstance(img, nibabel.nifti1.Nifti1Image):    
            img = img.get_fdata()
        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(3 * img_size, img_size))
        axes[0].imshow(img[ img.shape[0] // 2, :, :])
        axes[1].imshow(img[ :, img.shape[1] // 2, :])
        axes[2].imshow(img[ :, :, img.shape[2] // 2])
        plt.savefig(path_to_save)
            
        
            