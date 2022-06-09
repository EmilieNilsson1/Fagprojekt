#%%
import numpy as np
import scipy.stats as sps
import matplotlib.pyplot as plt

#%%
# making pdfs
x_i_diff = np.linspace(-4,4,1000)

prob_l = sps.laplace.pdf(x_i_diff)

prob_c = sps.cauchy.pdf(x_i_diff)

prob_g = sps.norm.pdf(x_i_diff)

prob_u = sps.uniform.pdf(x_i_diff)

plt.plot(x_i_diff,prob_g, label = "Gauss")
#plt.xlabel("$x$")
#plt.ylabel("Gauss pdf")
#plt.savefig("Gauss1D", dpi = 350)

plt.plot(x_i_diff, prob_l, label = "Laplace")
# #plt.xlabel("$x_{i}-x_{i+1}$")
# #plt.ylabel("Laplace pdf")
#plt.legend(loc =2, fontsize = 10)
#plt.savefig("Laplace1D", dpi = 350)

plt.plot(x_i_diff, prob_c, label = "Cauchy")
# plt.xlabel("$x_{i}-x_{i+1}$")
# #plt.ylabel("Cauchy pdf")
#plt.legend(loc =2, fontsize = 10)
#plt.savefig("Cauchy1D", dpi = 350)

#%%
# generating random walks with laplace and cauchy
np.random.seed(235424)
n = 1000
d_l = np.random.laplace(scale=1,size=n)
d_g = np.random.normal(scale=1,loc=0,size=n)
#d_c = np.random.standard_cauchy(size = n)
d_c = sps.cauchy.rvs(size=n,scale=0.3)
x_l = np.zeros(n)
x_c = np.zeros(n)
x_g = np.zeros(n)
for i in range(n):
    x_l[i] = x_l[i-1] + d_l[i-1]
    x_c[i] = x_c[i-1] + d_c[i-1]
    x_g[i] = x_g[i-1] + d_g[i-1]

#plt.plot(x_c)
plt.figure()
plt.plot(x_l, label = "Laplace")
plt.plot(x_g, label = "Cauchy")
#plt.savefig("Laplace_Randomwalk", dpi = 350)
plt.legend(loc =2, fontsize = 10)
plt.savefig("Cauchy_Randomwalk", dpi = 350)

# %%
