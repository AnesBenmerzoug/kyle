from abc import ABC, abstractmethod
from typing import Union, Sequence

import numpy as np

from kyle.transformations import (
    IdentitySimplexAut,
    SimplexAut,
)
from kyle.util import sample_index


class FakeClassifier(ABC):
    def __init__(
        self,
        num_classes: int,
        simplex_automorphism: SimplexAut = None,
        check_io=True,
    ):
        if num_classes < 1:
            raise ValueError(f"{self.__class__.__name__} requires at least two classes")
        self.num_classes = num_classes
        self._rng = np.random.default_rng()

        self._simplex_automorphism: SimplexAut = None
        self.set_simplex_automorphism(simplex_automorphism)
        self.check_io = check_io

    # TODO or not TODO: one could get rid of separate SimplexAut. class in favor of passing a function
    #   pro: the function is less verbose to write, easier for user; contra: naming and state become more convoluted
    def set_simplex_automorphism(self, aut: Union[SimplexAut, None]) -> None:
        """
        :param aut: if None, the identity automorphism will be set
        """
        if aut is None:
            aut = IdentitySimplexAut(self.num_classes)
        if aut.num_classes is not None and aut.num_classes != self.num_classes:
            raise ValueError(f"{aut} has wrong number of classes: {aut.num_classes}")
        self._simplex_automorphism = aut

    @abstractmethod
    def sample_confidences(self, n_samples: int) -> np.ndarray:
        ...

    @property
    def simplex_automorphism(self):
        return self._simplex_automorphism

    def get_sample_arrays(self, n_samples: int):
        """
        Get arrays with ground truth and predicted probabilities

        :param n_samples:
        :return: tuple of arrays of shapes (n_samples,), (n_samples, n_classes)
        """
        confidences = self.sample_confidences(n_samples)
        gt_probabilities = self.simplex_automorphism.transform(
            confidences, check_io=self.check_io
        )
        gt_labels = sample_index(gt_probabilities)
        return gt_labels, confidences

    def __str__(self):
        return f"{self.__class__.__name__}_{self.simplex_automorphism}"


class DirichletFC(FakeClassifier):
    def __init__(
        self,
        num_classes: int,
        alpha: Sequence[float] = None,
        simplex_automorphism: SimplexAut = None,
    ):
        super().__init__(num_classes, simplex_automorphism=simplex_automorphism)

        self._alpha: np.ndarray = None
        self.set_alpha(alpha)

    def set_alpha(self, alpha: Union[np.ndarray, None]):
        """
        :param alpha: if None, the default value of [1, ..., 1] will be set
        """
        if alpha is None:
            alpha = np.ones(self.num_classes)
        else:
            alpha = np.array(alpha)
            if not alpha.shape == (self.num_classes,):
                raise ValueError(f"Wrong shape of alpha: {alpha.shape}")
        self._alpha = alpha

    @property
    def alpha(self):
        return self._alpha

    def sample_confidences(self, n_samples: int) -> np.ndarray:
        return self._rng.dirichlet(self.alpha, size=n_samples)
