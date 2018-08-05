# -*- coding: utf-8 -*-
from pascal.pascal import Pascal

#hello_ps = 'pascal_src/assignments.txt'
#hello_ps = 'pascal_src/declarations.txt'
hello_ps = 'pascal_src/routines.pas'

def main():
    pascal = Pascal('execute', hello_ps, 'xlicraf')
#    pascal = Pascal('compile', hello_ps, 'xi')


if __name__ == '__main__':
    main()




