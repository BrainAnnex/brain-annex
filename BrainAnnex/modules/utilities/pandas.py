# Pandas-related utilities


def summarize_dataframe(df, caption = "") -> None:
    """
    Show the first 5 records of the dataset, prefaced by an optional caption,
    and a list of its columns, with counts of the records in each them

    :param df:      A Pandas data frame
    :param caption: Optional string to preface.  If present, the opening statement will read
                                                 "First 5 records of <caption>:"
    :return:        None
    """
    if caption != "":
        caption = f"of `{caption}`"

    if not df.empty:
        print(f"First 5 records {caption}:")

    print(df.head(5))

    if not df.empty:
        print("Columns, with number of records in each (excluding NaN):")
        print(df.count())
    print("List of Columns: ", list(df.columns))