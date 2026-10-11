class BankError(Exception):
    """Base exception for the simulation."""

class AuthenticationError(BankError): pass
class InsufficientFundsError(BankError): pass
class InvalidAmountError(BankError): pass
class AccountNotFoundError(BankError): pass
class AuthorizationError(BankError): pass
