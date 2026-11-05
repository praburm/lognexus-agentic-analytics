from graphviz import Digraph

dot = Digraph(comment='Agentic AIOps Flow')

dot.node('MS', 'Microservices')
dot.node('M', 'Monitor Agent')
dot.node('C', 'Correlation Agent')
dot.node('R', 'RCA Agent')
dot.node('A', 'Alert / Action')

dot.edges([
    ('MS', 'M'),
    ('M', 'C'),
    ('C', 'R'),
    ('R', 'A')
])

dot
