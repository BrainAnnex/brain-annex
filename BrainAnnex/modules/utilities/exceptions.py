import sys      # Used to give better feedback on Exceptions
import html     # Used to give better feedback on Exceptions


def exception_helper(ex, safe_html=False) -> str:
    """
    To give better info on an Exception, in the form:
        EXCEPTION_TYPE : THE_INFO_MESSAGE_IN_ex

    The info returned by "ex" is skimpy;
    for example, in case of a key error, all that it returns is the key name!

    :param ex:          The Exemption object
    :param safe_html:   Flag indicating whether to make safe for display in a browser (for example,
                        the exception type may contain triangular brackets)

    :return:    A string with a more detailed explanation of the given Exception
                (prefixed by the Exception type, in an HTML-safe form in case it gets sent to a web page)
                EXAMPLE (as seen when displayed in a browser):
                    <class 'neo4j.exceptions.ClientError'> : THE_INFO_MESSAGE_IN_ex
    """
    (exc_type, _, _) = sys.exc_info()

    if safe_html:
        exc_type = html.escape(str(exc_type))

    return f"{exc_type} : {ex}"
