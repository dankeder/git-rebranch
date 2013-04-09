TODO
====

- prior to creating a statefile, it should check that all the required branches exist

- create a man page

Use class-based exceptions.

String exceptions in new code are forbidden, because this language feature is
being removed in Python 2.6.

Modules or packages should define their own domain-specific base exception
class, which should be subclassed from the built-in Exception class. Always
include a class docstring. E.g.:

class MessageError(Exception):
    """Base class for errors in the email package."""

	Class naming conventions apply here, although you should add the suffix
	"Error" to your exception classes, if the exception is an error. Non-error
	exceptions need no special suffix.

