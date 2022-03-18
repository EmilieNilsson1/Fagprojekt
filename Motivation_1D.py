#%%
# Script to show why we cannot just use a naive solution
import numpy as np
from scipy import linalg 
import matplotlib.pyplot as plt

# parameters
psf_size = 10
noise_level = 0.01

# Creating input
x1,x2,x3,x4 = [0]*11,[1]*10,[-1]*10,[0]*10
x = np.array((x1 +x2 +x3 +x4))

# Creating PSF and Toeplitz matrix
def normd(x):
    prob_density = (np.pi) * np.exp(-0.5*((x)/1)**2)
    return prob_density

p = np.zeros(psf_size)
p[0] = normd(0)
for i in range(1,psf_size):
    p[i]=normd(0.25*i)
p *= 1/(np.sum(p))

p = np.append(p,np.zeros(x.size-psf_size))
A = linalg.toeplitz(p,p)
print("cond of A is",np.linalg.cond(A))

# Adding noise
noise = noise_level*np.random.rand(x.size)
b_smooth = A@x
b_smooth += noise

# Recreating input signal
x_solve = linalg.solve(A,b_smooth)

# Plotting results
plt.figure(0)
plt.plot(range(x.size),x)
plt.title("Input signal")

plt.figure(1)
plt.plot(range(x.size),x)
plt.plot(range(b_smooth.size),b_smooth)
plt.title("Input + blurred input")

plt.figure(2)
plt.plot(range(x.size),x_solve)
plt.title("Reconstructed input")

# Maybe wanted to do some subplots
# fig, sub = plt.subplots(3)
# sub[0].plot(range(x.size),x)
# sub[0].set_title("Input signal")
# sub[1].plot(range(x.size),x)
# sub[1].plot(range(x.size),b_smooth)
# sub[1].set_title("Input + blurred input")
# sub[2].plot(range(x.size),x_solve)
# sub[2].set_title("Reconstructed input signal")
# %%
