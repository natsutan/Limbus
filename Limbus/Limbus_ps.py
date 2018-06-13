# -*- coding: utf-8 -*-
from pascal.pascal import Pascal

#hello_ps = 'pascal_src/assignments.txt'
#hello_ps = 'pascal_src/repeat.txt'
#hello_ps = 'pascal_src/for.txt'
#hello_ps = 'pascal_src/loops.txt'
hello_ps = 'pascal_src/case.txt'



def main():
    pascal = Pascal('execute', hello_ps, 'xi')
#    pascal = Pascal('compile', hello_ps, 'xi')


if __name__ == '__main__':
    main()




