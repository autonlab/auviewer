# Provides a gateway to share variables amongst submodules
v={}
def provide(name, val):
    global v
    v[name]=val
def receive(name):
    global v
    return v[name]