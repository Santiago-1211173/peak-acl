grammar ACL;

/*
 * Gramática para FIPA ACL.
 * Reconhece a estrutura externa da mensagem ACL e valores  genéricos.
 * Slots FIPA (sender, receiver, reply-to, …) são tratados no Visitor em Python.
 */

/* ----------  PARSER  ---------- */

message
    : LPAREN performative param* RPAREN            #ACLmessage
    ;

performative
    : SYMBOL                                       #ACLperformative
    ;

param
    : COLON SYMBOL value                           #ACLparam
    ;

value
    : SYMBOL                                       #Atom
    | STRING                                       #String
    | message                                      #NestedMessage
    | LPAREN value+ RPAREN                         #ListValue
    ;

/* ----------  LEXER  ----------- */

LPAREN  : '(' ;
RPAREN  : ')' ;
COLON   : ':' ;
STRING  : '"' (~["\\]  | '\\' .)* '"' ;

// Inclui @ . / : + - para AIDs e URLs
SYMBOL  : [a-zA-Z0-9_@./+\-] [a-zA-Z0-9_@./:+\-]* ;

WS      : [ \t\r\n]+ -> skip ;
