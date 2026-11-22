HELP = "text を大文字にして出力する（--first で先頭 1 文字だけ）"


def run(args):
    first = "--first" in args
    text = " ".join(a for a in args if a != "--first")
    if first:
        print(text[0].upper() + text[1:])
    else:
        print(text.upper())
    return 0
