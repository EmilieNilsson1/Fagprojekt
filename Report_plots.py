#%%
import numpy as np
import scipy.stats as sps
import matplotlib.pyplot as plt
import cuqi

#%%
# making pdfs
x_i_diff = np.linspace(-1,2,1000)

prob_l = sps.laplace.pdf(x_i_diff)

prob_c = sps.cauchy.pdf(x_i_diff)

prob_g = sps.norm.pdf(x_i_diff)

prob_u = sps.uniform.pdf(x_i_diff, loc=-1, scale=2)

prob_u = sps.uniform.pdf(x_i_diff)

# plt.plot(x_i_diff,prob_g, label = "Gauss")
#plt.xlabel("$x$")
#plt.ylabel("Gauss pdf")
#plt.savefig("Gauss1D", dpi = 350)

# plt.plot(x_i_diff, prob_l, label = "Laplace")
# #plt.xlabel("$x_{i}-x_{i+1}$")
# #plt.ylabel("Laplace pdf")
#plt.legend(loc =2, fontsize = 10)
#plt.savefig("Laplace1D", dpi = 350)

# plt.plot(x_i_diff, prob_c, label = "Cauchy")
# plt.xlabel("$x_{i}-x_{i+1}$")
# #plt.ylabel("Cauchy pdf")
#plt.legend(loc =2, fontsize = 10)
#plt.savefig("Cauchy1D", dpi = 350)

plt.plot(x_i_diff, prob_u)
plt.savefig("Unif1D", dpi = 350)


#%%
# generating random walks with laplace and cauchy
np.random.seed(24424)
n = 500
d_l = np.random.laplace(scale=0.3,loc=0,size=n)
d_g = np.random.normal(scale=0.3,loc=0,size=n)
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
plt.savefig("Laplace_Randomwalk", dpi = 350)
plt.figure()
plt.plot(x_c, label = "Cauchy")
plt.savefig("Cauchy_Randomwalk", dpi = 350)
#plt.savefig("Laplace_Randomwalk", dpi = 350)
#plt.legend(loc =2, fontsize = 10)


#%%

n = 128*128
prior1 = cuqi.distribution.GMRF(np.zeros(n),prec=0.1,order=0,physical_dim=2)
prior2 = cuqi.distribution.GMRF(np.zeros(n),prec=0.1,order=1,physical_dim=2)
prior3 = cuqi.distribution.GMRF(np.zeros(n),prec=0.1,order=2,physical_dim=2)
prior4 = cuqi.distribution.GMRF(np.zeros(n),prec=10,order=0,physical_dim=2)
prior5 = cuqi.distribution.GMRF(np.zeros(n),prec=10,order=1,physical_dim=2)
prior6 = cuqi.distribution.GMRF(np.zeros(n),prec=10,order=2,physical_dim=2)

plt.figure()
prior1.sample().plot()
print(max(prior1.sample()))
plt.savefig("GMRF1.png",dpi=350)

plt.figure()
prior2.sample().plot()
print(max(prior2.sample()))
plt.savefig("GMRF2.png",dpi=350)

plt.figure()
prior3.sample().plot()
print(max(prior3.sample()))
plt.savefig("GMRF3.png",dpi=350)

plt.figure()
prior4.sample().plot()
print(max(prior4.sample()))
plt.savefig("GMRF4.png",dpi=350)

plt.figure()
prior5.sample().plot()
print(max(prior5.sample()))
plt.savefig("GMRF5.png",dpi=350)

plt.figure()
prior6.sample().plot()
print(max(prior6.sample()))
plt.savefig("GMRF6.png",dpi=350)
