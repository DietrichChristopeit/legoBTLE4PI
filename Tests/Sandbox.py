
if __name__ == '__main__':

    file = open('/home/pi/titles.txt', "r")
    lines: [str] = file.readlines()
    ret: [str] = []
    print("Original:\n", "".join(x for x in lines))
    for line in lines:
        words:[str] = line.strip().split(sep=' ')
        t: str = ''
        for word in words:
            t += word[0]
        ret.append(t)

    print(ret)
