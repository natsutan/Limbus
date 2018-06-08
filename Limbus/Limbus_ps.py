# -*- coding: utf-8 -*-
from pascal.pascal import Pascal

#hello_ps = 'pascal_src/assignments.txt'
#hello_ps = 'pascal_src/case.txt'
#hello_ps = 'pascal_src/if.txt'
#hello_ps = 'pascal_src/iferrors.txt'
hello_ps = 'pascal_src/loops.txt'



def main():
    pascal = Pascal('execute', hello_ps, 'xi')
#    pascal = Pascal('compile', hello_ps, 'xi')


if __name__ == '__main__':
    main()




