def yield_or_print_output(obj: str, yield_output: bool):
    """Yield object string if yield_output is true else print

    Args:
        obj (str): String to be printed or yielded
        yield_output (bool): If true, obj string would be yielded, else it would be printed

    Yields:
        string: Output to be yielded from the function based on obj string
    """

    if yield_output:
        yield obj
    # else:
    #     print(obj, end='')
