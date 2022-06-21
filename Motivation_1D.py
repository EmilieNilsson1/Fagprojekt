#%%
# Script to show why we cannot just use a naive solution
import numpy as np
from scipy import linalg 
import matplotlib.pyplot as plt

# parameters
# no. of elements in psf array
psf_size = 10
# std of noise
noise_level = 0.005

# Creating input
x1,x2,x3,x4 = [0]*11,[1]*10,[-1]*10,[0]*10
x = np.array((x1 +x2 +x3 +x4))

# Creating PSF and Toeplitz matrix
def normd(x):
    prob_density = (np.pi) * np.exp(-0.5*((x)/1)**2)
    return prob_density

p = np.zeros(psf_size)
# array for plotting psf
p_plot = p
p[0] = normd(0)
for i in range(1,psf_size):
    p[i]=normd(0.25*i)
p *= 1/(2*np.sum(p)-p[0])
print("p is", p)
p_plot = np.append(p,np.zeros(x.size//4))
p = np.append(p,np.zeros(x.size-psf_size))
print("p is now", p)
A = linalg.toeplitz(p,p)
print(A)
print("cond of A is",np.linalg.cond(A))

# Adding noise
noise = np.random.normal(0,noise_level,size=x.size)
print("2-norm of noise is", np.linalg.norm(noise))
b_smooth = A@x
b_smooth_noise = b_smooth + noise

# Recreating input signal
x_solve = linalg.solve(A,b_smooth_noise)

print("2-norm of solution x is", np.linalg.norm(x_solve))
# Plotting results
plt.figure(0)
plt.plot(range(x.size),x)
plt.title("Input signal")

plt.figure(1)
plt.plot(range(x.size),x,label = "True signal")
plt.plot(range(b_smooth_noise.size),b_smooth_noise, label = "Blurred signal")
#plt.title("True and blurred signal", fontsize = 18)
plt.legend(loc =2, fontsize = 8)
# small plot
plt.axes([.65, .6, .2, .2])
a = plt.plot(np.append(np.flip(p_plot),p_plot),'g')
plt.axis('on')
plt.title("Point Spread Function", fontsize=8)
plt.xticks([])
plt.yticks([])
plt.savefig('1dsimple.png',dpi = 350)

plt.figure(3)
plt.plot(range(x.size),x_solve)
plt.title("Reconstructed input")
plt.savefig("bad_recon.png", dpi = 350)

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
# plots for presentation
plt.figure(4)
plt.plot(range(b_smooth_noise.size),b_smooth_noise)
plt.savefig("lesgo.png", dpi = 350)

plt.figure(5)
plt.plot(range(x.size),x_solve)
plt.title(r'$A^{-1}b$',fontname="Times New Roman",fontweight="bold")
plt.savefig("lesgo2.png", dpi = 350)

plt.figure(6)
plt.plot(range(x.size),x)
plt.title(r'$\text{x}$',fontname="Times New Roman",fontweight="bold")
plt.savefig("lesgo3.png", dpi = 350)


