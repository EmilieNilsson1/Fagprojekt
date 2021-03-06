import scipy as sp
import scipy.stats as sps
import numpy as np

from cuqi.distribution import Normal
# import matplotlib
# import matplotlib.pyplot as plt
eps = np.finfo(float).eps

import cuqi
from cuqi.solver import CGLS
from cuqi.samples import Samples
from abc import ABC, abstractmethod

import sys

#===================================================================
class Sampler(ABC):

    def __init__(self, target, x0=None, dim=None, callback=None):

        self._dim = dim
        if hasattr(target,'dim'): 
            if self._dim is None:
                self._dim = target.dim 
            elif self._dim != target.dim:
                raise ValueError("'dim' need to be None or equal to 'target.dim'") 
        elif x0 is not None:
            self._dim = len(x0)

        self.target = target

        if x0 is None:
            x0 = np.ones(self.dim)
        self.x0 = x0

        self.callback = callback

    @property
    def geometry(self):
        if hasattr(self, 'target') and hasattr(self.target, 'geometry'):
            geom =  self.target.geometry
        else:
            geom = cuqi.geometry._DefaultGeometry(self.dim)
        return geom

    @property 
    def target(self):
        return self._target 

    @target.setter 
    def target(self, value):
        if  not isinstance(value, cuqi.distribution.Distribution) and callable(value):
            # obtain self.dim
            if self.dim is not None:
                dim = self.dim
            else:
                raise ValueError(f"If 'target' is a lambda function, the parameter 'dim' need to be specified when initializing {self.__class__}.")

            # set target
            self._target = cuqi.distribution.UserDefinedDistribution(logpdf_func=value, dim = dim)

        elif isinstance(value, cuqi.distribution.Distribution):
            self._target = value
        else:
            raise ValueError("'target' need to be either a lambda function or of type 'cuqi.distribution.Distribution'")


    @property
    def dim(self):
        if hasattr(self,'target') and hasattr(self.target,'dim'):
            self._dim = self.target.dim 
        return self._dim
    

    def sample(self,N,Nb=0):
        # Get samples from the samplers sample method
        result = self._sample(N,Nb)
        return self._create_Sample_object(result,N+Nb)

    def sample_adapt(self,N,Nb=0):
        # Get samples from the samplers sample method
        result = self._sample_adapt(N,Nb)
        return self._create_Sample_object(result,N+Nb)

    def _create_Sample_object(self,result,N):
        loglike_eval = None
        acc_rate = None
        if isinstance(result,tuple):
            #Unpack samples+loglike+acc_rate
            s = result[0]
            if len(result)>1: loglike_eval = result[1]
            if len(result)>2: acc_rate = result[2]
            if len(result)>3: raise TypeError("Expected tuple of at most 3 elements from sampling method.")
        else:
            s = result
                
        #Store samples in cuqi samples object if more than 1 sample
        if N==1:
            if len(s) == 1 and isinstance(s,np.ndarray): #Extract single value from numpy array
                s = s.ravel()[0]
            else:
                s = s.flatten()
        else:
            s = Samples(s, self.geometry)#, geometry = self.geometry)
            s.loglike_eval = loglike_eval
            s.acc_rate = acc_rate
        return s

    @abstractmethod
    def _sample(self,N,Nb):
        pass

    @abstractmethod
    def _sample_adapt(self,N,Nb):
        pass

    def _print_progress(self,s,Ns):
        """Prints sampling progress"""
        if (s % (max(Ns//100,1))) == 0:
            msg = f'Sample {s} / {Ns}'
            sys.stdout.write('\r'+msg)
        if s==Ns:
            msg = f'Sample {s} / {Ns}'
            sys.stdout.write('\r'+msg+'\n')

    def _call_callback(self, sample, sample_index):
        """ Calls the callback function. Assumes input is sample and sample index"""
        if self.callback is not None:
            self.callback(sample, sample_index)

class ProposalBasedSampler(Sampler,ABC):
    def __init__(self, target,  proposal=None, scale=1, x0=None, dim=None, **kwargs):
        #TODO: after fixing None dim
        #if dim is None and hasattr(proposal,'dim'):
        #    dim = proposal.dim
        super().__init__(target, x0=x0, dim=dim, **kwargs)

        self.proposal =proposal
        self.scale = scale


    @property 
    def proposal(self):
        return self._proposal 

    @proposal.setter 
    def proposal(self, value):
        self._proposal = value

    @property
    def geometry(self):
        geom1, geom2 = None, None
        if hasattr(self, 'proposal') and hasattr(self.proposal, 'geometry') and self.proposal.geometry.dim is not None:
            geom1=  self.proposal.geometry
        if hasattr(self, 'target') and hasattr(self.target, 'geometry') and self.target.geometry.dim is not None:
            geom2 = self.target.geometry
        if not isinstance(geom1,cuqi.geometry._DefaultGeometry) and geom1 is not None:
            return geom1
        elif not isinstance(geom2,cuqi.geometry._DefaultGeometry) and geom2 is not None: 
            return geom2
        else:
            return cuqi.geometry._DefaultGeometry(self.dim)



# another implementation is in https://github.com/mfouesneau/NUTS
class NUTS(Sampler):
    """No-U-Turn Sampler (Hoffman and Gelman, 2014).

    Samples a distribution given its logpdf and gradient using a Hamiltonian Monte Carlo (HMC) algorithm with automatic parameter tuning.

    For more details see: See Hoffman, M. D., & Gelman, A. (2014). The no-U-turn sampler: Adaptively setting path lengths in Hamiltonian Monte Carlo. Journal of Machine Learning Research, 15, 1593-1623.

    Parameters
    ----------

    target : `cuqi.distribution.Distribution`
        The target distribution to sample. Must have logpdf and gradient method. Custom logpdfs and gradients are supported by using a :class:`cuqi.distribution.UserDefinedDistribution`.
    
    x0 : ndarray
        Initial parameters. *Optional*

    max_depth : int
        Maximum depth of the tree.

    adapt_step_size : Bool or float
        Whether to adapt the step size.
        If True, the step size is adapted automatically.
        If False, the step size is fixed to the initially estimated value.
        If set to a scalar, the step size will be given by user and not adapted.

    opt_acc_rate : float
        The optimal acceptance rate to reach if using adaptive step size.
        Suggested values are 0.6 (default) or 0.8 (as in stan).

    callback : callable, *Optional*
        If set this function will be called after every sample.
        The signature of the callback function is `callback(sample, sample_index)`,
        where `sample` is the current sample and `sample_index` is the index of the sample.
        An example is shown in demos/demo31_callback.py.

    Example
    -------
    .. code-block:: python

        # Import cuqi
        import cuqi

        # Define a target distribution
        tp = cuqi.testproblem.WangCubic()
        target = tp.posterior

        # Set up sampler
        sampler = cuqi.sampler.NUTS(target)

        # Sample
        samples = sampler.sample(10000, 5000)

        # Plot samples
        samples.plot_pair()

    """
    def __init__(self, target, x0=None, max_depth=15, adapt_step_size=True, opt_acc_rate=0.6, **kwargs):
        super().__init__(target, x0=x0, **kwargs)
        self.max_depth = max_depth
        self.adapt_step_size = adapt_step_size
        self.opt_acc_rate = opt_acc_rate
    
    def _nuts_target(self, x): # returns logposterior tuple evaluation-gradient
        return self.target.logpdf(x), self.target.gradient(x)

    def _sample_adapt(self, N, Nb):
        return self._sample(N, Nb)
        
    def _sample(self, N, Nb):
        
        if self.adapt_step_size is True and Nb == 0:
            raise ValueError("Adaptive step size is True but number of burn-in steps is 0. Please set Nb > 0.")

        # Allocation
        Ns = Nb+N # total number of chains
        theta = np.empty((self.dim, Ns))
        joint_eval = np.empty(Ns)
        step_sizes = np.empty(Ns)

        # Initial state
        theta[:, 0] = self.x0
        joint_eval[0], grad = self._nuts_target(self.x0)

        # parameters dual averaging
        if (self.adapt_step_size == True):
            epsilon = self._FindGoodEpsilon(theta[:, 0], joint_eval[0], grad)
            mu = np.log(10*epsilon)
            gamma, t_0, kappa = 0.05, 10, 0.75 # kappa in (0.5, 1]
            epsilon_bar, H_bar = 1, 0
            delta = self.opt_acc_rate # https://mc-stan.org/docs/2_18/reference-manual/hmc-algorithm-parameters.html
            step_sizes[0] = epsilon
        elif (self.adapt_step_size == False):
            epsilon = self._FindGoodEpsilon(theta[:, 0], joint_eval[0], grad)
        else:
            epsilon = self.adapt_step_size # if scalar then user specifies the step size

        # run NUTS
        for k in range(1, Ns):
            theta_k, joint_k = theta[:, k-1], joint_eval[k-1] # initial position (parameters)
            r_k = self._Kfun(1, 'sample') # resample momentum vector
            Ham = joint_k - self._Kfun(r_k, 'eval') # Hamiltonian

            # slice variable
            log_u = Ham - np.random.exponential(1, size=1) # u = np.log(np.random.uniform(0, np.exp(H)))

            # initialization
            j, s, n = 0, 1, 1
            theta[:, k], joint_eval[k] = theta_k, joint_k
            theta_minus, theta_plus = np.copy(theta_k), np.copy(theta_k)
            grad_minus, grad_plus = np.copy(grad), np.copy(grad)
            r_minus, r_plus = np.copy(r_k), np.copy(r_k)

            # run NUTS
            while (s == 1) and (j <= self.max_depth):
                # sample a direction
                v = int(2*(np.random.rand() < 0.5)-1)

                # build tree: doubling procedure
                if (v == -1):
                    theta_minus, r_minus, grad_minus, _, _, _, \
                    theta_prime, joint_prime, grad_prime, n_prime, s_prime, alpha, n_alpha = \
                        self._BuildTree(theta_minus, r_minus, grad_minus, Ham, log_u, v, j, epsilon)
                else:
                    _, _, _, theta_plus, r_plus, grad_plus, \
                    theta_prime, joint_prime, grad_prime, n_prime, s_prime, alpha, n_alpha = \
                        self._BuildTree(theta_plus, r_plus, grad_plus, Ham, log_u, v, j, epsilon)

                # Metropolis step
                alpha2 = min(1, (n_prime/n)) #min(0, np.log(n_p) - np.log(n))
                if (s_prime == 1) and (np.random.rand() <= alpha2):
                    theta[:, k] = theta_prime
                    joint_eval[k] = joint_prime
                    grad = np.copy(grad_prime)

                # update number of particles, tree level, and stopping criterion
                n += n_prime
                dtheta = theta_plus - theta_minus
                s = s_prime * int((dtheta @ r_minus.T) >= 0) * int((dtheta @ r_plus.T) >= 0)
                j += 1

            # adapt epsilon during burn-in using dual averaging
            if (k <= Nb) and (self.adapt_step_size == True):
                eta1 = 1/(k + t_0)
                H_bar = (1-eta1)*H_bar + eta1*(delta - (alpha/n_alpha))
                epsilon = np.exp(mu - (np.sqrt(k)/gamma)*H_bar)
                eta = k**(-kappa)
                epsilon_bar = np.exp(eta*np.log(epsilon) + (1-eta)*np.log(epsilon_bar))
            elif (k == Nb+1) and (self.adapt_step_size == True):
                epsilon = epsilon_bar   # fix epsilon after burn-in
            step_sizes[k] = epsilon
            
            # msg
            self._print_progress(k+1, Ns) #k+1 is the sample number, k is index assuming x0 is the first sample
            self._call_callback(theta[:, k], k)
            
            if np.isnan(joint_eval[k]):
                raise NameError('NaN potential func')

        # apply burn-in 
        theta = theta[:, Nb:]
        joint_eval = joint_eval[Nb:]
        return theta, joint_eval, step_sizes

    #=========================================================================
    # auxiliary standard Gaussian PDF: kinetic energy function
    # d_log_2pi = d*np.log(2*np.pi)
    def _Kfun(self, r, flag):
        if flag == 'eval': # evaluate
            return 0.5*(r.T @ r) #+ d_log_2pi 
        if flag == 'sample': # sample
            return np.random.standard_normal(size=self.dim)

    #=========================================================================
    def _FindGoodEpsilon(self, theta, joint, grad, epsilon=1):
        r = self._Kfun(1, 'sample')    # resample a momentum
        Ham = joint - self._Kfun(r, 'eval')     # initial Hamiltonian
        _, r_prime, joint_prime, grad_prime = self._Leapfrog(theta, r, grad, epsilon)

        # trick to make sure the step is not huge, leading to infinite values of the likelihood
        k = 1
        while np.isinf(joint_prime) or np.isinf(grad_prime).any():
            k *= 0.5
            _, r_prime, joint_prime, grad_prime = self._Leapfrog(theta, r, grad, epsilon*k)
        epsilon = 0.5*k*epsilon

        # doubles/halves the value of epsilon until the accprob of the Langevin proposal crosses 0.5
        Ham_prime = joint_prime - self._Kfun(r_prime, 'eval')
        log_ratio = Ham_prime - Ham
        a = 1 if log_ratio > np.log(0.5) else -1
        while (a*log_ratio > -a*np.log(2)):
            epsilon = (2**a)*epsilon
            _, r_prime, joint_prime, _ = self._Leapfrog(theta, r, grad, epsilon)
            Ham_prime = joint_prime - self._Kfun(r_prime, 'eval')
            log_ratio = Ham_prime - Ham
        return epsilon

    #=========================================================================
    def _Leapfrog(self, theta_old, r_old, grad_old, epsilon):
        # symplectic integrator: trajectories preserve phase space volumen
        r_new = r_old + 0.5*epsilon*grad_old     # half-step
        theta_new = theta_old + epsilon*r_new     # full-step
        joint_new, grad_new = self._nuts_target(theta_new)     # new gradient
        r_new += 0.5*epsilon*grad_new     # half-step
        return theta_new, r_new, joint_new, grad_new

    #=========================================================================
    # @functools.lru_cache(maxsize=128)
    def _BuildTree(self, theta, r, grad, Ham, log_u, v, j, epsilon, Delta_max=1000):
        if (j == 0):     # base case
            # single leapfrog step in the direction v
            theta_prime, r_prime, joint_prime, grad_prime = self._Leapfrog(theta, r, grad, v*epsilon)
            Ham_prime = joint_prime - self._Kfun(r_prime, 'eval')     # Hamiltonian eval
            n_prime = int(log_u <= Ham_prime)     # if particle is in the slice
            s_prime = int(log_u < Delta_max + Ham_prime)     # check U-turn
            #
            diff_Ham = Ham_prime - Ham
            alpha_prime = min(1, np.exp(diff_Ham))     # logalpha_p = min(0, H_p - H)
            n_alpha_prime = 1
            #
            theta_minus, theta_plus = theta_prime, theta_prime
            r_minus, r_plus = r_prime, r_prime
            grad_minus, grad_plus = grad_prime, grad_prime
        else: 
            # recursion: build the left/right subtrees
            theta_minus, r_minus, grad_minus, theta_plus, r_plus, grad_plus, \
            theta_prime, joint_prime, grad_prime, n_prime, s_prime, alpha_prime, n_alpha_prime = \
                self._BuildTree(theta, r, grad, Ham, log_u, v, j-1, epsilon)
            if (s_prime == 1): # do only if the stopping criteria does not verify at the first subtree
                if (v == -1):
                    theta_minus, r_minus, grad_minus, _, _, _, \
                    theta_2prime, joint_2prime, grad_2prime, n_2prime, s_2prime, alpha_2prime, n_alpha_2prime = \
                        self._BuildTree(theta_minus, r_minus, grad_minus, Ham, log_u, v, j-1, epsilon)
                else:
                    _, _, _, theta_plus, r_plus, grad_plus, \
                    theta_2prime, joint_2prime, grad_2prime, n_2prime, s_2prime, alpha_2prime, n_alpha_2prime = \
                        self._BuildTree(theta_plus, r_plus, grad_plus, Ham, log_u, v, j-1, epsilon)

                # Metropolis step
                alpha2 = n_2prime / max(1, (n_prime + n_2prime))
                if (np.random.rand() <= alpha2):
                    theta_prime = np.copy(theta_2prime)
                    joint_prime = np.copy(joint_2prime)
                    grad_prime = np.copy(grad_2prime)

                # update number of particles and stopping criterion
                alpha_prime += alpha_2prime
                n_alpha_prime += n_alpha_2prime
                dtheta = theta_plus - theta_minus
                s_prime = s_2prime * int((dtheta@r_minus.T)>=0) * int((dtheta@r_plus.T)>=0)
                n_prime += n_2prime
        return theta_minus, r_minus, grad_minus, theta_plus, r_plus, grad_plus, \
                theta_prime, joint_prime, grad_prime, n_prime, s_prime, alpha_prime, n_alpha_prime



class Linear_RTO(Sampler):
    """
    Linear RTO (Randomize-Then-Optimize) sampler.

    Samples posterior related to the inverse problem with Gaussian likelihood and prior, and where the forward model is Linear.

    Parameters
    ------------
    target : `cuqi.distribution.Posterior` or 5-dimensional tuple.
        If target is of type cuqi.distribution.Posterior, it represents the posterior distribution.
        If target is a 5-dimensional tuple, it assumes the following structure:
        (data, model, L_sqrtprec, P_mean, P_sqrtrec)
        
        Here:
        data: is a m-dimensional numpy array containing the measured data.
        model: is a m by n dimensional matrix or LinearModel representing the forward model.
        L_sqrtprec: is the squareroot of the precision matrix of the Gaussian likelihood.
        P_mean: is the prior mean.
        P_sqrtprec: is the squareroot of the precision matrix of the Gaussian mean.

    x0 : `np.ndarray` 
        Initial point for the sampler. *Optional*.

    maxit : int
        Maximum number of iterations of the inner CGLS solver. *Optional*.

    tol : float
        Tolerance of the inner CGLS solver. *Optional*.

    callback : callable, *Optional*
        If set this function will be called after every sample.
        The signature of the callback function is `callback(sample, sample_index)`,
        where `sample` is the current sample and `sample_index` is the index of the sample.
        An example is shown in demos/demo31_callback.py.
        
    """
    def __init__(self, target, x0=None, maxit=50, tol=1e-5, shift=0, **kwargs):
        
        # Accept tuple of inputs and construct posterior
        if isinstance(target, tuple) and len(target) == 5:
            # Structure (data, model, L_sqrtprec, P_mean, P_sqrtprec)
            data = target[0]
            model = target[1]
            L_sqrtprec = target[2]
            P_mean = target[3]
            P_sqrtprec = target[4]

            # If numpy matrix convert to CUQI model
            if isinstance(model, np.ndarray) and len(model.shape) == 2:
                model = cuqi.model.LinearModel(model)

            # Check model input
            if not isinstance(model, cuqi.model.LinearModel):
                raise TypeError("Model needs to be cuqi.model.LinearModel or matrix")

            # Likelihood
            L = cuqi.distribution.GaussianSqrtPrec(model, L_sqrtprec).to_likelihood(data)

            # Prior TODO: allow multiple priors stacked
            #if isinstance(P_mean, list) and isinstance(P_sqrtprec, list):
            #    P = cuqi.distribution.JointGaussianSqrtPrec(P_mean, P_sqrtprec)
            #else:
            P = cuqi.distribution.GaussianSqrtPrec(P_mean, P_sqrtprec)

            # Construct posterior
            target = cuqi.distribution.Posterior(L, P)

        super().__init__(target, x0=x0, **kwargs)

        # Check target type
        if not isinstance(target, cuqi.distribution.Posterior):
            raise ValueError(f"To initialize an object of type {self.__class__}, 'target' need to be of type 'cuqi.distribution.Posterior'.")       

        # Check Linear model and Gaussian prior+likelihood
        if not isinstance(self.model, cuqi.model.LinearModel):
            raise TypeError("Model needs to be linear")

        if not hasattr(self.likelihood.distribution, "sqrtprec"):
            raise TypeError("Distribution in Likelihood must contain a sqrtprec attribute")

        if not hasattr(self.prior, "sqrtprec"):
            raise TypeError("prior must contain a sqrtprec attribute")

        if not hasattr(self.prior, "sqrtprecTimesMean"):
            raise TypeError("Prior must contain a sqrtprecTimesMean attribute")

        # Modify initial guess        
        if x0 is not None:
            self.x0 = x0
        else:
            self.x0 = np.zeros(self.prior.dim)

        # Other parameters
        self.maxit = maxit
        self.tol = tol        
        self.shift = 0
                
        L1 = self.likelihood.distribution.sqrtprec
        L2 = self.prior.sqrtprec
        L2mu = self.prior.sqrtprecTimesMean

        # pre-computations
        self.m = len(self.data)
        self.n = len(self.x0)
        self.b_tild = np.hstack([L1@self.data, L2mu]) 

        if not callable(self.model):
            self.M = sp.sparse.vstack([L1@self.model, L2])
        else:
            # in this case, model is a function doing forward and backward operations
            def M(x, flag):
                if flag == 1:
                    out1 = L1 @ self.model.forward(x)
                    out2 = L2 @ x
                    out  = np.hstack([out1, out2])
                elif flag == 2:
                    idx = int(self.m)
                    out1 = self.model.adjoint(L1.T@x[:idx])
                    out2 = L2.T @ x[idx:]
                    out  = out1 + out2                
                return out   
            self.M = M       

    @property
    def prior(self):
        return self.target.prior

    @property
    def likelihood(self):
        return self.target.likelihood

    @property
    def model(self):
        return self.target.model     
    
    @property
    def data(self):
        return self.target.data

    def _sample(self, N, Nb):   
        Ns = N+Nb   # number of simulations        
        samples = np.empty((self.n, Ns))
                     
        # initial state   
        samples[:, 0] = self.x0
        for s in range(Ns-1):
            y = self.b_tild + np.random.randn(len(self.b_tild))
            sim = CGLS(self.M, y, samples[:, s], self.maxit, self.tol, self.shift)            
            samples[:, s+1], _ = sim.solve()

            self._print_progress(s+2,Ns) #s+2 is the sample number, s+1 is index assuming x0 is the first sample
            self._call_callback(samples[:, s+1], s+1)

        # remove burn-in
        samples = samples[:, Nb:]
        
        return samples, None, None

    def _sample_adapt(self, N, Nb):
        return self._sample(N,Nb)


#===================================================================
#===================================================================
#===================================================================
class CWMH(ProposalBasedSampler):
    """Component-wise Metropolis Hastings sampler.

    Allows sampling of a target distribution by a component-wise random-walk sampling of a proposal distribution along with an accept/reject step.

    Parameters
    ----------

    target : `cuqi.distribution.Distribution` or lambda function
        The target distribution to sample. Custom logpdfs are supported by using a :class:`cuqi.distribution.UserDefinedDistribution`.
    
    proposal : `cuqi.distribution.Distribution` or callable method
        The proposal to sample from. If a callable method it should provide a single independent sample from proposal distribution. Defaults to a Gaussian proposal.  *Optional*.

    scale : float
        Scale parameter used to define correlation between previous and proposed sample in random-walk.  *Optional*.

    x0 : ndarray
        Initial parameters. *Optional*

    dim : int
        Dimension of parameter space. Required if target and proposal are callable functions. *Optional*.

    callback : callable, *Optional*
        If set this function will be called after every sample.
        The signature of the callback function is `callback(sample, sample_index)`,
        where `sample` is the current sample and `sample_index` is the index of the sample.
        An example is shown in demos/demo31_callback.py.

    Example
    -------
    .. code-block:: python

        # Parameters
        dim = 5 # Dimension of distribution
        mu = np.arange(dim) # Mean of Gaussian
        std = 1 # standard deviation of Gaussian

        # Logpdf function
        logpdf_func = lambda x: -1/(std**2)*np.sum((x-mu)**2)

        # Define distribution from logpdf as UserDefinedDistribution (sample and gradients also supported as inputs to UserDefinedDistribution)
        target = cuqi.distribution.UserDefinedDistribution(dim=dim, logpdf_func=logpdf_func)

        # Set up sampler
        sampler = cuqi.sampler.CWMH(target, scale=1)

        # Sample
        samples = sampler.sample(2000)

    """
    def __init__(self, target,  proposal=None, scale=1, x0=None, dim = None, **kwargs):
        super().__init__(target, proposal=proposal, scale=scale,  x0=x0, dim=dim, **kwargs)
        
    @ProposalBasedSampler.proposal.setter 
    def proposal(self, value):
        fail_msg = "Proposal should be either None, cuqi.distribution.Distribution conditioned only on 'location' and 'scale', lambda function, or cuqi.distribution.Normal conditioned only on 'mean' and 'std'"

        if value is None:
            self._proposal = cuqi.distribution.Normal(mean = lambda location:location,std = lambda scale:scale )

        elif isinstance(value, cuqi.distribution.Distribution) and sorted(value.get_conditioning_variables())==['location','scale']:
            self._proposal = value

        elif isinstance(value, cuqi.distribution.Normal) and sorted(value.get_conditioning_variables())==['mean','std']:
            self._proposal = value(mean = lambda location:location, std = lambda scale:scale)

        elif not isinstance(value, cuqi.distribution.Distribution) and callable(value):
            self._proposal = value

        else:
            raise ValueError(fail_msg)


    def _sample(self, N, Nb):
        Ns = N+Nb   # number of simulations

        # allocation
        samples = np.empty((self.dim, Ns))
        target_eval = np.empty(Ns)
        acc = np.zeros((self.dim, Ns), dtype=int)

        # initial state    
        samples[:, 0] = self.x0
        target_eval[0] = self.target.logpdf(self.x0)
        acc[:, 0] = np.ones(self.dim)

        # run MCMC
        for s in range(Ns-1):
            # run component by component
            samples[:, s+1], target_eval[s+1], acc[:, s+1] = self.single_update(samples[:, s], target_eval[s])

            self._print_progress(s+2,Ns) #s+2 is the sample number, s+1 is index assuming x0 is the first sample
            self._call_callback(samples[:, s+1], s+1)

        # remove burn-in
        samples = samples[:, Nb:]
        target_eval = target_eval[Nb:]
        acccomp = acc[:, Nb:].mean(axis=1)   
        print('\nAverage acceptance rate all components:', acccomp.mean(), '\n')
        
        return samples, target_eval, acccomp

    def _sample_adapt(self, N, Nb):
        # this follows the vanishing adaptation Algorithm 4 in:
        # Andrieu and Thoms (2008) - A tutorial on adaptive MCMC
        Ns = N+Nb   # number of simulations

        # allocation
        samples = np.empty((self.dim, Ns))
        target_eval = np.empty(Ns)
        acc = np.zeros((self.dim, Ns), dtype=int)

        # initial state
        samples[:, 0] = self.x0
        target_eval[0] = self.target.logpdf(self.x0)
        acc[:, 0] = np.ones(self.dim)

        # initial adaptation params 
        Na = int(0.1*N)                                        # iterations to adapt
        hat_acc = np.empty((self.dim, int(np.floor(Ns/Na))))     # average acceptance rate of the chains
        lambd = np.empty((self.dim, int(np.floor(Ns/Na)+1)))     # scaling parameter \in (0,1)
        lambd[:, 0] = self.scale
        star_acc = 0.21/self.dim + 0.23    # target acceptance rate RW
        i, idx = 0, 0

        # run MCMC
        for s in range(Ns-1):
            # run component by component
            samples[:, s+1], target_eval[s+1], acc[:, s+1] = self.single_update(samples[:, s], target_eval[s])
            
            # adapt prop spread of each component using acc of past samples
            if ((s+1) % Na == 0):
                # evaluate average acceptance rate
                hat_acc[:, i] = np.mean(acc[:, idx:idx+Na], axis=1)

                # compute new scaling parameter
                zeta = 1/np.sqrt(i+1)   # ensures that the variation of lambda(i) vanishes
                lambd[:, i+1] = np.exp(np.log(lambd[:, i]) + zeta*(hat_acc[:, i]-star_acc))  

                # update parameters
                self.scale = np.minimum(lambd[:, i+1], np.ones(self.dim))

                # update counters
                i += 1
                idx += Na

            # display iterations 
            self._print_progress(s+2,Ns) #s+2 is the sample number, s+1 is index assuming x0 is the first sample
            self._call_callback(samples[:, s+1], s+1)
            
        # remove burn-in
        samples = samples[:, Nb:]
        target_eval = target_eval[Nb:]
        acccomp = acc[:, Nb:].mean(axis=1)
        print('\nAverage acceptance rate all components:', acccomp.mean(), '\n')
        
        return samples, target_eval, acccomp

    def single_update(self, x_t, target_eval_t):
        if isinstance(self.proposal,cuqi.distribution.Distribution):
            x_i_star = self.proposal(location= x_t, scale = self.scale).sample()
        else:
            x_i_star = self.proposal(x_t, self.scale) 
        x_star = x_t.copy()
        acc = np.zeros(self.dim)

        for j in range(self.dim):
            # propose state
            x_star[j] = x_i_star[j]

            # evaluate target
            target_eval_star = self.target.logpdf(x_star)

            # ratio and acceptance probability
            ratio = target_eval_star - target_eval_t  # proposal is symmetric
            alpha = min(0, ratio)

            # accept/reject
            u_theta = np.log(np.random.rand())
            if (u_theta <= alpha):
                x_t[j] = x_i_star[j]
                target_eval_t = target_eval_star
                acc[j] = 1
            else:
                pass
                # x_t[j]       = x_t[j]
                # target_eval_t = target_eval_t
            x_star = x_t.copy()
        #
        return x_t, target_eval_t, acc

#===================================================================
#===================================================================
#===================================================================
class MetropolisHastings(ProposalBasedSampler):
    """Metropolis Hastings sampler.

    Allows sampling of a target distribution by random-walk sampling of a proposal distribution along with an accept/reject step.

    Parameters
    ----------

    target : `cuqi.distribution.Distribution` or lambda function
        The target distribution to sample. Custom logpdfs are supported by using a :class:`cuqi.distribution.UserDefinedDistribution`.
    
    proposal : `cuqi.distribution.Distribution` or callable method
        The proposal to sample from. If a callable method it should provide a single independent sample from proposal distribution. Defaults to a Gaussian proposal.  *Optional*.

    scale : float
        Scale parameter used to define correlation between previous and proposed sample in random-walk.  *Optional*.

    x0 : ndarray
        Initial parameters. *Optional*

    dim : int
        Dimension of parameter space. Required if target and proposal are callable functions. *Optional*.

    callback : callable, *Optional*
        If set this function will be called after every sample.
        The signature of the callback function is `callback(sample, sample_index)`,
        where `sample` is the current sample and `sample_index` is the index of the sample.
        An example is shown in demos/demo31_callback.py.

    Example
    -------
    .. code-block:: python

        # Parameters
        dim = 5 # Dimension of distribution
        mu = np.arange(dim) # Mean of Gaussian
        std = 1 # standard deviation of Gaussian

        # Logpdf function
        logpdf_func = lambda x: -1/(std**2)*np.sum((x-mu)**2)

        # Define distribution from logpdf as UserDefinedDistribution (sample and gradients also supported)
        target = cuqi.distribution.UserDefinedDistribution(dim=dim, logpdf_func=logpdf_func)

        # Set up sampler
        sampler = cuqi.sampler.MetropolisHastings(target, scale=1)

        # Sample
        samples = sampler.sample(2000)

    """
    #target,  proposal=None, scale=1, x0=None, dim=None
    #    super().__init__(target, proposal=proposal, scale=scale,  x0=x0, dim=dim)
    def __init__(self, target, proposal=None, scale=None, x0=None, dim=None, **kwargs):
        """ Metropolis-Hastings (MH) sampler. Default (if proposal is None) is random walk MH with proposal that is Gaussian with identity covariance"""
        super().__init__(target, proposal=proposal, scale=scale,  x0=x0, dim=dim, **kwargs)


    @ProposalBasedSampler.proposal.setter 
    def proposal(self, value):
        fail_msg = "Proposal should be either None, symmetric cuqi.distribution.Distribution or a lambda function."

        if value is None:
            self._proposal = cuqi.distribution.Gaussian(np.zeros(self.dim),np.ones(self.dim), np.eye(self.dim))
        elif not isinstance(value, cuqi.distribution.Distribution) and callable(value):
            raise NotImplementedError(fail_msg)
        elif isinstance(value, cuqi.distribution.Distribution) and value.is_symmetric:
            self._proposal = value
        else:
            raise ValueError(fail_msg)
        self._proposal.geometry = self.target.geometry

    def _sample(self, N, Nb):
        if self.scale is None:
            raise ValueError("Scale must be set to sample without adaptation. Consider using sample_adapt instead.")
        
        Ns = N+Nb   # number of simulations

        # allocation
        samples = np.empty((self.dim, Ns))
        target_eval = np.empty(Ns)
        acc = np.zeros(Ns, dtype=int)

        # initial state    
        samples[:, 0] = self.x0
        target_eval[0] = self.target.logpdf(self.x0)
        acc[0] = 1

        # run MCMC
        for s in range(Ns-1):
            # run component by component
            samples[:, s+1], target_eval[s+1], acc[s+1] = self.single_update(samples[:, s], target_eval[s])
            self._print_progress(s+2,Ns) #s+2 is the sample number, s+1 is index assuming x0 is the first sample
            self._call_callback(samples[:, s+1], s+1)

        # remove burn-in
        samples = samples[:, Nb:]
        target_eval = target_eval[Nb:]
        accave = acc[Nb:].mean()   
        print('\nAverage acceptance rate:', accave, '\n')
        #
        return samples, target_eval, accave

    def _sample_adapt(self, N, Nb):
        # Set intial scale if not set
        if self.scale is None:
            self.scale = 0.1
            
        Ns = N+Nb   # number of simulations

        # allocation
        samples = np.empty((self.dim, Ns))
        target_eval = np.empty(Ns)
        acc = np.zeros(Ns)

        # initial state    
        samples[:, 0] = self.x0
        target_eval[0] = self.target.logpdf(self.x0)
        acc[0] = 1

        # initial adaptation params 
        Na = int(0.1*N)                              # iterations to adapt
        hat_acc = np.empty(int(np.floor(Ns/Na)))     # average acceptance rate of the chains
        lambd = self.scale
        star_acc = 0.234    # target acceptance rate RW
        i, idx = 0, 0

        # run MCMC
        for s in range(Ns-1):
            # run component by component
            samples[:, s+1], target_eval[s+1], acc[s+1] = self.single_update(samples[:, s], target_eval[s])
            
            # adapt prop spread using acc of past samples
            if ((s+1) % Na == 0):
                # evaluate average acceptance rate
                hat_acc[i] = np.mean(acc[idx:idx+Na])

                # d. compute new scaling parameter
                zeta = 1/np.sqrt(i+1)   # ensures that the variation of lambda(i) vanishes
                lambd = np.exp(np.log(lambd) + zeta*(hat_acc[i]-star_acc))

                # update parameters
                self.scale = min(lambd, 1)

                # update counters
                i += 1
                idx += Na

            # display iterations
            self._print_progress(s+2,Ns) #s+2 is the sample number, s+1 is index assuming x0 is the first sample


        # remove burn-in
        samples = samples[:, Nb:]
        target_eval = target_eval[Nb:]
        accave = acc[Nb:].mean()   
        print('\nAverage acceptance rate:', accave, 'MCMC scale:', self.scale, '\n')
        
        return samples, target_eval, accave


    def single_update(self, x_t, target_eval_t):
        # propose state
        xi = self.proposal.sample(1)   # sample from the proposal
        x_star = x_t + self.scale*xi.flatten()   # MH proposal

        # evaluate target
        target_eval_star = self.target.logpdf(x_star)

        # ratio and acceptance probability
        ratio = target_eval_star - target_eval_t  # proposal is symmetric
        alpha = min(0, ratio)

        # accept/reject
        u_theta = np.log(np.random.rand())
        if (u_theta <= alpha):
            x_next = x_star
            target_eval_next = target_eval_star
            acc = 1
        else:
            x_next = x_t
            target_eval_next = target_eval_t
            acc = 0
        
        return x_next, target_eval_next, acc


#===================================================================
#===================================================================
#===================================================================
class pCN(Sampler):   
    #Samples target*proposal
    #TODO. Check proposal, needs to be Gaussian and zero mean.
    """Preconditioned Crank-Nicolson sampler 
    
    Parameters
    ----------
    target : `cuqi.distribution.Posterior` or tuple of likelihood and prior objects
        If target is of type cuqi.distribution.Posterior, it represents the posterior distribution.
        If target is a tuple of (cuqi.likelihood.Likelihood, cuqi.distribution.Distribution) objects,
        the first element is considered the likelihood and the second is considered the prior.

    scale : int

    x0 : `np.ndarray` 
      Initial point for the sampler

    callback : callable, *Optional*
        If set this function will be called after every sample.
        The signature of the callback function is `callback(sample, sample_index)`,
        where `sample` is the current sample and `sample_index` is the index of the sample.
        An example is shown in demos/demo31_callback.py.

    Example 
    -------

    This uses a custom logpdf and sample function.

    .. code-block:: python

        # Parameters
        dim = 5 # Dimension of distribution
        mu = np.arange(dim) # Mean of Gaussian
        std = 1 # standard deviation of Gaussian

        # Logpdf function of likelihood
        logpdf_func = lambda x: -1/(std**2)*np.sum((x-mu)**2)

        # sample function of prior N(0,I)
        sample_func = lambda : 0 + 1*np.random.randn(dim,1)

        # Define as UserDefinedDistributions
        likelihood = cuqi.likelihood.UserDefinedLikelihood(dim=dim, logpdf_func=logpdf_func)
        prior = cuqi.distribution.UserDefinedDistribution(dim=dim, sample_func=sample_func)

        # Set up sampler
        sampler = cuqi.sampler.pCN((likelihood,prior), scale = 0.1)

        # Sample
        samples = sampler.sample(5000)

    Example
    -------

    This uses CUQIpy distributions.

    .. code-block:: python

        # Parameters
        dim = 5 # Dimension of distribution
        mu = np.arange(dim) # Mean of Gaussian
        std = 1 # standard deviation of Gaussian

        # Define as UserDefinedDistributions
        model = cuqi.model.Model(lambda x: x, range_geometry=dim, domain_geometry=dim)
        likelihood = cuqi.distribution.GaussianCov(mean=model, cov=np.ones(dim)).to_likelihood(mu)
        prior = cuqi.distribution.GaussianCov(mean=np.zeros(dim), cov=1)

        target = cuqi.distribution.Posterior(likelihood, prior)

        # Set up sampler
        sampler = cuqi.sampler.pCN(target, scale = 0.1)

        # Sample
        samples = sampler.sample(5000)
        
    """
    def __init__(self, target, scale=None, x0=None, **kwargs):
        super().__init__(target, x0=x0, dim=None, **kwargs) 
        self.scale = scale
    
    @property
    def prior(self):
        if isinstance(self.target, cuqi.distribution.Posterior):
            return self.target.prior
        elif isinstance(self.target,tuple) and len(self.target)==2:
            return self.target[1]

    @property
    def likelihood(self):
        if isinstance(self.target, cuqi.distribution.Posterior):
            return self.target.likelihood
        elif isinstance(self.target,tuple) and len(self.target)==2:
            return self.target[0]


    @Sampler.target.setter 
    def target(self, value):
        if isinstance(value, cuqi.distribution.Posterior):
            self._target = value
            self._loglikelihood = lambda x : self.likelihood.log(x)
        elif isinstance(value,tuple) and len(value)==2 and \
             (isinstance(value[0], cuqi.likelihood.Likelihood) or isinstance(value[0], cuqi.likelihood.UserDefinedLikelihood))  and \
             isinstance(value[1], cuqi.distribution.Distribution):
            self._target = value
            self._loglikelihood = lambda x : self.likelihood.log(x)
        else:
            raise ValueError(f"To initialize an object of type {self.__class__}, 'target' need to be of type 'cuqi.distribution.Posterior'.")
        
        #TODO:
        #if not isinstance(self.prior,(cuqi.distribution.Gaussian,cuqi.distribution.GaussianCov, cuqi.distribution.GaussianPrec, cuqi.distribution.GaussianSqrtPrec, cuqi.distribution.Normal)):
        #    raise ValueError("The prior distribution of the target need to be Gaussian")

    @property
    def dim(self):
        if hasattr(self,'target') and hasattr(self.target,'dim'):
            self._dim = self.target.dim
        elif hasattr(self,'target') and isinstance(self.target,tuple) and len(self.target)==2:
            self._dim = self.target[0].dim
        return self._dim

    def _sample(self, N, Nb):
        if self.scale is None:
            raise ValueError("Scale must be set to sample without adaptation. Consider using sample_adapt instead.")

        Ns = N+Nb   # number of simulations

        # allocation
        samples = np.empty((self.dim, Ns))
        loglike_eval = np.empty(Ns)
        acc = np.zeros(Ns, dtype=int)

        # initial state    
        samples[:, 0] = self.x0
        loglike_eval[0] = self._loglikelihood(self.x0)
        acc[0] = 1

        # run MCMC
        for s in range(Ns-1):
            # run component by component
            samples[:, s+1], loglike_eval[s+1], acc[s+1] = self.single_update(samples[:, s], loglike_eval[s])

            self._print_progress(s+2,Ns) #s+2 is the sample number, s+1 is index assuming x0 is the first sample
            self._call_callback(samples[:, s+1], s+1)

        # remove burn-in
        samples = samples[:, Nb:]
        loglike_eval = loglike_eval[Nb:]
        accave = acc[Nb:].mean()   
        print('\nAverage acceptance rate:', accave, '\n')
        #
        return samples, loglike_eval, accave

    def _sample_adapt(self, N, Nb):
        # Set intial scale if not set
        if self.scale is None:
            self.scale = 0.1

        Ns = N+Nb   # number of simulations

        # allocation
        samples = np.empty((self.dim, Ns))
        loglike_eval = np.empty(Ns)
        acc = np.zeros(Ns)

        # initial state    
        samples[:, 0] = self.x0
        loglike_eval[0] = self._loglikelihood(self.x0) 
        acc[0] = 1

        # initial adaptation params 
        Na = int(0.1*N)                              # iterations to adapt
        hat_acc = np.empty(int(np.floor(Ns/Na)))     # average acceptance rate of the chains
        lambd = self.scale
        star_acc = 0.44    # target acceptance rate RW
        i, idx = 0, 0

        # run MCMC
        for s in range(Ns-1):
            # run component by component
            samples[:, s+1], loglike_eval[s+1], acc[s+1] = self.single_update(samples[:, s], loglike_eval[s])
            
            # adapt prop spread using acc of past samples
            if ((s+1) % Na == 0):
                # evaluate average acceptance rate
                hat_acc[i] = np.mean(acc[idx:idx+Na])

                # d. compute new scaling parameter
                zeta = 1/np.sqrt(i+1)   # ensures that the variation of lambda(i) vanishes
                lambd = np.exp(np.log(lambd) + zeta*(hat_acc[i]-star_acc))

                # update parameters
                self.scale = min(lambd, 1)

                # update counters
                i += 1
                idx += Na

            # display iterations
            if ((s+1) % (max(Ns//100,1))) == 0 or (s+1) == Ns-1:
                print("\r",'Sample', s+1, '/', Ns, end="")

            self._call_callback(samples[:, s+1], s+1)

        print("\r",'Sample', s+2, '/', Ns)

        # remove burn-in
        samples = samples[:, Nb:]
        loglike_eval = loglike_eval[Nb:]
        accave = acc[Nb:].mean()   
        print('\nAverage acceptance rate:', accave, 'MCMC scale:', self.scale, '\n')
        
        return samples, loglike_eval, accave

    def single_update(self, x_t, loglike_eval_t):
        # propose state
        xi = self.prior.sample(1).flatten()   # sample from the prior
        x_star = np.sqrt(1-self.scale**2)*x_t + self.scale*xi   # pCN proposal

        # evaluate target
        loglike_eval_star =  self._loglikelihood(x_star) 

        # ratio and acceptance probability
        ratio = loglike_eval_star - loglike_eval_t  # proposal is symmetric
        alpha = min(0, ratio)

        # accept/reject
        u_theta = np.log(np.random.rand())
        if (u_theta <= alpha):
            x_next = x_star
            loglike_eval_next = loglike_eval_star
            acc = 1
        else:
            x_next = x_t
            loglike_eval_next = loglike_eval_t
            acc = 0
        
        return x_next, loglike_eval_next, acc
    
    

#===================================================================
#===================================================================
#===================================================================
class ULA(Sampler):
    """Unadjusted Langevin algorithm (ULA) (Roberts and Tweedie, 1996)

    Samples a distribution given its logpdf and gradient (up to a constant) based on
    Langevin diffusion dL_t = dW_t + 1/2*Nabla target.logpdf(L_t)dt,  where L_t is 
    the Langevin diffusion and W_t is the `dim`-dimensional standard Brownian motion.

    For more details see: Roberts, G. O., & Tweedie, R. L. (1996). Exponential convergence
    of Langevin distributions and their discrete approximations. Bernoulli, 341-363.

    Parameters
    ----------

    target : `cuqi.distribution.Distribution`
        The target distribution to sample. Must have logpdf and gradient method. Custom logpdfs 
        and gradients are supported by using a :class:`cuqi.distribution.UserDefinedDistribution`.
    
    x0 : ndarray
        Initial parameters. *Optional*

    scale : int
        The Langevin diffusion discretization time step (In practice, a scale of 1/dim**2 is
        recommended but not guaranteed to be the optimal choice).

    dim : int
        Dimension of parameter space. Required if target logpdf and gradient are callable 
        functions. *Optional*.

    callback : callable, *Optional*
        If set this function will be called after every sample.
        The signature of the callback function is `callback(sample, sample_index)`,
        where `sample` is the current sample and `sample_index` is the index of the sample.
        An example is shown in demos/demo31_callback.py.


    Example
    -------
    .. code-block:: python

        # Parameters
        dim = 5 # Dimension of distribution
        mu = np.arange(dim) # Mean of Gaussian
        std = 1 # standard deviation of Gaussian

        # Logpdf function
        logpdf_func = lambda x: -1/(std**2)*np.sum((x-mu)**2)
        gradient_func = lambda x: -2/(std**2)*(x - mu)

        # Define distribution from logpdf and gradient as UserDefinedDistribution
        target = cuqi.distribution.UserDefinedDistribution(dim=dim, logpdf_func=logpdf_func,
            gradient_func=gradient_func)

        # Set up sampler
        sampler = cuqi.sampler.ULA(target, scale=1/dim**2)

        # Sample
        samples = sampler.sample(2000)

    A Deblur example can be found in demos/demo27_ULA.py
    """
    def __init__(self, target, scale, x0=None, dim=None, rng=None, **kwargs):
        super().__init__(target, x0=x0, dim=dim, **kwargs)
        self.scale = scale
        self.rng = rng

    def _sample_adapt(self, N, Nb):
        return self._sample(N, Nb)

    def _sample(self, N, Nb):    
        # allocation
        Ns = Nb+N
        samples = np.empty((self.dim, Ns))
        target_eval = np.empty(Ns)
        g_target_eval = np.empty((self.dim, Ns))
        acc = np.zeros(Ns)

        # initial state
        samples[:, 0] = self.x0
        target_eval[0], g_target_eval[:,0] = self.target.logpdf(self.x0), self.target.gradient(self.x0)
        acc[0] = 1

        # ULA
        for s in range(Ns-1):
            samples[:, s+1], target_eval[s+1], g_target_eval[:,s+1], acc[s+1] = \
                self.single_update(samples[:, s], target_eval[s], g_target_eval[:,s])            
            self._print_progress(s+2,Ns) #s+2 is the sample number, s+1 is index assuming x0 is the first sample
            self._call_callback(samples[:, s+1], s+1)
    
        # apply burn-in 
        samples = samples[:, Nb:]
        target_eval = target_eval[Nb:]
        acc = acc[Nb:]
        return samples, target_eval, np.mean(acc)

    def single_update(self, x_t, target_eval_t, g_target_eval_t):
        # approximate Langevin diffusion
        xi = cuqi.distribution.Normal(mean=np.zeros(self.dim), std=np.sqrt(self.scale)).sample(rng=self.rng)
        x_star = x_t + 0.5*self.scale*g_target_eval_t + xi
        logpi_eval_star, g_logpi_star = self.target.logpdf(x_star), self.target.gradient(x_star)

        # msg
        if np.isnan(logpi_eval_star):
            raise NameError('NaN potential func. Consider using smaller scale parameter')

        return x_star, logpi_eval_star, g_logpi_star, 1 # sample always accepted without Metropolis correction


class MALA(ULA):
    """  Metropolis-adjusted Langevin algorithm (MALA) (Roberts and Tweedie, 1996)

    Samples a distribution given its logpdf and gradient (up to a constant) based on
    Langevin diffusion dL_t = dW_t + 1/2*Nabla target.logpdf(L_t)dt,  where L_t is 
    the Langevin diffusion and W_t is the `dim`-dimensional standard Brownian motion. 
    The sample is then accepted or rejected according to Metropolis???Hastings algorithm.

    For more details see: Roberts, G. O., & Tweedie, R. L. (1996). Exponential convergence
    of Langevin distributions and their discrete approximations. Bernoulli, 341-363.

    Parameters
    ----------

    target : `cuqi.distribution.Distribution`
        The target distribution to sample. Must have logpdf and gradient method. Custom logpdfs 
        and gradients are supported by using a :class:`cuqi.distribution.UserDefinedDistribution`.
    
    x0 : ndarray
        Initial parameters. *Optional*

    scale : int
        The Langevin diffusion discretization time step.

    dim : int
        Dimension of parameter space. Required if target logpdf and gradient are callable 
        functions. *Optional*.

    callback : callable, *Optional*
        If set this function will be called after every sample.
        The signature of the callback function is `callback(sample, sample_index)`,
        where `sample` is the current sample and `sample_index` is the index of the sample.
        An example is shown in demos/demo31_callback.py.


    Example
    -------
    .. code-block:: python

        # Parameters
        dim = 5 # Dimension of distribution
        mu = np.arange(dim) # Mean of Gaussian
        std = 1 # standard deviation of Gaussian

        # Logpdf function
        logpdf_func = lambda x: -1/(std**2)*np.sum((x-mu)**2)
        gradient_func = lambda x: -2/(std**2)*(x-mu)

        # Define distribution from logpdf as UserDefinedDistribution (sample and gradients also supported)
        target = cuqi.distribution.UserDefinedDistribution(dim=dim, logpdf_func=logpdf_func,
            gradient_func=gradient_func)

        # Set up sampler
        sampler = cuqi.sampler.MALA(target, scale=1/5**2)

        # Sample
        samples = sampler.sample(2000)

    A Deblur example can be found in demos/demo28_MALA.py
    """
    def __init__(self, target, scale, x0=None, dim=None, rng=None, **kwargs):
        super().__init__(target, scale, x0=x0, dim=dim, rng=rng, **kwargs)

    def single_update(self, x_t, target_eval_t, g_target_eval_t):
        # approximate Langevin diffusion
        xi = cuqi.distribution.Normal(mean=np.zeros(self.dim), std=np.sqrt(self.scale)).sample(rng=self.rng)
        x_star = x_t + (self.scale/2)*g_target_eval_t + xi
        logpi_eval_star, g_logpi_star = self.target.logpdf(x_star), self.target.gradient(x_star)

        # Metropolis step
        log_target_ratio = logpi_eval_star - target_eval_t
        log_prop_ratio = self.log_proposal(x_t, x_star, g_logpi_star) \
            - self.log_proposal(x_star, x_t,  g_target_eval_t)
        log_alpha = min(0, log_target_ratio + log_prop_ratio)

        # accept/reject
        log_u = np.log(cuqi.distribution.Uniform(low=0, high=1).sample(rng=self.rng))
        if (log_u <= log_alpha) and (np.isnan(logpi_eval_star) == False):
            return x_star, logpi_eval_star, g_logpi_star, 1
        else:
            return x_t.copy(), target_eval_t, g_target_eval_t.copy(), 0

    def log_proposal(self, theta_star, theta_k, g_logpi_k):
        mu = theta_k + ((self.scale)/2)*g_logpi_k
        misfit = theta_star - mu
        return -0.5*((1/(self.scale))*(misfit.T @ misfit))

class UnadjustedLaplaceApproximation(Sampler):
    """ Unadjusted Laplace approximation sampler
    
    Samples an approximate posterior where the prior is approximated
    by a Gaussian distribution. The likelihood must be Gaussian.

    Currently only works for Laplace_diff priors.

    The inner solver is Conjugate Gradient Least Squares (CGLS) solver.

    For more details see: Uribe, Felipe, et al. "A hybrid Gibbs sampler for edge-preserving 
    tomographic reconstruction with uncertain view angles." arXiv preprint arXiv:2104.06919 (2021).

    Parameters
    ----------
    target : `cuqi.distribution.Posterior`
        The target posterior distribution to sample.

    x0 : ndarray
        Initial parameters. *Optional*

    maxit : int
        Maximum number of inner iterations for solver when generating one sample.

    tol : float
        Tolerance for inner solver. Will stop before maxit if the inner solvers convergence check reaches tol.

    beta : float
        Smoothing parameter for the Gaussian approximation of the Laplace distribution. Larger beta is easier to sample but is a worse approximation.

    rng : np.random.RandomState
        Random number generator used for sampling. *Optional*

    callback : callable, *Optional*
        If set this function will be called after every sample.
        The signature of the callback function is `callback(sample, sample_index)`,
        where `sample` is the current sample and `sample_index` is the index of the sample.
        An example is shown in demos/demo31_callback.py.

    Returns
    -------
    cuqi.samples.Samples
        Samples from the posterior distribution.

    """

    def __init__(self, target, x0=None, maxit=50, tol=1e-5, beta=1e-5, rng=None, **kwargs):
        
        super().__init__(target, x0=x0, **kwargs)

        # Check target type
        if not isinstance(self.target, cuqi.distribution.Posterior):
            raise ValueError(f"To initialize an object of type {self.__class__}, 'target' need to be of type 'cuqi.distribution.Posterior'.")       

        # Check Linear model
        if not isinstance(self.target.likelihood.model, cuqi.model.LinearModel):
            raise TypeError("Model needs to be linear")

        # Check Gaussian likelihood
        if not hasattr(self.target.likelihood.distribution, "sqrtprec"):
            raise TypeError("Distribution in Likelihood must contain a sqrtprec attribute")

        # Check that prior is Laplace_diff
        if not isinstance(self.target.prior, cuqi.distribution.Laplace_diff):
            raise ValueError('Unadjusted Laplace approximation requires Laplace_diff prior')

        # Modify initial guess since Sampler sets it to ones.       
        if x0 is not None:
            self.x0 = x0
        else:
            self.x0 = np.zeros(self.target.prior.dim)
        
        # Store internal parameters
        self.maxit = maxit
        self.tol = tol
        self.beta = beta
        self.rng = rng

    def _sample_adapt(self, Ns, Nb):
        return self._sample(Ns, Nb)

    def _sample(self, Ns, Nb):
        """ Sample from the approximate posterior.

        Parameters
        ----------
        Ns : int
            Number of samples to draw.

        Nb : int
            Number of burn-in samples to discard.

        Returns
        -------
        samples : ndarray
            Samples from the approximate posterior.

        target_eval : ndarray
            Log-likelihood of each sample.

        acc : ndarray
            Acceptance rate of each sample.

        """

        # Extract diff_op from target prior
        D = self.target.prior._diff_op
        n = D.shape[0]

        # Gaussian approximation of Laplace_diff prior as function of x_k
        def Lk_fun(x_k):
            dd =  1/np.sqrt((D @ x_k)**2 + self.beta*np.ones(n))
            W = sp.sparse.diags(dd)
            return W.sqrt() @ D

        # Now prepare "Linear_RTO" type sampler. TODO: Use Linear_RTO for this instead
        self._shift = 0

        # Pre-computations
        self._model = self.target.likelihood.model   
        self._data = self.target.likelihood.data
        self._m = len(self._data)
        self._L1 = self.target.likelihood.distribution.sqrtprec

        # Initial Laplace approx
        self._L2 = Lk_fun(self.x0)
        self._L2mu = self._L2@self.target.prior.location
        self._b_tild = np.hstack([self._L1@self._data, self._L2mu]) 
        
        #self.n = len(self.x0)
        
        # Least squares form
        def M(x, flag):
            if flag == 1:
                out1 = self._L1 @ self._model.forward(x)
                out2 = np.sqrt(1/self.target.prior.scale)*(self._L2 @ x)
                out  = np.hstack([out1, out2])
            elif flag == 2:
                idx = int(self._m)
                out1 = self._model.adjoint(self._L1.T@x[:idx])
                out2 = np.sqrt(1/self.target.prior.scale)*(self._L2.T @ x[idx:])
                out  = out1 + out2                
            return out 
        
        # Initialize samples
        N = Ns+Nb   # number of simulations        
        samples = np.empty((self.target.dim, N))
                     
        # initial state   
        samples[:, 0] = self.x0
        for s in range(N-1):

            # Update Laplace approximation
            self._L2 = Lk_fun(samples[:, s])
            self._L2mu = self._L2@self.target.prior.location
            self._b_tild = np.hstack([self._L1@self._data, self._L2mu]) 
        
            # Sample from approximate posterior
            e = Normal(mean=np.zeros(len(self._b_tild)), std=1).sample(rng=self.rng)
            y = self._b_tild + e # Perturb data
            sim = CGLS(M, y, samples[:, s], self.maxit, self.tol, self._shift)            
            samples[:, s+1], _ = sim.solve()

            self._print_progress(s+2,N) #s+2 is the sample number, s+1 is index assuming x0 is the first sample
            self._call_callback(samples[:, s+1], s+1)

        # remove burn-in
        samples = samples[:, Nb:]
        
        return samples, None, None
