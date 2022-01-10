import sys, traceback

class Symbol(str):
    def __new__(cls,name):
        if '"' in name:
            raise Exception("@Symbol.__new__ name << "+str(name)+" >> contains \"")
        return str.__new__(cls,name)  
               
class List(list):
    def __init__(self,l=[]):
        list.__init__(self,l)
    def __str__(self):
        return '('+' '.join([str(x) for x in list(self)])+')'       
    #def __getitem__(self,i):
    #    if i<0 or i>=len(self):
    #        return None
    #    return list(self)[i]
  
class Vector(list):
    def __init__(self):
        pass
    def __str__(self):
        return '['+' '.join([str(x) for x in list(self)])+']'
    #def __getitem__(self,i):
    #    if i<0 or i>=len(self):
    #        return None
    #    return list(self)[i]
        
class Dict(dict):
    def __init__(self,d={}):
        dict.__init__(self,d)
    def __str__(self):
        return 
    def __getitem__(self,k):
        if type(k) is Symbol:
            return dict(self).get(k,None)
        return None
    def __setitem__(self,k,v):
        if type(k) is Symbol:
            dict(self).__setitem__(k,v)
        raise Exception("@Dict.__setitem__ key << "+str(k)+" >> is not Symbol")
    def __str__(self):
        l=[]
        for k,v in dict(self).items():
            l.append(k)
            l.append(v)                    
        return '{'+' '.join([str(x) for x in l])+'}'
        
def space(s):
    return s == ' ' or s == '\n' or s == '\r' or s == '\t' or s == '\f' or s == '\v' or s == ','
    
class StringPtr:
    def __init__(self,s):
        if isinstance(s,StringPtr):
            self.s = s.s
            self.i = s.i
        else:
            self.s = str(s)
            self.i = 0
    def nend(self):
        return self.i < len(self.s)
    def end(self):
        return not self.nend()
    def inc(self):
        self.i += 1
    def __getitem__(self,offset):
        try:
            return self.s[self.i+offset]
        except:
            return ""
    def skip_spaces(self):
        while self.nend() and space(self[0]):
            self.inc()
    def remainder(self):
        return self.s[self.i:]     
        
def to_str(c):
    if c is None:
        return "nil"
    elif c is True:
        return 'true'
    elif c is False:
        return 'false'
    else:
        return str(c)

def recursive_parse(s):
    s.skip_spaces()
    if s.end():
        return None
    if s[0]=='(':
        s.inc()
        s.skip_spaces()
        c=List()
        while s[0]!=')' and s.nend():
            c.append(recursive_parse(s))
            s.skip_spaces()            
        if s.end():
            raise Exception("Exception: expected ')', got EOF")
        s.inc()
        return c
    elif s[0]=='[':
        s.inc()
        s.skip_spaces()
        c=Vector()
        while s[0]!=']' and s.nend():
            c.append(recursive_parse(s))
            s.skip_spaces()            
        if s.end():
            raise Exception("Exception: expected ']', got EOF")
        s.inc()
        return c
    elif s[0]=='{':
        s.inc()        
        s.skip_spaces()
        t=Dict()
        key = True
        while s[0]!='}' and s.nend():
            i = recursive_parse(s)
            s.skip_spaces()
            if key:
                k = i
            else:
                c[k] = i
            key = not key            
        if s.end():
            raise Exception("Exception: expected '}', got EOF")
        s.inc()
        return c
    else:
        j = s.i
        if s[0]=='\"':
            while s.nend():
                s.inc()
                if s[0]=='\\':
                    s.inc()
                    if not space(s[0]):
                        s.inc()
                if s[0]=='\"':
                    break
            if s[0]!='\"':
                raise Exception("Exception: expected '\"', got EOF")
            s.inc()
            return s.s[j:s.i] #s.s[j+1:s.i-1]
        elif s[0]=='\'':
            s.inc()
            return List(["quote",recursive_parse(s)])
        elif s[0]=='`':
            s.inc()
            return List(["quasiquote",recursive_parse(s)])
        elif s[0]=='~':
            s.inc()
            if s[0]=='@':
                s.inc()            
                return List(["splice-unquote",recursive_parse(s)])            
            return List(["unquote",recursive_parse(s)])
        elif s[0]=='@':
            s.inc()
            return List(["deref",recursive_parse(s)])                    
        elif s[0]=='^':
            s.inc()
            s.skip_spaces()
            m = recursive_parse(s)
            s.inc()
            s.skip_spaces()
            o = recursive_parse(s)
            s.inc()
            return List(["with-meta",o,m])
        else:
            while s.nend() and (not space(s[0])) and s[0]!='(' and s[0]!=')' and s[0]!='[' and s[0]!=']' and s[0]!='{' and s[0]!='}':
                s.inc()
            try:
                return int(s.s[j:s.i])                
            except:
                return Symbol(s.s[j:s.i])
    return None

def parse(s):
    s=StringPtr(s)
    k=List()
    while s.nend():
        k.append(recursive_parse(s))
    return k
   
def READ():
    return parse(input("user> "))[0]
  
def DO(c,e):
    r = None
    if type(c) is List:
        for i in c:
            r = EVAL(i,e)
    return r

def IF(c,e):
    if EVAL(c[0],e) is False:
        return EVAL(c[2],e) 
    else:
        return EVAL(c[1],e)

def LET(c,e):
  ee=Env(e)
  l=c[0]
  if type(l) is List or type(l) is Vector:
      while l:
          x = l[0]
          l = l[1:]
          ee[x] = EVAL(l[0],ee)
          l = l[1:]
  return EVAL(c[1],ee)

def EMPTYQ(c,e):
    x = EVAL(c[0],e)
    if type(x) is List:
        return len(x) == 0
    return False
       
def COUNT(c,e):
    x=EVAL(c[0],e)
    if type(x) == List:
        return len(x)
    return None

def PRN(c,e):
    print(str(EVAL(c[0],e)))
    return None
    
class Env(dict):
    def __init__(self,outer=None):
        self.outer=outer      
    def __getitem__(self,k):
        if k in dict(self):
            return dict(self).__getitem__(k)
        if self.outer is None:      
            raise Exception("@Env.__getitem__ key << "+str(k)+" >> not found") 
        else:   
            return self.outer[k]
    def __setitem__(self,k,v):
        if type(k) is Symbol:
            dict.__setitem__(self,k,v)
        else:
            raise Exception("@Env.__setitem__ key << "+str(k)+" >> not valid")
    def __str__(self):
        s='Env{'
        sep=''
        for k,v in dict.items(self):
            if callable(v):
                s+=sep+str(k)+':...'
            else:
                s+=sep+str(k)+':'+str(v)
            sep=','
        s+=';'+str(self.outer)+'}'
        return s
    def __repr__(self):
        return self.__str__()

class Closure:
    def __init__(self,args,body,env):
        self.args = args
        self.body = body
        self.env = env                 
    def __call__(self,c,e):
        ee = Env(self.env)        
        if type(c) is List:
            for x,y in zip(c,self.args):
                ee[x] = EVAL(y,e)
        return EVAL(self.body,ee)
                            
def eval_list(c,e):
    if type(c) is List:
        return List([EVAL(x,e) for x in c])
    return None
      
def EVAL(c,env):
    if type(c) == List:
        f = EVAL(c[0],env)
        if callable(f):
            return f(c[1:],env)
        else:
            return (f,eval_list(cdr(c),env))
    elif type(c) is Symbol:
        return env[c]
    elif type(c) == List:
        return Vector([EVAL(x,env) for x in c])
    elif type(c) == Dict:
        return Dict({k : EVAL(c[k],env) for k in c.keys()})
    else:
        return c
        
repl_env = Env()
repl_env[Symbol('true')] = True
repl_env[Symbol('false')] = False
repl_env[Symbol('nil')] = False
repl_env[Symbol('quote')] = lambda c,e: EVAL(c[0],e)+EVAL(c[1],e)
repl_env[Symbol('+')] = lambda c,e: EVAL(c[0],e)+EVAL(c[1],e)
repl_env[Symbol('-')] = lambda c,e: EVAL(c[0],e)-EVAL(c[1],e)
repl_env[Symbol('*')] = lambda c,e: EVAL(c[0],e)*EVAL(c[1],e)
repl_env[Symbol('/')] = lambda c,e: int(EVAL(c[0],e)/EVAL(c[1],e))
repl_env[Symbol('def!')] = lambda c,e: e.__setitem__(c[0],EVAL(c[1],e))
repl_env[Symbol('let*')] = LET
repl_env[Symbol('do')] = DO
repl_env[Symbol('if')] = IF
repl_env[Symbol('fn*')] = lambda c,e: Closure(c[0],c[1],e)
repl_env[Symbol('list')] = lambda c,e: eval_list(c[1],e)
repl_env[Symbol('list?')] = lambda c,e: type(EVAL(c[1],e)) is List
repl_env[Symbol('empty?')] = EMPTYQ
repl_env[Symbol('count')] = COUNT
repl_env[Symbol('<')] = lambda c,e: EVAL(c[0],e)<EVAL(c[1],e)
repl_env[Symbol('>')] = lambda c,e: EVAL(c[0],e)>EVAL(c[1],e)
repl_env[Symbol('<=')] = lambda c,e: EVAL(c[0],e)<=EVAL(c[1],e)
repl_env[Symbol('>=')] = lambda c,e: EVAL(c[0],e)>=EVAL(c[1],e)
repl_env[Symbol('=')] = lambda c,e: EVAL(c[0],e)==EVAL(c[1],e)
repl_env[Symbol('prn')] = PRN
                       
while True:
    try:
        print(to_str(EVAL(READ(),repl_env)))
    except Exception as e:
        print("".join(traceback.format_exception(*sys.exc_info())))         
    except EOFError:
        break
