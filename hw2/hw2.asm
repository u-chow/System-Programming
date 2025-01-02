MUL_TABLE RESW  81
        LDX     #0
        LDA     #1
        LDT     #1
        LDS     #0

LOOP1   LDT    #243
        COMPR  X,T
        JEQ    END
        LDT    #1
        LDA    #1
        ADDR    T,S
LOOP2   LDT    #1
        MULR    S,T
        MULR    A,T
        STT    MUL_TABLE,X
        LDT    #3
        ADD    #1
        ADDR    T,X
        COMP   #10
        JLT     LOOP2

        J       LOOP1

END     RSUB