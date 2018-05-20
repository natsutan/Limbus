# -*- coding: utf-8 -*-
from pascal import Pascal

#hello_ps = 'pascal_src/scannertest.txt'
hello_ps = 'pascal_src/comment.txt'

def main():
#    pascal = Pascal('execute', hello_ps, {})
    pascal = Pascal('compile', hello_ps, {})


if __name__ == '__main__':
    main()




