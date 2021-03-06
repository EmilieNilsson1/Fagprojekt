import numpy as np
from scipy.sparse import csc_matrix
from scipy.sparse import hstack
from scipy.linalg import solve
from cuqi.samples import Samples, CUQIarray
from cuqi.geometry import Geometry, StepExpansion, KLExpansion, CustomKL, Continuous1D, _DefaultGeometry, Continuous2D, Discrete, Image2D
import cuqi
import matplotlib.pyplot as plt

class Model(object):
    """Generic model defined by a forward operator.

    Parameters
    -----------
    forward : 2D ndarray or callable function.
        Forward operator.

    range_geometry : integer or cuqi.geometry.Geometry
        If integer is given a _DefaultGeometry is created with dimension of the integer.

    domain_geometry : integer or cuqi.geometry.Geometry
        If integer is given a _DefaultGeometry is created with dimension of the integer.

    gradient : callable function
        Jacobian of the forward operator at a given point and direction.

    Attributes
    -----------
    range_geometry : cuqi.geometry.Geometry
        The geometry representing the range.

    domain_geometry : cuqi.geometry.Geometry
        The geometry representing the domain.

    Methods
    -----------
    :meth:`forward` the forward operator.
    :meth:`range_dim` the dimension of the range.
    :meth:`domain_dim` the dimension of the domain.
    """
    def __init__(self, forward, range_geometry, domain_geometry, gradient=None):

        #Check if input is callable
        if callable(forward) is not True:
            raise TypeError("Forward needs to be callable function of some kind")
        
        #Check if input is callable
        if (gradient is not None) and (callable(gradient) is not True):
            raise TypeError("Gradient needs to be callable function of some kind")
 
        #Store forward func
        self._forward_func = forward
        self._gradient_func = gradient
         
        #Store range_geometry
        if isinstance(range_geometry, int):
            self.range_geometry = _DefaultGeometry(grid=range_geometry)
        elif isinstance(range_geometry, Geometry):
            self.range_geometry = range_geometry
        elif range_geometry is None:
            raise AttributeError("The parameter 'range_geometry' is not specified by the user and it connot be inferred from the attribute 'forward'.")
        else:
            raise TypeError("The parameter 'range_geometry' should be of type 'int' or 'cuqi.geometry.Geometry'.")

        #Store domain_geometry
        if isinstance(domain_geometry, int):
            self.domain_geometry = _DefaultGeometry(grid=domain_geometry)
        elif isinstance(domain_geometry, Geometry):
            self.domain_geometry = domain_geometry
        elif domain_geometry is None:
            raise AttributeError("The parameter 'domain_geometry' is not specified by the user and it connot be inferred from the attribute 'forward'.")
        else:
            raise TypeError("The parameter 'domain_geometry' should be of type 'int' or 'cuqi.geometry.Geometry'.")

        # Store non_default_args of the forward operator for faster caching when checking for those arguments.
        self._non_default_args = cuqi.utilities.get_non_default_args(self)

    @property
    def domain_dim(self): 
        return self.domain_geometry.dim

    @property
    def range_dim(self): 
        return self.range_geometry.dim
    
    def forward(self, x, is_par=True):
        """ Forward function of the model.
        
        Forward converts the input to function values (if needed) using the domain geometry of the model.
        Forward converts the output function values to parameters using the domain geometry of the model.

        Parameters
        ----------
        x : ndarray or cuqi.samples.CUQIarray
            The model input.

        is_par : bool
            If True the input is assumed to be parameters.
            If False the input is assumed to be function values.

        Returns
        -------
        ndarray or cuqi.samples.CUQIarray
            The model output. Always returned as parameters.
        """

        # Convert input to function values
        if type(x) is CUQIarray and not isinstance(x.geometry, _DefaultGeometry):
            x = x.funvals
        else:
            if is_par:
                x = self.domain_geometry.par2fun(x)

        # Compute foward (if Samples we compute for each sample)
        # TODO: Check if this can be done all-at-once for computational speed-up
        if isinstance(x,Samples):
            Ns = x.samples.shape[-1]
            data_samples = np.zeros((self.range_dim,Ns))
            for s in range(Ns):
                data_samples[:,s] = self._forward_func(x.samples[:,s])
            return Samples(data_samples,geometry=self.range_geometry)
        else:
            out = self._forward_func(x)
            out = self.range_geometry.fun2par(out) #Convert to parameters
            if type(x) is CUQIarray:
                out = CUQIarray(out, is_par=True, geometry=self.range_geometry)
            return out

    def __call__(self,x):
        return self.forward(x)

    def gradient(self, direction, wrt):
        """ Gradient of the forward operator.

        For non-linear models the gradient is computed using the
        forward operator and the Jacobian of the forward operator.

        Parameters
        ----------
        direction : ndarray
            The direction to compute the gradient. The Jacobian is applied to this direction.

        wrt : ndarray
            The point to compute the Jacobian at. This is only used for non-linear models.
        
        """
        if self._gradient_func is None:
            raise NotImplementedError("Gradient is not implemented for this model.")
        return self._gradient_func(direction, wrt)

    # approximate the Jacobian matrix of callable function func
    def approx_jacobian(self, x, epsilon=np.sqrt(np.finfo(np.float).eps)):
        # x       - The state vector
        # func    - A vector-valued function of the form f(x,*args)
        # epsilon - The peturbation used to determine the partial derivatives
        # The approximation is done using forward differences
        x0 = np.asfarray(x)
        f0 = self.forward(x0)
        jac = np.zeros([len(x0), len(f0)])
        dx = np.zeros(len(x0))
        for i in range(len(x0)):
            dx[i] = epsilon
            jac[i] = (self.forward(x0+dx) - f0)/epsilon
            dx[i] = 0.0
        return jac.T
    
    def __len__(self):
        return self.range_dim

    def __repr__(self) -> str:
        return "CUQI {}: {} -> {}. Forward parameters: {}".format(self.__class__.__name__,self.domain_geometry,self.range_geometry,cuqi.utilities.get_non_default_args(self))
    
class LinearModel(Model):
    """Model based on a Linear forward operator.

    Parameters
    -----------
    forward : 2D ndarray or callable function.
        Forward operator.

    adjoint : 2d ndarray or callable function. (optional if matrix is passed as forward)

    range_geometry : integer or cuqi.geometry.Geometry (optional)
        If integer is given a _DefaultGeometry is created with dimension of the integer.

    domain_geometry : integer or cuqi.geometry.Geometry (optional)
        If integer is given a _DefaultGeometry is created with dimension of the integer.

    Attributes
    -----------
    range_geometry : cuqi.geometry.Geometry
        The geometry representing the range.

    domain_geometry : cuqi.geometry.Geometry
        The geometry representing the domain.

    Methods
    -----------
    :meth:`forward` the forward operator.
    :meth:`range_dim` the dimension of the range.
    :meth:`domain_dim` the dimension of the domain.
    :meth:`get_matrix` returns an ndarray with the matrix representing the forward operator.
    """
    # Linear forward model with forward and adjoint (transpose).
    
    def __init__(self,forward,adjoint=None,range_geometry=None,domain_geometry=None):
        #Assume forward is matrix if not callable (TODO: add more checks)
        if not callable(forward):      
            forward_func = lambda x: self._matrix@x
            adjoint_func = lambda y: self._matrix.T@y
            matrix = forward
        else:
            forward_func = forward
            adjoint_func = adjoint
            matrix = None

        #Check if input is callable
        if callable(adjoint_func) is not True:
            raise TypeError("Adjoint needs to be callable function of some kind")

        # Use matrix to derive range_geometry and domain_geometry
        if matrix is not None:
            if range_geometry is None:
                range_geometry = _DefaultGeometry(grid=matrix.shape[0])
            if domain_geometry is None:
                domain_geometry = _DefaultGeometry(grid=matrix.shape[1])  

        #Initialize Model class
        super().__init__(forward_func,range_geometry,domain_geometry)

        #Add adjoint
        self._adjoint_func = adjoint_func

        #Store matrix privately
        self._matrix = matrix

        # if matrix is not None: 
        #     assert(self.range_dim  == matrix.shape[0]), "The parameter 'forward' dimensions are inconsistent with the parameter 'range_geometry'"
        #     assert(self.domain_dim == matrix.shape[1]), "The parameter 'forward' dimensions are inconsistent with parameter 'domain_geometry'"

    def adjoint(self, y, is_par=True):
        """ Adjoint of the model.
        
        Adjoint converts the input to function values (if needed) using the range geometry of the model.
        Adjoint converts the output function values to parameters using the range geometry of the model.

        Parameters
        ----------
        y : ndarray or cuqi.samples.CUQIarray
            The adjoint model input.

        Returns
        -------
        ndarray or cuqi.samples.CUQIarray
            The adjoint model output. Always returned as parameters.
        """
        # Convert input to function values
        if type(y) is CUQIarray and not isinstance(y.geometry, _DefaultGeometry):
            y = y.funvals
        else:
            if is_par:
                y = self.range_geometry.par2fun(y) #Convert to function values

        # Compute adjoint
        out = self._adjoint_func(y)

        # Convert output to parameters
        out = self.domain_geometry.fun2par(out) #Convert to parameters
        if type(y) is CUQIarray:
            out = CUQIarray(out, is_par=True, geometry=self.domain_geometry)
        return out


    def get_matrix(self):
        if self._matrix is not None: #Matrix exists so return it
            return self._matrix
        else:
            #TODO: Can we compute this faster while still in sparse format?
            mat = csc_matrix((self.range_dim,0)) #Sparse (m x 1 matrix)
            e = np.zeros(self.domain_dim)
            
            # Stacks sparse matrices on csc matrix
            for i in range(self.domain_dim):
                e[i] = 1
                col_vec = self.forward(e)
                mat = hstack((mat,col_vec[:,None])) #mat[:,i] = self.forward(e)
                e[i] = 0

            #Store matrix for future use
            self._matrix = mat

            return self._matrix

    def gradient(self, direction, wrt=None):
        """ Gradient of the model.

        In the case of a linear model, the gradient is computed using the adjoint.

        Parameters
        ----------
        direction : ndarray
            The direction to compute the gradient. The Jacobian is applied to this direction.

        wrt : ndarray
            The point to compute Jacobian at. This is only used for non-linear models.
        
        """
        #Avoid complicated geometries that change the gradient.
        if not type(self.domain_geometry) in [_DefaultGeometry, Continuous1D, Continuous2D, Discrete, Image2D]:
            raise NotImplementedError("Gradient not implemented for model {} with domain geometry {}".format(self,self.domain_geometry))

        return self.adjoint(direction)
    
    def __matmul__(self, x):
        return self.forward(x)

    @property
    def T(self):
        """Transpose of linear model. Returns a new linear model acting as the transpose."""
        transpose = LinearModel(self.adjoint,self.forward,self.domain_geometry,self.range_geometry)
        if self._matrix is not None:
            transpose._matrix = self._matrix.T
        return transpose
        

class PDEModel(Model):
    """
    Model based on an underlying cuqi.pde.PDE.
    In the forward operation the PDE is assembled, solved and observed.
    
    Parameters
    -----------
    forward : 2D ndarray or callable function.
        Forward operator assembling, solving and observing the pde.

    range_geometry : integer or cuqi.geometry.Geometry (optional)
        If integer is given a _DefaultGeometry is created with dimension of the integer.

    domain_geometry : integer or cuqi.geometry.Geometry (optional)
        If integer is given a _DefaultGeometry is created with dimension of the integer.

    Attributes
    -----------
    range_geometry : cuqi.geometry.Geometry
        The geometry representing the range.

    domain_geometry : cuqi.geometry.Geometry
        The geometry representing the domain.

    Methods
    -----------
    :meth:`forward` the forward operator.
    :meth:`range_dim` the dimension of the range.
    :meth:`domain_dim` the dimension of the domain.
    """
    def __init__(self, PDE, range_geometry, domain_geometry):
        #....
        if not isinstance(PDE,cuqi.pde.PDE):
            raise ValueError("PDE needs to be a cuqi PDE.")

        super().__init__(self._forward_func, range_geometry, domain_geometry)

        self.pde = PDE

    def _forward_func(self,x):
        
        self.pde.assemble(parameter=x)

        sol, info = self.pde.solve()

        obs = self.pde.observe(sol)

        return obs

    # Add the underlying PDE class name to the repr.
    def __repr__(self) -> str:
        return super().__repr__()+". PDE: {}".format(self.pde.__class__.__name__)
        
