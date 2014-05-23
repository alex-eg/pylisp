# Lexer

tokens = (
    'LPAREN', 'RPAREN', 'NUMBER', 'SYMBOL'
)

t_LPAREN = r'\('
t_RPAREN = r'\)'

def t_NUMBER(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t

t_ignore = " \t" # ignore tabs and spaces

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count('\n')

def t_SYMBOL(t):
    r'[^0-9\(\)][^ \n\(\)]*' # everything else is a symbol
    return t

def t_error(t):
    print("Illegal character {0}".format(t.value[0]))
    t.lexer.skip(1)

import ply.lex as lex
lex.lex()

# Parser

def p_expression(t):
    '''expression : atom
                  | list'''
    t[0] = t[1]

def p_atom(t):
    '''atom : NUMBER 
            | SYMBOL'''
    if isinstance(t[1], int):
        t[0] = ('num', t[1])
    else:
        t[0] = ('sym', t[1])

def p_list(t):
    '''list : LPAREN RPAREN
            | LPAREN expression_list RPAREN'''
    if t[2] == ')':
        t[0] = ('sym', 'nil')
    else: t[0] = ('list', t[2])

def p_expression_list(t):
    '''expression_list : expression
                       | expression_list expression'''
    if len(t) == 2: t[0] = [t[1]]
    else: 
        t[0] = t[1]
        t[0].append(t[2])    
    
def p_error(t):
    if t == None: print ("Unexpected end of input!")
    else: 
        print("Syntax error at {0}".format(t.value))

import ply.yacc as yacc
yacc.yacc()

# Type checking

def is_list(n):
    return n[0] == 'list'

def is_num(n):
    return n[0] == 'num'

def is_sym(n):
    return n[0] == 'sym'

def p_val(n):
    return n[1]

# Evaluation

symtab = { } # symbol table

def pylisp_eval(expr):
    expr_type = expr[0]
    if expr_type == 'num':
        return expr[1]
    elif expr_type == 'sym':
        try:
            return symtab[expr[1]]
        except KeyError:
            print("Symbol {0} not defined".format(expr[1]))
            raise
    elif expr_type == 'list':
        return pylisp_eval_list(expr[1])
    else:
        print("Unknown expression type {0}".format(expr_type))
        raise

from types import *

def pylisp_eval_list(list_contents):
    global symtab
    fun_name = list_contents[0][1]
    fun = None
    try:
        fun = symtab[fun_name]
    except KeyError:
        print("Function {0} not defined".format(fun_name))
    if type(fun) == FunctionType:
        return fun(*list_contents[1:])
    elif type(fun) == tuple: # user-defined function
        fun_args = fun[0]

        parameters = list(map(pylisp_eval, list_contents[1:]))

        if not len(parameters) == len(fun_args):
            print ("Function {0} called with {1} arguments, but wants exactly {2}".format(fun_name, len(parameters), len(fun_args)))
            raise

        bind_formal_parameters = {}
        for i in range(len(fun_args)):
            bind_formal_parameters[fun_args[i]] = parameters[i]
        old_symtab = symtab
        symtab.update(bind_formal_parameters)
        
        fun_body = fun[1]
        value = pylisp_eval(fun_body)
        symtab = old_symtab
        return value
    else: pass

# Built-ins

import operator as op
from functools import reduce

def pylisp_plus(*par_list):
    vals = map(pylisp_eval, par_list)
    return reduce(op.add, vals, 0)

def pylisp_sub(*par_list):
    vals = map(pylisp_eval, par_list)
    return reduce(op.sub, vals, 0)

def pylisp_mul(*par_list):
    vals = map(pylisp_eval, par_list)
    return reduce(op.mul, vals, 1)

def pylisp_eq(*par_list):
    vals = map(pylisp_eval, par_list)
    result = reduce(op.eq, vals, True)
    return result

def pylisp_define(*par_list):
    if len(par_list) != 2:
        print("Bad define statement")
        raise

    if is_sym(par_list[0]):
        var_name = par_list[0][1]
        symtab[var_name] = pylisp_eval(par_list[1])
        return symtab[var_name]
    elif is_list(par_list[0]):
        fun_signature_list = p_val(par_list[0])
        if not is_sym(fun_signature_list[0]):
            print("Function name must be a symbol")
            raise
        fun_name = p_val(fun_signature_list[0])
        check_arguments = reduce(lambda a, x: is_sym(x) and a, fun_signature_list, True)
        if not check_arguments:
            print("Arguments name must be symbols")
            raise
        
        fun_arg_names = list(map(p_val, fun_signature_list[1:]))
        
        fun_body = par_list[1]
        
        symtab[fun_name] = (fun_arg_names, fun_body)            
    else:
        print("Cannot define a literal")
        raise

symtab['define'] = pylisp_define
symtab['+'] = pylisp_plus
symtab['-'] = pylisp_sub
symtab['*'] = pylisp_mul
symtab['='] = pylisp_eq

while 1:
    try:
        s = input('pylisp > ')
    except EOFError:
        break
    g = yacc.parse(s)
    try:
        print(pylisp_eval(g))
    except Exception as e:
        print ("Unexpected exception: {0}".format(e))
