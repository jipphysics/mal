import sys, traceback
  
class Symbol(str):
    def __new__(cls,name):
        if '"' in name:
            raise Exception("@Symbol.__new__ name << "+str(name)+" >> contains \"")
        return str.__new__(cls,name)
              
class Key(str):
    def __new__(cls,name):
        if '"' in name or not name[0] == ':':
            raise Exception("@Key.__new__ name << "+str(name)+" >> is invalid \"")
        return str.__new__(cls,name)  

class Vector(list):
    def __init__(self,l=[]):
        list.__init__(self,l)
       
class Dict(dict):
    def __init__(self,d={}):
        dict.__init__(self,d)
    def __str__(self):
        return 
    def __getitem__(self,k):
        if type(k) is Key:
            return dict(self).get(k,None)
        return None
    def __setitem__(self,k,v):
        if type(k) is Key:
            dict(self).__setitem__(k,v)
        raise Exception("@Dict.__setitem__ key << "+str(k)+" >> is not Key")

class Closure:
    def __init__(self,args,body,env):
        self.args = args
        self.body = body
        self.env = env                 
    def __call__(self,c,e):
        ee = Env(self.env) 
        if isinstance(c,list):
            a = self.args
            while a:
                if a[0] == "&":
                    ee[a[1]] = eval_list(c[0:],e)
                    break
                else:
                    ee[a[0]] = EVAL(c[0],e)
                a = a[1:]
                c = c[1:]
        return EVAL(self.body,ee)

def tostr(c,r=False,q='"'): # r = readably, q = enclose
    if c is None:
        return "nil"
    elif c is True:
        return 'true'
    elif c is False:
        return 'false'
    elif type(c) is int:
        return str(c)
    elif type(c) is str:
        if r:
            return (q+c+q).replace('\\','\\\\').replace('"','\\"')
        return q+c+q
    elif type(c) is list:
        return '('+' '.join([tostr(x,r=r,q=q) for x in c])+')'
    elif type(c) is Vector:
        return '['+' '.join([tostr(x,r=r,q=q) for x in c])+']'
    elif type(c) is Dict:    
        l=[]
        for k,v in dict(self).items():
            l.append(k)
            l.append(v)                    
        return '{'+' '.join([tostr(x,r=r,q=q) for x in l])+'}'
    elif type(c) is Closure:
        return c
    elif type(c) is Env:
        sep=""
        s='Env{'
        for k,v in dict.items(self):
            if callable(v):
                s+=sep+tostr(k,r=r,q=q)+':...'
            else:
                s+=sep+tostr(k,r=r,q=q)+':'+tostr(v,r=r,q=q)
            sep=' '
        s+=';'+tostr(self.outer,r=r,q=q)+'}'
        return s
    else:
        return c
        
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
        
def recursive_parse(s):
    s.skip_spaces()
    if s.end():
        return None
    if s[0]=='(':
        s.inc()
        s.skip_spaces()
        c=[]
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
            return s.s[j+1:s.i-1]
        elif s[0]=='\'':
            s.inc()
            return ["quote",recursive_parse(s)]
        elif s[0]=='`':
            s.inc()
            return ["quasiquote",recursive_parse(s)]
        elif s[0]=='~':
            s.inc()
            if s[0]=='@':
                s.inc()            
                return ["splice-unquote",recursive_parse(s)]
            return ["unquote",recursive_parse(s)]
        elif s[0]=='@':
            s.inc()
            return ["deref",recursive_parse(s)]
        elif s[0]=='^':
            s.inc()
            s.skip_spaces()
            m = recursive_parse(s)
            s.inc()
            s.skip_spaces()
            o = recursive_parse(s)
            s.inc()
            return ["with-meta",o,m]
        else:
            while s.nend() and (not space(s[0])) and s[0]!='(' and s[0]!=')' and s[0]!='[' and s[0]!=']' and s[0]!='{' and s[0]!='}':
                s.inc()
            try:
                return int(s.s[j:s.i])                
            except:
                if s.s[j] == ':':
                    return Key(s.s[j:s.i])                
                else:
                    return Symbol(s.s[j:s.i])
    return None

def parse(s):
    s=StringPtr(s)
    k=[]
    while s.nend():
        k.append(recursive_parse(s))
    return k
   
def eval_list(c,e):
    if type(c) is list:
        return [EVAL(x,e) for x in c]
    elif type(c) is Vector:
        return Vector([EVAL(x,e) for x in c])
    elif type(c) is Dict:
        return Dict({k : EVAL(x,e) for x in c.items()})
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
                                              
def EVAL(c,env):
    if type(c) is list and len(c)>0:
        f = EVAL(c[0],env)
        if callable(f):
            return f(c[1:],env)
        else:
            return (f,eval_list(c[1:],env))
    elif type(c) is Symbol:
        return env[c]
    elif type(c) is Vector:
        return Vector([EVAL(x,env) for x in c])
    elif type(c) == Dict:
        return Dict({k : EVAL(c[k],env) for k in c.keys()})
    else:
        return c
        
repl_env = Env()
repl_env[Symbol('true')] = True
repl_env[Symbol('false')] = False
repl_env[Symbol('nil')] = None
repl_env[Symbol('quote')] = lambda c,e: EVAL(c[0],e)+EVAL(c[1],e)
repl_env[Symbol('+')] = lambda c,e: EVAL(c[0],e)+EVAL(c[1],e)
repl_env[Symbol('-')] = lambda c,e: EVAL(c[0],e)-EVAL(c[1],e)
repl_env[Symbol('*')] = lambda c,e: EVAL(c[0],e)*EVAL(c[1],e)
repl_env[Symbol('/')] = lambda c,e: int(EVAL(c[0],e)/EVAL(c[1],e))
repl_env[Symbol('def!')] = lambda c,e: e.__setitem__(c[0],EVAL(c[1],e))
repl_env[Symbol('fn*')] = lambda c,e: Closure(c[0],c[1],e)
repl_env[Symbol('list')] = lambda c,e: eval_list(c,e)
repl_env[Symbol('list?')] = lambda c,e: type(EVAL(c[0],e)) is list
repl_env[Symbol('<')] = lambda c,e: EVAL(c[0],e)<EVAL(c[1],e)
repl_env[Symbol('>')] = lambda c,e: EVAL(c[0],e)>EVAL(c[1],e)
repl_env[Symbol('<=')] = lambda c,e: EVAL(c[0],e)<=EVAL(c[1],e)
repl_env[Symbol('>=')] = lambda c,e: EVAL(c[0],e)>=EVAL(c[1],e)
repl_env[Symbol('=')] = lambda c,e: EVAL(c[0],e)==EVAL(c[1],e)

def LET(c,e):
  ee=Env(e)
  l=c[0]
  if isinstance(c,list):
      while l:
          x = l[0]
          l = l[1:]
          ee[x] = EVAL(l[0],ee)
          l = l[1:]
  return EVAL(c[1],ee)
repl_env[Symbol('let*')] = LET

def DO(c,e):
    r = None
    if isinstance(c,list):
        for i in c:
            r = EVAL(i,e)
    return r
repl_env[Symbol('do')] = DO

def IF(c,e):
    x=EVAL(c[0],e)
    if x is False or x is None:
        if len(c)>2:
            return EVAL(c[2],e)
        return None
    elif len(c)>1:
        return EVAL(c[1],e)
    else:
        return None #raise Exception("@IF invalid expression") 
repl_env[Symbol('if')] = IF

def EMPTYQ(c,e):
    x = EVAL(c[0],e)
    if isinstance(x,list):
        return len(x) == 0
    return False
repl_env[Symbol('empty?')] = EMPTYQ

def COUNT(c,e):
    x=EVAL(c[0],e)
    print("@COUNT c="+str(c)+" x="+str(x)+" e="+str(e))    
    if isinstance(x,list):
        return len(x)
    return 0
repl_env[Symbol('count')] = COUNT

def NOT(c,e):
    x=EVAL(c[0],e)
    if x is False or x is None:
        return True
    return False
repl_env[Symbol('not')] = NOT

def PR_STR(c,e):
    return ' '.join([tostr(EVAL(i,e),r=True,q='"') for i in c])
repl_env[Symbol('pr-str')] = PR_STR

def STR(c,e):
    #return '"'+''.join([tostr(EVAL(i,e),r=False,q='') for i in c])+'"'
    return ''.join([tostr(EVAL(i,e),r=False,q='') for i in c])
repl_env[Symbol('str')] = STR

def PRN(c,e):
    print(' '.join([tostr(EVAL(i,e),r=False,q='"') for i in c]))
    return None
repl_env[Symbol('prn')] = PRN

def PRINTLN(c,e):
    print(' '.join([tostr(EVAL(i,e),r=False,q='') for i in c]))
    return None    
repl_env[Symbol('println')] = PRINTLN
   
def READ():
    return parse(input("user> "))[0]   
                       
while True:
    try:
        print(tostr(EVAL(READ(),repl_env)))
    except Exception as e:
        print("".join(traceback.format_exception(*sys.exc_info())))         
    except EOFError:
        break
