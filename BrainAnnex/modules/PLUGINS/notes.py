import re


class Notes:

    @classmethod
    def new_content_item_in_category_SUCCESSFUL(cls, item_id: int, pars: dict) -> None:
        """

        :param item_id:
        :param pars:
        :return:        None
        """
        body = pars["body"]

        # printing original string
        print("The original string is : " +  body)

        # using regex( findall() )
        # to extract words from string
        res = re.findall(r'\w+', body)

        # printing result
        print("The list of words is : " +  str(res))

        # TODO: index_note_contents
