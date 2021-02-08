from concurrent.futures.thread import ThreadPoolExecutor

def p(a, b) -> bool:
    c = a * b
    return True

def main():
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(p, 323, 1235)
        print(future.result())

if __name__ == '__main__':
    main()
