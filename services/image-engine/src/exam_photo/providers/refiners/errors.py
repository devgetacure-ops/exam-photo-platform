class RefinementError(RuntimeError):
    """Base exception for mask refinement errors."""

    pass


class RefinementInputError(RefinementError):
    """Raised when the input coarse or probability mask is invalid."""

    pass


class RefinementOutputError(RefinementError):
    """Raised when the generated refined masks fail validation."""

    pass
