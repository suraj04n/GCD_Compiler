import re
from collections import defaultdict, Counter

class Token:
    def __init__(self, type_, value, line, position):
        self.type = type_
        self.value = value
        self.line = line
        self.position = position
    
    def __str__(self):
        return f"Token({self.type}, '{self.value}', line={self.line}, pos={self.position})"

class Lexer:
    def __init__(self, text):
        self.text = text
        self.position = 0
        self.current_char = self.text[0] if self.text else None
        self.line = 1
        self.line_pos = 1
        self.tokens = []
    
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

    def peek(self):
        peek_pos = self.position + 1
        if peek_pos >= len(self.text):
            return None
        return self.text[peek_pos]

    def id_(self):
        result = ''
        line, position = self.line, self.line_pos
        
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        keywords = {
            'int': 'INT_TYPE',
            'if': 'IF',
            'for': 'FOR',
            'begin': 'BEGIN',
            'end': 'END',
        }
        return Token(keywords.get(result, 'ID'), result, line, position)

    def number(self):
        result = ''
        line, position = self.line, self.line_pos
        
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        
        return Token('INT_CONST', int(result), line, position)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            if self.current_char.isalpha() or self.current_char == '_':
                return self.id_()
            
            if self.current_char.isdigit():
                return self.number()
            
            # Single character tokens
            if self.current_char in {';', ',', '(', ')', '*', '/', '%'}:
                token_types = {';': 'SEMICOLON', ',': 'COMMA', '(': 'LPAREN', 
                               ')': 'RPAREN', '*': 'MUL', '/': 'DIV', '%': 'MOD'}
                token = Token(token_types[self.current_char], self.current_char, self.line, self.line_pos)
                self.advance()
                return token
            
            # Two character tokens and assignments
            if self.current_char == '=':
                line, position = self.line, self.line_pos
                self.advance()
                if self.current_char == '=':
                    token = Token('EQ', '==', line, position)
                    self.advance()
                else:
                    token = Token('ASSIGN', '=', line, position)
                return token
            
            if self.current_char == '+':
                line, position = self.line, self.line_pos
                self.advance()
                if self.current_char == '+':
                    token = Token('INC', '++', line, position)
                    self.advance()
                else:
                    token = Token('PLUS', '+', line, position)
                return token
            
            # Special tokens for our example
            if self.current_char == 'r' and self.position + 4 < len(self.text) and self.text[self.position:self.position+5] == 'relop':
                token = Token('RELOP', 'relop', self.line, self.line_pos)
                for _ in range(5): self.advance()
                return token
            
            if self.current_char == 'e' and self.position + 3 < len(self.text) and self.text[self.position:self.position+4] == 'expr':
                token = Token('EXPR', 'expr', self.line, self.line_pos)
                for _ in range(4): self.advance()
                return token
            
            # Skip unrecognized characters
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
        self.symbol_table = {}
    
    def eat(self, token_type):
        if self.current_token.type == token_type:
            old_token = self.current_token
            self.current_token_idx += 1
            if self.current_token_idx < len(self.tokens):
                self.current_token = self.tokens[self.current_token_idx]
            else:
                self.current_token = None
            return old_token
        return None

    def parse(self):
        return self.program()

    def program(self):
        node = SyntaxNode("Program")
        node.add_child(self.main_function())
        return node

    def main_function(self):
        node = SyntaxNode("MainFunction")
        
        self.eat('INT_TYPE')
        
        if self.current_token.type == 'ID' and self.current_token.value == 'main':
            node.add_child(SyntaxNode("Identifier", self.current_token.value))
            self.eat('ID')
        
        self.eat('LPAREN')
        self.eat('RPAREN')
        
        self.eat('BEGIN')
        
        node.add_child(self.block())
        
        self.eat('END')
        
        return node

    def block(self):
        node = SyntaxNode("Block")
        
        if self.current_token and self.current_token.type == 'INT_TYPE':
            node.add_child(self.variable_declaration())
        
        if self.current_token and self.current_token.type == 'IF':
            node.add_child(self.if_statement())
        
        if self.current_token and self.current_token.type == 'FOR':
            node.add_child(self.for_loop())
        
        return node

    def variable_declaration(self):
        node = SyntaxNode("VariableDeclaration")
        
        node.add_child(SyntaxNode("Type", self.current_token.value))
        self.eat('INT_TYPE')
        
        variables_node = self.variable_list()
        node.add_child(variables_node)
        
        for child in variables_node.children:
            if child.type == "Identifier":
                self.symbol_table[child.value] = {"type": "int", "scope": "local"}
        
        self.eat('SEMICOLON')
        
        return node

    def variable_list(self):
        node = SyntaxNode("VariableList")
        
        if self.current_token and self.current_token.type == 'ID':
            node.add_child(SyntaxNode("Identifier", self.current_token.value))
            self.eat('ID')
        
        while self.current_token and self.current_token.type == 'COMMA':
            self.eat('COMMA')
            if self.current_token and self.current_token.type == 'ID':
                node.add_child(SyntaxNode("Identifier", self.current_token.value))
                self.eat('ID')
        
        return node

    def if_statement(self):
        node = SyntaxNode("IfStatement")
        
        self.eat('IF')
        
        self.eat('LPAREN')
        node.add_child(self.condition())
        self.eat('RPAREN')
        
        node.add_child(self.assignment())
        
        return node

    def condition(self):
        node = SyntaxNode("Condition")
        
        node.add_child(SyntaxNode("Expression", self.current_token.value))
        self.eat('EXPR')
        
        node.add_child(SyntaxNode("RelationalOperator", self.current_token.value))
        self.eat('RELOP')
        
        node.add_child(SyntaxNode("Expression", self.current_token.value))
        self.eat('EXPR')
        
        return node

    def assignment(self):
        node = SyntaxNode("Assignment")
        
        node.add_child(SyntaxNode("Identifier", self.current_token.value))
        self.eat('ID')
        
        self.eat('ASSIGN')
        
        node.add_child(SyntaxNode("Identifier", self.current_token.value))
        self.eat('ID')
        
        self.eat('SEMICOLON')
        
        return node

    def for_loop(self):
        node = SyntaxNode("ForLoop")
        
        self.eat('FOR')
        self.eat('LPAREN')
        
        # Initialization
        init_node = SyntaxNode("Initialization")
        init_node.add_child(SyntaxNode("Identifier", self.current_token.value))
        self.eat('ID')
        
        self.eat('ASSIGN')
        
        init_node.add_child(SyntaxNode("IntConstant", self.current_token.value))
        self.eat('INT_CONST')
        
        node.add_child(init_node)
        self.eat('SEMICOLON')
        
        # Condition
        node.add_child(self.condition())
        self.eat('SEMICOLON')
        
        # Increment
        inc_node = SyntaxNode("Increment")
        inc_node.add_child(SyntaxNode("IncrementOperator", self.current_token.value))
        self.eat('INC')
        
        inc_node.add_child(SyntaxNode("Identifier", self.current_token.value))
        self.eat('ID')
        
        node.add_child(inc_node)
        self.eat('RPAREN')
        
        # Loop body
        self.eat('BEGIN')
        node.add_child(self.for_body())
        self.eat('END')
        
        return node

    def for_body(self):
        node = SyntaxNode("ForBody")
        node.add_child(self.assignment())
        return node

class CFG:
    def __init__(self):
        self.productions = {
            'Program': ['MainFunction'],
            'MainFunction': ['INT_TYPE ID LPAREN RPAREN BEGIN Block END'],
            'Block': ['VariableDeclaration IfStatement ForLoop'],
            'VariableDeclaration': ['INT_TYPE VariableList SEMICOLON'],
            'VariableList': ['ID', 'ID COMMA VariableList'],
            'IfStatement': ['IF LPAREN Condition RPAREN Assignment'],
            'Condition': ['EXPR RELOP EXPR'],
            'Assignment': ['ID ASSIGN ID SEMICOLON'],
            'ForLoop': ['FOR LPAREN Initialization SEMICOLON Condition SEMICOLON Increment RPAREN BEGIN ForBody END'],
            'Initialization': ['ID ASSIGN INT_CONST'],
            'Increment': ['INC ID'],
            'ForBody': ['Assignment'],
        }
        self.terminals = {'INT_TYPE', 'ID', 'LPAREN', 'RPAREN', 'BEGIN', 'END', 'SEMICOLON', 
                         'COMMA', 'IF', 'EXPR', 'RELOP', 'ASSIGN', 'INT_CONST', 'FOR', 'INC', '$'}
        self.non_terminals = set(self.productions.keys())
        self.first = {}
        self.follow = {}
        self.parse_table = {}
        self.compute_first()
        self.compute_follow()
        self.construct_parse_table()

    def compute_first(self):
        # Initialize FIRST sets
        for nt in self.non_terminals:
            self.first[nt] = set()
        for t in self.terminals:
            self.first[t] = {t}
        
        # Compute FIRST sets
        changed = True
        while changed:
            changed = False
            for nt, productions in self.productions.items():
                for production in productions:
                    symbols = production.split()
                    i, should_add_epsilon = 0, True
                    
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
        # Initialize FOLLOW sets
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
                            # Case 1: A -> αBβ, add FIRST(β) - {ε} to FOLLOW(B)
                            if i < len(symbols) - 1:
                                next_symbols = symbols[i+1:]
                                first_of_beta = self.get_first_of_sequence(next_symbols)
                                
                                for terminal in first_of_beta - {'epsilon'}:
                                    if terminal not in self.follow[symbol]:
                                        self.follow[symbol].add(terminal)
                                        changed = True
                                
                                # Case 2: If ε is in FIRST(β), add FOLLOW(A) to FOLLOW(B)
                                if 'epsilon' in first_of_beta:
                                    for terminal in self.follow[nt]:
                                        if terminal not in self.follow[symbol]:
                                            self.follow[symbol].add(terminal)
                                            changed = True
                            
                            # Case 3: A -> αB, add FOLLOW(A) to FOLLOW(B)
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

    def construct_parse_table(self):
        # Initialize the parse table with empty cells
        for nt in self.non_terminals:
            self.parse_table[nt] = {}
            for t in self.terminals:
                self.parse_table[nt][t] = []
        
        # Fill the parse table
        for nt, productions in self.productions.items():
            for prod_idx, production in enumerate(productions):
                # Get a name for this production
                prod_name = f"{nt} -> {production}"
                
                # For each terminal in FIRST(production)
                first_of_prod = self.get_first_of_sequence(production.split())
                for terminal in first_of_prod - {'epsilon'}:
                    self.parse_table[nt][terminal].append(prod_name)
                
                # If epsilon is in FIRST(production), add production to FOLLOW(nt) entries
                if 'epsilon' in first_of_prod:
                    for terminal in self.follow[nt]:
                        self.parse_table[nt][terminal].append(prod_name)

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

def print_parse_table(cfg):
    # Determine column widths
    terminal_width = max(len(t) for t in cfg.terminals) + 2
    production_width = max(len(f"{nt} -> {prod}") for nt, prods in cfg.productions.items() for prod in prods) + 2
    
    # Create header
    result = "LL(1) Parse Table:\n\n"
    result += " " * terminal_width + "| "
    for terminal in sorted(cfg.terminals):
        result += f"{terminal:{terminal_width}}| "
    result += "\n"
    result += "-" * (terminal_width + 1 + (terminal_width + 2) * len(cfg.terminals)) + "\n"
    
    # Create rows
    for nt in sorted(cfg.non_terminals):
        result += f"{nt:{terminal_width}}| "
        for terminal in sorted(cfg.terminals):
            cell = cfg.parse_table[nt].get(terminal, [])
            cell_content = ", ".join(cell) if cell else ""
            result += f"{cell_content:{terminal_width}}| "
        result += "\n"
    
    return result

def main():
    # Input code
    code = """int main() begin int n1, n2, i, gcd; if(expr relop expr) gcd = i; for(i=1; expr relop expr; ++i) begin gcd=1; end end"""
    
    # Process the code
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    syntax_tree = parser.parse()
    cfg = CFG()
    
    # Generate all required files
    with open("syntax_tree.txt", "w") as f:
        f.write(print_syntax_tree(syntax_tree))
    
    with open("parse_tree.txt", "w") as f:
        f.write(print_parse_tree(syntax_tree))
    
    with open("symbol_table.txt", "w") as f:
        f.write("Symbol Table:\n" + "-" * 40 + "\n")
        f.write(f"{'Name':<15}{'Type':<10}{'Scope':<10}\n" + "-" * 40 + "\n")
        for name, info in parser.symbol_table.items():
            f.write(f"{name:<15}{info['type']:<10}{info['scope']:<10}\n")
    
    with open("first.txt", "w") as f:
        f.write("FIRST Sets:\n")
        for nt in cfg.non_terminals:
            f.write(f"FIRST({nt}) = {{{', '.join(sorted(cfg.first[nt]))}}}\n")
    
    with open("follow.txt", "w") as f:
        f.write("FOLLOW Sets:\n")
        for nt in cfg.non_terminals:
            f.write(f"FOLLOW({nt}) = {{{', '.join(sorted(cfg.follow[nt]))}}}\n")
    
    with open("token_stream.txt", "w") as f:
        for token in tokens:
            f.write(f"{token}\n")
    
    with open("token_summary.txt", "w") as f:
        token_count = Counter([token.type for token in tokens])
        f.write("Token Summary:\n" + "-" * 40 + "\n")
        f.write(f"{'Token Type':<20}{'Count':<10}\n" + "-" * 40 + "\n")
        for token_type, count in token_count.items():
            f.write(f"{token_type:<20}{count:<10}\n")
    
    with open("tokens.txt", "w") as f:
        f.write("Tokens Used:\n" + "-" * 40 + "\n")
        for token_type in sorted(set(token.type for token in tokens)):
            f.write(f"{token_type}\n")
    
    # Generate parse table
    with open("parse_table.txt", "w") as f:
        f.write(print_parse_table(cfg))

if __name__ == "__main__":
    main()
