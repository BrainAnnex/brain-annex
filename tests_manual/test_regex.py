import re                   # For REGEX

def test_regex():
    """
    Tester function for regex

    :return:
    """
    file_contents = "HERE DEFINE STRING TO PARSE"

    pattern_1 = R"\n([a-zA-Z ]+)@@@\n"          # Full name
    pattern_2 = ".+ profile\n"                  # Throwaway line
    pattern_3 = "---1st1st degree connection\n" # Throwaway line
    pattern_4 = "(.+)\n(.+)\n"                  # Role and location (across 2 lines)

    pattern = pattern_1 + pattern_2 + pattern_3 + pattern_4
    #pattern = R"\n([a-zA-Z ]+)@@@\n.+ profile\n---1st1st degree connection\n(.+)\n(.+)"  # R"---1st1st degree connection\n(.+)"

    all_matches = re.findall(pattern, file_contents)    # , re.DOTALL
    if all_matches:     # If the list is not empty, i.e. if matches were found
        print(f"{len(all_matches)} MATCHES found")
        for matchInstance in all_matches:   # Consider each match in turn
            print("Overall Match: " , matchInstance)     # This will be a tuple of capture groups
    else:
        print("NO MATCHES found")
