import pydoc
import re, sys, os

def bold(text):
    """Format a string in bold by overstriking."""
    return ''.join(map(lambda ch: ch + "\b" + ch, text))

def underline(text):
    """Format a string in underline by overstriking."""
    return ''.join(map(lambda ch: ch + "\b_", text))

def section(head,body):
    text = "\n".join(map(lambda line: "\t" + line, body.split("\n")))
    return bold(head.upper()) + "\n" + text + "\n"

class rsfpar:
    def __init__(self,type,default='',range='',desc=''):
        self.type = underline(type) + " "
        self.default = "=" + str(default)
        self.range = " " + range
        self.desc = "\t" + desc + "\n"
    def show(self,name):
        return self.type + bold(name + self.default) + self.range + self.desc

class rsfprog:
    def __init__(self,name,file,dir,desc=None):
        self.name = name
        self.file = file
        self.prog = os.path.join(dir,name) 
        self.desc = desc
        self.snps = None
        self.cmts = None
        self.also = None
        self.pars = {}
    def synopsis (self,snps,cmts):
        self.snps = snps
        self.cmts = cmts
    def par (self,name,par):
        self.pars[name] = par
    def document(self):
        doc = section('name',self.name)
        if self.desc:
            doc += section('description',self.desc)
        if self.snps:
            doc += section('synopsis',self.snps)
        if self.cmts:
            doc += section('comments',self.cmts)
        pars =  self.pars.keys()
        if pars:
            pars.sort()
            pardoc = ''
            for par in pars:
                pardoc += self.pars[par].show(par)
            doc += section('parameters',pardoc.rstrip())
        if self.also:
            doc += section('see also',self.also)
        doc += section('source',self.file)
        pydoc.pager(doc)

comment = None
param = None
string = None
synopsis = None

rsfprefix = 'sf'

def getprog(file,out):
    global comment, param, synopsis, string
    if not comment:
        comment = re.compile(r'\/\*((?:[^*]|\*[^/])+)\*\/')
        param = re.compile(r'if\s*\(\!sf_get(?P<type>bool|int|float)\s*'
                           '\(\s*\"(?P<name>\w+)\"\s*\,\s*\&(?P<var>\w+)\s*'
                           '\)\s*\)\s*[\{]?\s*'
                           '(?:(?P=var)\s*\=\s*(?P<default>[^\;]+))?'
                           '\;\s*(?:\/\*\s*(?P<desc>(?:[^*]|\*[^/])+)\*\/)?')
        string = re.compile(r'sf_getstring\s*\(\s*\"(?P<name>\w+)\"[^\;]*\;'
                            '\s*(?:\/\*\s*(?P<desc>(?:[^*]|\*[^/])+)\*\/)?')
        synopsis = re.compile(r'\s*Takes\s*\:\s*((?:[^\n]|[\n][^\n])+)'
                              '((?:.|\n)*)$')
    dir = os.path.dirname(os.path.abspath(file))
    print dir
    name = rsfprefix + re.sub('^M','',os.path.basename(file))
    name = re.sub('.c$','',name)
    src = open(file,"r")   # open source
    text = ''.join(src.readlines())
    src.close()
    first = comment.match(text)
    if first:
        tops = first.group(1).split("\n")
        desc = tops.pop(0).lstrip()
        first = "\n".join(tops)
    else:
        desc = None
    prog = rsfprog(name,file,dir,desc)
    out.write("%s = rsfdoc.rsfprog('%s','%s','%s','%s')\n" %
              (name,name,file,dir,desc))
    pars = param.findall(text)
    parline = ''
    for par in pars:
        type = par[0]
        parname = par[1]
        default = par[3]
        desc = par[4]
        range = ''
        if (type == 'bool'):
            if (default == 'true'):
                default = 'y'
            else:
                default = 'n'
            type = 'bool  ' # to align with string
            range = '[y/n]'
        elif (type == 'int'):
            type = 'int   ' # to align with string
        elif (type == 'float'):
            type = 'float ' # to align with string
        prog.par(parname,rsfpar(type,default,range,desc))
        out.write("%s.par('%s',rsfdoc.rsfpar('%s','%s','%s','''%s'''))\n" %
                  (name,parname,type,default,range,desc))
        parline += " %s=%s" % (parname,default)
    pars = string.findall(text)
    for par in pars:
        type = 'string'
        parname = par[0]
        desc = par[1]
        prog.par(parname,rsfpar("string",desc=desc))
        out.write("%s.par('%s',rsfdoc.rsfpar('string',desc='''%s'''))\n" %
                  (name,parname,desc))
        parline += " %s=" % (parname)
    if first:
        info = synopsis.match(first)
        if info:
            snps = name + " " + info.group(1).lstrip() + parline
            cmts = info.group(2).lstrip()
            prog.synopsis(snps,cmts)
            out.write("%s.synopsis('''%s''','''%s''')\n" % (name,snps,cmts))
    out.write("rsfprog['%s']=%s\n\n" % (name,name))

if __name__ == "__main__":
    junk = open('junk.py',"w")
    junk.write("import rsfdoc\n\n")
    junk.write("rsfprog = {}\n")
    getprog('seis/main/dd.c',junk)
    junk.write("sfdd.document()\n\n")
    junk.write("print sfdd.prog\n\n")
    junk.close()
    #
    import junk
    #
    os.unlink("junk.py")
    os.unlink("junk.pyc")


