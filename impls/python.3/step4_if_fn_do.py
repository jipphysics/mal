import sys, traceback

def car(c):
    if type(c) == tuple:# or type(c) == list:
        return c[0]
    return None
def cdr(c):
    if type(c) == tuple:# or type(c) == list:
        return c[1]
    return None
def caar(c):
    return car(car(c))
def cadr(c):
    return car(cdr(c))
def cdar(c):
    return cdr(car(c))
def cddr(c):
    return cdr(cdr(c))
def caaar(c):
    return car(caar(c))
def caadr(c):
    return car(cadr(c))
def cadar(c):
    return car(cdar(c))
def caddr(c):
    return car(cddr(c))
def cdaar(c):
    return cdr(caar(c))
def cdadr(c):
    return cdr(cadr(c))
def cddar(c):
    return cdr(cdar(c))
def cdddr(c):
    return cdr(cddr(c))

def space(s):
    return s == ' ' or s == '\n' or s == '\r' or s == '\t' or s == '\f' or s == '\v' or s == ','
    
class String:
    def __init__(self,s):
        if isinstance(s,String):
            self.s = s.s
            self.i = s.i
            self.e = s.e                        
        else:
            self.s = str(s)
            self.i = 0
            self.e = len(self.s)
    def nend(self):
        return self.i < self.e
    def end(self):
        return not self.nend()
    def inc(self):
        self.i += 1
    def __getitem__(self,offset):
        try:
            return self.s[self.i+offset]
        except:
            return ""
    def eat_spaces(self):
        while self.nend() and space(self[0]):
            self.inc()
    def remainder(self):
        return self.s[self.i:]

def to_str(c):
    if c is None:
        return "()"
    elif type(c) == tuple:
        s="("
        i=c
        while i:
            s+=to_str(car(i))
            i=cdr(i)
            if type(i) != tuple and i:
                s+=" . "+to_str(i)
                break
            if i:
                s+=" "
        return s+")"
    elif type(c) == list:
        sep=""
        s="["
        for i in c:
            s+=sep
            sep=" "
            s+=to_str(i)            
        return s+"]"
    elif type(c) == dict:
        sep=""
        s="{"
        for k,v in c.items():
            s+=sep+to_str(k)+" "+to_str(v)
        return s+"}"
    elif c is True:
        return 'true'
    elif c is False:
        return 'false'
    else:
        return str(c)

def recursive_parse(s):
    s.eat_spaces()
    if s.end():
        return None
    if s[0]=='(':
        s.inc()
        s.eat_spaces()
        k=None
        c=None
        while s[0]!=')' and s.nend():
            if s[0]=='.' and (space(s[1]) or s[1]==')'):
                s.inc()
                s.eat_spaces()
                if s[0]!=')' and s.nend():
                    c = recursive_parse(s)
                s.eat_spaces()
            else:
                k=(recursive_parse(s),k)
                s.eat_spaces()
        if s.end():
            raise Exception("Exception: expected ')', got EOF")
        while k:
            c=(car(k),c)
            k=cdr(k)
        s.inc()
        return c
    elif s[0]=='[':
        s.inc()
        s.eat_spaces()
        c=[]
        while s[0]!=']' and s.nend():
            c.append(recursive_parse(s))
            s.eat_spaces()            
        if s.end():
            raise Exception("Exception: expected ']', got EOF")
        s.inc()
        return c
    elif s[0]=='{':
        s.inc()        
        s.eat_spaces()
        t=[]
        while s[0]!='}' and s.nend():
            t.append(recursive_parse(s))
            s.eat_spaces()
        if s.end():
            raise Exception("Exception: expected '}', got EOF")
        s.inc()
        c = {}
        key = True
        for i in t:
            if key:
                k = i
            else:
                c[k] = i
            key = not key
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
            return ("quote",(recursive_parse(s),None))
        elif s[0]=='`':
            s.inc()
            return ("quasiquote",(recursive_parse(s),None))            
        elif s[0]=='~':
            s.inc()
            if s[0]=='@':
                s.inc()            
                return ("splice-unquote",(recursive_parse(s),None))            
            return ("unquote",(recursive_parse(s),None))
        elif s[0]=='@':
            s.inc()
            return ("deref",(recursive_parse(s),None))                    
        elif s[0]=='^':
            s.inc()
            s.eat_spaces()
            m = recursive_parse(s)
            s.inc()
            s.eat_spaces()
            o = recursive_parse(s)
            s.inc()
            return ("with-meta",(o,(m,None)))
        else:
            while s.nend() and (not space(s[0])) and s[0]!='(' and s[0]!=')' and s[0]!='[' and s[0]!=']' and s[0]!='{' and s[0]!='}':
                s.inc()
            try:
                #return float(s.s[j:s.i])
                return int(s.s[j:s.i])                
            except:
                return s.s[j:s.i]
    return None

def parse(s):
    s=String(s)
    k=None
    while s.nend():
        k=(recursive_parse(s),k)
    r=None
    while k:
        r=(car(k),r)
        k=cdr(k)
    return r
   
def READ():
    return car(parse(input("user> ")))
  
def DO(c,e):
    r = None
    if type(c) == tuple:
        while c:
            r = EVAL(car(c),e)
            c = cdr(c)
    return r

def IF(c,e):
    a = EVAL(car(c),e)
    if a is None or a is False:
        return EVAL(caddr(c),e) 
    else:
        return EVAL(cadr(c),e)

def LET(c,e):
  ee=Env(e)
  l=car(c)
  if type(l) == tuple:
      while l:
          x = car(l)
          l = cdr(l)
          ee[x] = EVAL(car(l),ee)
          l = cdr(l)
  elif type(l) == list:
      while l:
          x = l[0]
          l = l[1:]
          ee[x] = EVAL(l[0],ee)
          l = l[1:]
  return EVAL(cadr(c),ee)

def LIST(c,e):
    if type(c) == tuple:
        return (EVAL(car(c),e),LIST(cdr(c),e))
    return None
     
def LISTQ(c,e):
    a = EVAL(car(c),e)
    if a is None or type(a) == tuple:
        return True
    return False

def EMPTYQ(c,e):
    a = EVAL(car(c),e)
    if a is None:
        return True        
    return False
       
def COUNT(c,e):
    n=0
    a=EVAL(car(c),e)
    if type(a) == tuple:
        while a:
            n+=1
            a=cdr(a)
    return n

class Env(dict):
    def __init__(self,outer=None):
        self.outer=outer      
    def __getitem__(self,k):
        if k in dict(self):
            return dict(self).__getitem__(k)
        if self.outer:
            return self.outer[k]
        raise Exception("@Env.__getitem__ key << "+str(k)+" >> not found") 
    def __setitem__(self,k,v):
        if type(k) is str:
            dict.__setitem__(self,k,v)
            return v
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
        print("@Closure.__call__ e=",e)    
        #ee = Env(e)
        ee = Env(self.env)        
        if type(c) == tuple:
            a = self.args
            while c and a:
                ee[car(a)] = EVAL(car(c),e)
                c = cdr(c)
                a = cdr(a)
        print("@Closure.__call__ ee=",ee)
        return EVAL(self.body,ee)
                            
def eval_list(c,env):
    if type(c) == tuple:
        return (EVAL(car(c),env),eval_list(cdr(c),env))
    return EVAL(cdr(c),env)
      
def EVAL(c,env):
    print("@EVAL c="+to_str(c))
    if type(c) == tuple:
        f = EVAL(car(c),env)
        if callable(f):
            return f(cdr(c),env)
        else:
            return (f,eval_list(cdr(c),env))
    elif type(c) == str:
        return env[c]
    elif type(c) == list:
        return [EVAL(x,env) for x in c]
    elif type(c) == dict:
        return {k : EVAL(c[k],env) for k in c.keys()}        
    else:
        return c
        
repl_env = Env()
repl_env['true'] = True
repl_env['false'] = False
repl_env['nil'] = None
repl_env['quote'] = lambda c,e: EVAL(car(c),e)+EVAL(cadr(c),e)
repl_env['+'] = lambda c,e: EVAL(car(c),e)+EVAL(cadr(c),e)
repl_env['-'] = lambda c,e: EVAL(car(c),e)-EVAL(cadr(c),e)
repl_env['*'] = lambda c,e: EVAL(car(c),e)*EVAL(cadr(c),e)
repl_env['/'] = lambda c,e: int(EVAL(car(c),e)/EVAL(cadr(c),e))
repl_env['def!'] = lambda c,e: e.__setitem__(car(c),EVAL(cadr(c),e))
repl_env['let*'] = LET
repl_env['do'] = DO
repl_env['if'] = IF
repl_env['fn*'] = lambda c,e: Closure(car(c),cadr(c),e)
repl_env['list'] = LIST
repl_env['list?'] = LISTQ
repl_env['empty?'] = EMPTYQ
repl_env['count'] = COUNT
repl_env['<'] = lambda c,e: EVAL(car(c),e)<EVAL(cadr(c),e)
repl_env['>'] = lambda c,e: EVAL(car(c),e)>EVAL(cadr(c),e)
repl_env['<='] = lambda c,e: EVAL(car(c),e)<=EVAL(cadr(c),e)
repl_env['>='] = lambda c,e: EVAL(car(c),e)>=EVAL(cadr(c),e)
repl_env['='] = lambda c,e: EVAL(car(c),e)==EVAL(cadr(c),e)       
                       
while True:
    try:
        print(to_str(EVAL(READ(),repl_env)))
    except Exception as e:
        print("".join(traceback.format_exception(*sys.exc_info())))         
    except EOFError:
        break
