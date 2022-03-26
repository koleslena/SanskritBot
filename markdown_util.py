def bold(s):
    return '<b>' + s + '</b>'


def starred(s):
    return bold('*') + ' ' + s


def cut_message(str):
    message_size = 2000

    tag = False
    ancore = 0

    stop = min(len(str), message_size)
    for i in range(stop):
        if str[i] == '<' and str[i + 1] == 'a':
            tag = True
            ancore = i
        elif str[i] == '<' and str[i + 1] == '/' and str[i + 2] == 'a':
            tag = False
    if not tag:
        return str[:message_size]
    elif tag:
        return str[:ancore]


def parse_answer(lines, url):
    message_size = 2000
    see_more = f"\n<a href='{url}'>see more</a>"
    lines[0] = bold(lines[0])
    starred_lines = [starred(s) if s[0].isdigit() else s for s in lines]
    str = starred('\n'.join(starred_lines))
    if len(str) > message_size:
        return cut_message(str) + see_more
    return str
