
def first_non_null(*iterable):
    """
    Returns the first element from the iterable which is not None.
    If all the elements are 'None', 'None' is returned.
    :param iterable: Iterable containing list of elements.
    :return: First non-null element, or None if all elements are 'None'.
    """
    return next((item for item in iterable if item is not None), None)
