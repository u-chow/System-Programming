ZERO        WORD    0
ONE         WORD    1
THREE       WORD    3
TEN         WORD    10
I           RESW    1
TEMP        RESW    1
Y           RESW    1
MUL_TABLE   RESW    81

        LDX     ZERO
        LDA     ONE
        STA     I
        STA     TEMP

LOOP1   LDA     I
        COMP    TEN
        JEQ     END
        
        LDA     ONE
        STA     TEMP

LOOP2   LDA     I
        MUL     TEMP
        LDX     Y 
        STA     MUL_TABLE,X
        
        LDA     Y
        ADD     THREE
        STA     Y
        
        LDA     TEMP
        ADD     ONE
        STA     TEMP
        
        COMP    TEN
        JLT     LOOP2
        
        LDA     I
        ADD     ONE
        STA     I

        J       LOOP1
        
END     RSUB