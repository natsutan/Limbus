# -*- coding: utf-8 -*-
from pascal.pascal import Pascal

#hello_ps = 'pascal_src/assignments.txt'
#hello_ps = 'pascal_src/declarations.txt'
hello_ps = 'pascal_src/block_test.txt'

def main():
    pascal = Pascal('execute', hello_ps, 'xi')
#    pascal = Pascal('compile', hello_ps, 'xi')


if __name__ == '__main__':
    main()




