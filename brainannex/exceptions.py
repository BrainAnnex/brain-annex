import sys      # Used to give better feedback on Exceptions


def exception_helper(ex) -> str:
    """
    To give better info on an Exception, in the form:
        EXCEPTION_TYPE : THE_INFO_MESSAGE_IN_ex

    The info returned by "ex" is skimpy;
    for example, in case of a key error, all that it returns is the key name!

    :param ex:  The Exemption object

    :return:    A string with a more detailed explanation of the given Exception
                (prefixed by the Exception type)
                EXAMPLE:
                    class 'neo4j.exceptions.ClientError' : THE_INFO_MESSAGE_IN_ex
    """
    (exc_type, _, _) = sys.exc_info()

    friendly_error = f"{exc_type} : {ex}"

    # If triangular brackets are present, turn them into round ones
    # (to prevent problems if shown on a web page)
    return friendly_error.replace("<", "(").replace(">", ")")
