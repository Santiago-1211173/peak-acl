grammar ACL;

/* ----------  PARSER  ---------- */

message      : LPAREN performative param* RPAREN            #ACLmessage; 
performative : SYMBOL                                       #ACLperformative; 
param        : COLON SYMBOL value                           #ACLparam;
value        : SYMBOL                                       #Atom
             | STRING                                       #String 
             | message                                      #NestedMessage  
             | LPAREN value+ RPAREN                         #ListValue 
             ;                       

/* ----------  LEXER  ----------- */

LPAREN  : '(' ;
RPAREN  : ')' ;
COLON   : ':' ;
STRING  : '"' (~["\\]  | '\\' .)* '"' ;                
SYMBOL  : [a-zA-Z0-9_@./+-][a-zA-Z0-9_@./:+-]* ;
WS      : [ \t\r\n]+ -> skip ;
