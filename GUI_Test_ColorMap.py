# %%
from matplotlib import pyplot as plt
import numpy as np
from matplotlib import cm
from PIL import Image
from PIL import ImageOps
import os
import cuqi
import sys
import scipy
sys.path.append("..")

phantom = cuqi.data.satellite(size=128)
TP = cuqi.testproblem.Deconvolution2D(dim=128, phantom=phantom)
TP.prior = cuqi.distribution.Laplace_diff(
    location=np.zeros(TP.model.domain_dim),
    scale=0.01,
    physical_dim=2 # Indicates that the prior should be in 2D.
)
samples = TP.sample_posterior(200)
#%%
A = samples.samples
std = np.reshape(np.std(A,axis=-1),(-1,128))
mean = np.reshape(np.mean(A,axis=-1),(-1,128))
RED = np.zeros((128,128))
std_stand = std/np.max(std)
plt.imshow(mean, cmap = 'gray')
plt.imshow(RED,cmap='autumn', alpha = std_stand)



# %%
