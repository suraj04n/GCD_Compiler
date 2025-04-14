import re
import sys
from collections import defaultdict, Counter

class Token:
    def __init__(self, type_, value, line, position):
        self.type = type_
        self.value = value
        self.line = line
        self.position = position
    
    def __str__(self):
        return f"Token({self.type}, '{self.value}', line={self.line}, pos={self.position})"
    
    def __repr__(self):
        return self.__str__()

class Lexer:
    def __init__(self, text):
        self.text = text
        self.position = 0
        self.current_char = self.text[self.position] if self.text else None
        self.line = 1
        self.line_pos = 1
        self.tokens = []
        self.errors = []

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.line_pos = 0
        
        self.position += 1
        self.line_pos += 1
        
        if self.position >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.position]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        # Skip single-line comment
        if self.current_char == '/' and self.peek() == '/':
            self.advance()
            self.advance()
            while self.current_char is not None and self.current_char != '\n':
                self.advance()
            return True
        # Skip multi-line comment
        elif self.current_char == '/' and self.peek() == '*':
            self.advance()
            self.advance()
            while self.current_char is not None:
                if self.current_char == '*' and self.peek() == '/':
                    self.advance()
                    self.advance()
                    return True
                self.advance()
            self.errors.append(f"Error: Unclosed comment at line {self.line}")
            return True
        return False

    def peek(self):
        peek_pos = self.position + 1
        if peek_pos >= len(self.text):
            return None
        return self.text[peek_pos]

    def id_(self):
        # Handle identifiers and keywords
        result = ''
        line = self.line
        position = self.line_pos
        
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        token_type = self._get_keyword_or_id(result)
        return Token(token_type, result, line, position)

    def _get_keyword_or_id(self, value):
        keywords = {
            'int': 'INT_TYPE',
            'float': 'FLOAT_TYPE',
            'if': 'IF',
            'else': 'ELSE',
            'while': 'WHILE',
            'for': 'FOR',
            'return': 'RETURN',
            'begin': 'BEGIN',
            'end': 'END',
        }
        return keywords.get(value, 'ID')

    def number(self):
        result = ''
        line = self.line
        position = self.line_pos
        
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        
        if self.current_char == '.' and self.peek() and self.peek().isdigit():
            result += self.current_char
            self.advance()
            
            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()
            
            return Token('FLOAT_CONST', float(result), line, position)
        
        return Token('INT_CONST', int(result), line, position)

    def get_next_token(self):
        while self.current_char is not None:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            # Skip comments
            if self.current_char == '/' and (self.peek() == '/' or self.peek() == '*'):
                if self.skip_comment():
                    continue
            
            # Handle identifiers and keywords
            if self.current_char.isalpha() or self.current_char == '_':
                return self.id_()
            
            # Handle numbers
            if self.current_char.isdigit():
                return self.number()
            
            # Handle symbols
            if self.current_char == ';':
                token = Token('SEMICOLON', ';', self.line, self.line_pos)
                self.advance()
                return token
            
            if self.current_char == ',':
                token = Token('COMMA', ',', self.line, self.line_pos)
                self.advance()
                return token
            
            if self.current_char == '(':
                token = Token('LPAREN', '(', self.line, self.line_pos)
                self.advance()
                return token
            
            if self.current_char == ')':
                token = Token('RPAREN', ')', self.line, self.line_pos)
                self.advance()
                return token
            
            if self.current_char == '{':
                token = Token('LBRACE', '{', self.line, self.line_pos)
                self.advance()
                return token
            
            if self.current_char == '}':
                token = Token('RBRACE', '}', self.line, self.line_pos)
                self.advance()
                return token
            
            if self.current_char == '=':
                line = self.line
                position = self.line_pos
                self.advance()
                if self.current_char == '=':
                    token = Token('EQ', '==', line, position)
                    self.advance()
                else:
                    token = Token('ASSIGN', '=', line, position)
                return token
            
            if self.current_char == '+':
                line = self.line
                position = self.line_pos
                self.advance()
                if self.current_char == '+':
                    token = Token('INC', '++', line, position)
                    self.advance()
                else:
                    token = Token('PLUS', '+', line, position)
                return token
            
            if self.current_char == '-':
                line = self.line
                position = self.line_pos
                self.advance()
                if self.current_char == '-':
                    token = Token('DEC', '--', line, position)
                    self.advance()
                else:
                    token = Token('MINUS', '-', line, position)
                return token
            
            if self.current_char == '*':
                token = Token('MUL', '*', self.line, self.line_pos)
                self.advance()
                return token
            
            if self.current_char == '/':
                token = Token('DIV', '/', self.line, self.line_pos)
                self.advance()
                return token
            
            if self.current_char == '%':
                token = Token('MOD', '%', self.line, self.line_pos)
                self.advance()
                return token
            
            if self.current_char == '<':
                line = self.line
                position = self.line_pos
                self.advance()
                if self.current_char == '=':
                    token = Token('LTE', '<=', line, position)
                    self.advance()
                else:
                    token = Token('LT', '<', line, position)
                return token
            
            if self.current_char == '>':
                line = self.line
                position = self.line_pos
                self.advance()
                if self.current_char == '=':
                    token = Token('GTE', '>=', line, position)
                    self.advance()
                else:
                    token = Token('GT', '>', line, position)
                return token
            
            if self.current_char == '!':
                line = self.line
                position = self.line_pos
                self.advance()
                if self.current_char == '=':
                    token = Token('NEQ', '!=', line, position)
                    self.advance()
                    return token
            
            if self.current_char == '&' and self.peek() == '&':
                token = Token('AND', '&&', self.line, self.line_pos)
                self.advance()
                self.advance()
                return token
            
            if self.current_char == '|' and self.peek() == '|':
                token = Token('OR', '||', self.line, self.line_pos)
                self.advance()
                self.advance()
                return token
            
            # Handle identifier 'relop' as a special case for the example
            if self.current_char == 'r' and self.position + 4 < len(self.text) and self.text[self.position:self.position+5] == 'relop':
                token = Token('RELOP', 'relop', self.line, self.line_pos)
                for _ in range(5):
                    self.advance()
                return token
            
            # Handle identifier 'expr' as a special case for the example
            if self.current_char == 'e' and self.position + 3 < len(self.text) and self.text[self.position:self.position+4] == 'expr':
                token = Token('EXPR', 'expr', self.line, self.line_pos)
                for _ in range(4):
                    self.advance()
                return token
            
            # Error: Invalid character
            error_msg = f"Error: Invalid character '{self.current_char}' at line {self.line}, position {self.line_pos}"
            self.errors.append(error_msg)
            self.advance()
        
        return Token('EOF', None, self.line, self.line_pos)

    def tokenize(self):
        token = self.get_next_token()
        while token.type != 'EOF':
            self.tokens.append(token)
            token = self.get_next_token()
        self.tokens.append(token)  # Add EOF token
        return self.tokens

class SyntaxNode:
    def __init__(self, type_, value=None, children=None):
        self.type = type_
        self.value = value
        self.children = children if children is not None else []
    
    def add_child(self, node):
        self.children.append(node)
    
    def __str__(self):
        if self.value is not None:
            return f"{self.type}({self.value})"
        return self.type

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_idx = 0
        self.current_token = self.tokens[0] if tokens else None
        self.errors = []
        self.symbol_table = {}  # Symbol table for variable declarations
    
    def error(self, message):
        if self.current_token:
            error_msg = f"Error at line {self.current_token.line}, position {self.current_token.position}: {message}"
        else:
            error_msg = f"Error: {message}"
        self.errors.append(error_msg)
        return SyntaxNode("ERROR", error_msg)

    def eat(self, token_type):
        if self.current_token.type == token_type:
            old_token = self.current_token
            self.current_token_idx += 1
            if self.current_token_idx < len(self.tokens):
                self.current_token = self.tokens[self.current_token_idx]
            else:
                self.current_token = None
            return old_token
        else:
            self.error(f"Expected {token_type}, got {self.current_token.type}")
            return None

    def parse(self):
        return self.program()

    def program(self):
        node = SyntaxNode("Program")
        
        # Main function
        node.add_child(self.main_function())
        
        return node

    def main_function(self):
        node = SyntaxNode("MainFunction")
        
        # int
        self.eat('INT_TYPE')
        
        # main
        if self.current_token.type == 'ID' and self.current_token.value == 'main':
            node.add_child(SyntaxNode("Identifier", self.current_token.value))
            self.eat('ID')
        else:
            self.error("Expected 'main' identifier")
        
        # ()
        self.eat('LPAREN')
        self.eat('RPAREN')
        
        # begin
        if self.current_token.type == 'BEGIN':
            self.eat('BEGIN')
        else:
            self.error("Expected 'begin'")
        
        # Function body
        node.add_child(self.block())
        
        # end
        if self.current_token and self.current_token.type == 'END':
            self.eat('END')
        else:
            self.error("Expected 'end'")
        
        return node

    def block(self):
        node = SyntaxNode("Block")
        
        # Variable declarations
        if self.current_token and self.current_token.type == 'INT_TYPE':
            node.add_child(self.variable_declaration())
        
        # If statement
        if self.current_token and self.current_token.type == 'IF':
            node.add_child(self.if_statement())
        
        # For loop
        if self.current_token and self.current_token.type == 'FOR':
            node.add_child(self.for_loop())
        
        return node

    def variable_declaration(self):
        node = SyntaxNode("VariableDeclaration")
        
        # int
        type_node = SyntaxNode("Type", self.current_token.value)
        node.add_child(type_node)
        self.eat('INT_TYPE')
        
        # Variable list
        variables_node = self.variable_list()
        node.add_child(variables_node)
        
        # Add variables to symbol table
        for child in variables_node.children:
            if child.type == "Identifier":
                var_name = child.value
                self.symbol_table[var_name] = {"type": "int", "scope": "local"}
        
        # ;
        self.eat('SEMICOLON')
        
        return node

    def variable_list(self):
        node = SyntaxNode("VariableList")
        
        # First variable
        if self.current_token and self.current_token.type == 'ID':
            node.add_child(SyntaxNode("Identifier", self.current_token.value))
            self.eat('ID')
        else:
            self.error("Expected identifier")
        
        # Additional variables
        while self.current_token and self.current_token.type == 'COMMA':
            self.eat('COMMA')
            if self.current_token and self.current_token.type == 'ID':
                node.add_child(SyntaxNode("Identifier", self.current_token.value))
                self.eat('ID')
            else:
                self.error("Expected identifier after comma")
        
        return node

    def if_statement(self):
        node = SyntaxNode("IfStatement")
        
        # if
        self.eat('IF')
        
        # (condition)
        self.eat('LPAREN')
        node.add_child(self.condition())
        self.eat('RPAREN')
        
        # Body
        node.add_child(self.assignment())
        
        return node

    def condition(self):
        node = SyntaxNode("Condition")
        
        # Handle the special case for this example
        if (self.current_token and self.current_token.type == 'EXPR' and 
            self.tokens[self.current_token_idx + 1].type == 'RELOP' and 
            self.tokens[self.current_token_idx + 2].type == 'EXPR'):
            
            node.add_child(SyntaxNode("Expression", self.current_token.value))
            self.eat('EXPR')
            
            node.add_child(SyntaxNode("RelationalOperator", self.current_token.value))
            self.eat('RELOP')
            
            node.add_child(SyntaxNode("Expression", self.current_token.value))
            self.eat('EXPR')
        else:
            self.error("Expected 'expr relop expr' pattern")
        
        return node

    def assignment(self):
        node = SyntaxNode("Assignment")
        
        # Variable
        if self.current_token and self.current_token.type == 'ID':
            node.add_child(SyntaxNode("Identifier", self.current_token.value))
            self.eat('ID')
        else:
            self.error("Expected identifier")
        
        # =
        self.eat('ASSIGN')
        
        # Expression
        if self.current_token and self.current_token.type == 'ID':
            node.add_child(SyntaxNode("Identifier", self.current_token.value))
            self.eat('ID')
        else:
            self.error("Expected identifier or expression")
        
        # ;
        self.eat('SEMICOLON')
        
        return node

    def for_loop(self):
        node = SyntaxNode("ForLoop")
        
        # for
        self.eat('FOR')
        
        # (initialization; condition; increment)
        self.eat('LPAREN')
        
        # Initialization
        init_node = SyntaxNode("Initialization")
        if self.current_token and self.current_token.type == 'ID':
            init_node.add_child(SyntaxNode("Identifier", self.current_token.value))
            self.eat('ID')
            
            self.eat('ASSIGN')
            
            if self.current_token and self.current_token.type == 'INT_CONST':
                init_node.add_child(SyntaxNode("IntConstant", self.current_token.value))
                self.eat('INT_CONST')
            else:
                self.error("Expected integer constant")
        else:
            self.error("Expected identifier")
        
        node.add_child(init_node)
        self.eat('SEMICOLON')
        
        # Condition
        node.add_child(self.condition())
        self.eat('SEMICOLON')
        
        # Increment
        inc_node = SyntaxNode("Increment")
        if self.current_token and self.current_token.type == 'INC':
            inc_node.add_child(SyntaxNode("IncrementOperator", self.current_token.value))
            self.eat('INC')
            
            if self.current_token and self.current_token.type == 'ID':
                inc_node.add_child(SyntaxNode("Identifier", self.current_token.value))
                self.eat('ID')
            else:
                self.error("Expected identifier after increment operator")
        elif self.current_token and self.current_token.type == 'ID':
            inc_node.add_child(SyntaxNode("Identifier", self.current_token.value))
            self.eat('ID')
            
            if self.current_token and self.current_token.type == 'INC':
                inc_node.add_child(SyntaxNode("IncrementOperator", self.current_token.value))
                self.eat('INC')
            else:
                self.error("Expected increment operator")
        else:
            self.error("Expected identifier or increment operator")
        
        node.add_child(inc_node)
        self.eat('RPAREN')
        
        # Loop body
        if self.current_token and self.current_token.type == 'BEGIN':
            self.eat('BEGIN')
            node.add_child(self.for_body())
            if self.current_token and self.current_token.type == 'END':
                self.eat('END')
            else:
                self.error("Expected 'end'")
        else:
            self.error("Expected 'begin'")
        
        return node

    def for_body(self):
        node = SyntaxNode("ForBody")
        
        # Assignment
        if self.current_token and self.current_token.type == 'ID':
            node.add_child(self.assignment())
        else:
            self.error("Expected identifier")
        
        return node

class CFG:
    def __init__(self):
        self.productions = {
            'Program': ['MainFunction'],
            'MainFunction': ['INT_TYPE ID LPAREN RPAREN BEGIN Block END'],
            'Block': ['VariableDeclaration IfStatement ForLoop', 'VariableDeclaration'],
            'VariableDeclaration': ['INT_TYPE VariableList SEMICOLON'],
            'VariableList': ['ID', 'ID COMMA VariableList'],
            'IfStatement': ['IF LPAREN Condition RPAREN Assignment'],
            'Condition': ['EXPR RELOP EXPR'],
            'Assignment': ['ID ASSIGN ID SEMICOLON', 'ID ASSIGN INT_CONST SEMICOLON'],
            'ForLoop': ['FOR LPAREN Initialization SEMICOLON Condition SEMICOLON Increment RPAREN BEGIN ForBody END'],
            'Initialization': ['ID ASSIGN INT_CONST'],
            'Increment': ['INC ID', 'ID INC'],
            'ForBody': ['Assignment'],
        }
        self.terminals = {'INT_TYPE', 'ID', 'LPAREN', 'RPAREN', 'BEGIN', 'END', 'SEMICOLON', 
                         'COMMA', 'IF', 'EXPR', 'RELOP', 'ASSIGN', 'INT_CONST', 'FOR', 'INC'}
        self.non_terminals = set(self.productions.keys())
        self.first = {}
        self.follow = {}
        self.compute_first()
        self.compute_follow()

    def compute_first(self):
        # Initialize FIRST sets for all non-terminals
        for nt in self.non_terminals:
            self.first[nt] = set()
        
        # Initialize FIRST sets for terminals
        for terminal in self.terminals:
            self.first[terminal] = {terminal}
        
        # Compute FIRST sets for non-terminals
        changed = True
        while changed:
            changed = False
            
            for nt, productions in self.productions.items():
                for production in productions:
                    symbols = production.split()
                    i = 0
                    should_add_epsilon = True
                    
                    while i < len(symbols) and should_add_epsilon:
                        symbol = symbols[i]
                        
                        if symbol in self.terminals:
                            if symbol not in self.first[nt]:
                                self.first[nt].add(symbol)
                                changed = True
                            should_add_epsilon = False
                        else:  # Non-terminal
                            for terminal in self.first[symbol] - {'epsilon'}:
                                if terminal not in self.first[nt]:
                                    self.first[nt].add(terminal)
                                    changed = True
                            
                            if 'epsilon' not in self.first[symbol]:
                                should_add_epsilon = False
                        
                        i += 1
                    
                    if should_add_epsilon and 'epsilon' not in self.first[nt]:
                        self.first[nt].add('epsilon')
                        changed = True

    def compute_follow(self):
        # Initialize FOLLOW sets for all non-terminals
        for nt in self.non_terminals:
            self.follow[nt] = set()
        
        # Add $ to FOLLOW set of the start symbol
        self.follow['Program'] = {'$'}
        
        # Compute FOLLOW sets
        changed = True
        while changed:
            changed = False
            
            for nt, productions in self.productions.items():
                for production in productions:
                    symbols = production.split()
                    
                    for i, symbol in enumerate(symbols):
                        if symbol in self.non_terminals:
                            # Case 1: A -> αBβ, then add FIRST(β) - {ε} to FOLLOW(B)
                            if i < len(symbols) - 1:
                                next_symbols = symbols[i+1:]
                                first_of_beta = self.get_first_of_sequence(next_symbols)
                                
                                for terminal in first_of_beta - {'epsilon'}:
                                    if terminal not in self.follow[symbol]:
                                        self.follow[symbol].add(terminal)
                                        changed = True
                                
                                # Case 2: A -> αBβ and ε is in FIRST(β), then add FOLLOW(A) to FOLLOW(B)
                                if 'epsilon' in first_of_beta:
                                    for terminal in self.follow[nt]:
                                        if terminal not in self.follow[symbol]:
                                            self.follow[symbol].add(terminal)
                                            changed = True
                            
                            # Case 3: A -> αB, then add FOLLOW(A) to FOLLOW(B)
                            elif i == len(symbols) - 1:
                                for terminal in self.follow[nt]:
                                    if terminal not in self.follow[symbol]:
                                        self.follow[symbol].add(terminal)
                                        changed = True

    def get_first_of_sequence(self, symbols):
        if not symbols:
            return {'epsilon'}
        
        result = set()
        i = 0
        all_have_epsilon = True
        
        while i < len(symbols) and all_have_epsilon:
            symbol = symbols[i]
            
            if symbol in self.terminals:
                result.add(symbol)
                all_have_epsilon = False
            else:  # Non-terminal
                result.update(self.first[symbol] - {'epsilon'})
                
                if 'epsilon' not in self.first[symbol]:
                    all_have_epsilon = False
            
            i += 1
        
        if all_have_epsilon:
            result.add('epsilon')
        
        return result

def print_syntax_tree(node, level=0):
    indent = "  " * level
    node_str = f"{indent}{node}"
    
    if not node.children:
        return node_str + "\n"
    
    result = node_str + "\n"
    for child in node.children:
        result += print_syntax_tree(child, level + 1)
    
    return result

def print_parse_tree(node, level=0):
    indent = "  " * level
    result = f"{indent}<{node.type}>\n"
    
    if node.value is not None:
        result += f"{indent}  {node.value}\n"
    
    for child in node.children:
        result += print_parse_tree(child, level + 1)
    
    result += f"{indent}</{node.type}>\n"
    return result

def generate_symbol_table(symbol_table):
    result = "Symbol Table:\n"
    result += "-" * 40 + "\n"
    result += f"{'Name':<15}{'Type':<10}{'Scope':<10}\n"
    result += "-" * 40 + "\n"
    
    for name, info in symbol_table.items():
        result += f"{name:<15}{info['type']:<10}{info['scope']:<10}\n"
    
    return result

def main():
    # Input code
    code = """int main() begin int n1, n2, i, gcd; if(expr relop expr) gcd = i; for(i=1; expr relop expr; ++i) begin gcd=1; end end"""
    
    # Tokenize
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    
    # Parse
    parser = Parser(tokens)
    syntax_tree = parser.parse()
    
    # Define CFG and compute FIRST and FOLLOW sets
    cfg = CFG()
    
    # Generate syntax tree
    with open("syntax_tree.txt", "w") as f:
        f.write(print_syntax_tree(syntax_tree))
    
    # Generate parse tree
    with open("parse_tree.txt", "w") as f:
        f.write(print_parse_tree(syntax_tree))
    
    # Generate symbol table
    with open("symbol_table.txt", "w") as f:
        f.write(generate_symbol_table(parser.symbol_table))
    
    # Generate first sets
    with open("first.txt", "w") as f:
        f.write("FIRST Sets:\n")
        for nt, first_set in cfg.first.items():
            if nt in cfg.non_terminals:
                f.write(f"FIRST({nt}) = {{{', '.join(sorted(first_set))}}}\n")
    
    # Generate follow sets
    with open("follow.txt", "w") as f:
        f.write("FOLLOW Sets:\n")
        for nt, follow_set in cfg.follow.items():
            f.write(f"FOLLOW({nt}) = {{{', '.join(sorted(follow_set))}}}\n")
    
    # Generate token stream
    with open("token_stream.txt", "w") as f:
        for token in tokens:
            f.write(f"{token}\n")
    
    # Generate token summary
    token_count = Counter([token.type for token in tokens])
    with open("token_summary.txt", "w") as f:
        f.write("Token Summary:\n")
        f.write("-" * 40 + "\n")
        f.write(f"{'Token Type':<20}{'Count':<10}\n")
        f.write("-" * 40 + "\n")
        for token_type, count in token_count.items():
            f.write(f"{token_type:<20}{count:<10}\n")
    
    # Generate tokens used
    with open("tokens.txt", "w") as f:
        f.write("Tokens Used:\n")
        f.write("-" * 40 + "\n")
        for token_type in sorted(set(token.type for token in tokens)):
            f.write(f"{token_type}\n")
    
    # Generate errors
    with open("error.txt", "w") as f:
        if lexer.errors or parser.errors:
            f.write("Errors:\n")
            for error in lexer.errors:
                f.write(f"{error}\n")
            for error in parser.errors:
                f.write(f"{error}\n")
        else:
            f.write("No errors detected.\n")

if __name__ == "__main__":
    main()