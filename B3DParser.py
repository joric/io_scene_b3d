#!/usr/bin/python3
# by Joric, https://github.com/joric/io_scene_b3d

import os
import struct

FX_FULLBRIGHT=  0x0001
FX_VERTEXCOLOR= 0x0002
FX_FLATSHADED=  0x0004
FX_NOFOG=       0x0008
FX_DOUBLESIDED= 0x0010
FX_VERTEXALPHA= 0x0020
FX_ALPHATEST=   0x2000
FX_CONDLIGHT=   0x4000
FX_EMISSIVE=    0x8000

BLEND_REPLACE=  0
BLEND_ALPHA=    1
BLEND_MULTIPLY= 2
BLEND_ADD=      3
BLEND_DOT3=     4
BLEND_MULTIPLY2=5

class B3DParser:
    def __init__(self):
        self.fp = None

    def gets(self):
        s = b''
        while True:
            c = self.fp.read(1)
            if c == b'\x00':
                return s.decode(errors='ignore')
            s += c

    def i(self,n):
        return struct.unpack(n*'i', self.fp.read(n*4))

    def f(self,n):
        return struct.unpack(n*'f', self.fp.read(n*4))

    def next_chunk(self):
        pos = self.fp.tell()
        s1,s2,s3,s4, size = struct.unpack('4ci', self.fp.read(8))
        chunk = ''.join([chr(ord(x)) for x in (s1,s2,s3,s4)])
        next = pos + size + 8
        return chunk, pos, size, next

    def cb_result(self):
        return True

    def parse(self, filepath):
        filesize = os.stat(filepath).st_size
        self.fp = open(filepath,'rb')
        stack = []
        while self.fp.tell() <= filesize-8:

            while stack and stack[-1]==self.fp.tell():
                del stack[-1]
                self.cb_prev()

            chunk, pos, size, next = self.next_chunk()

            if chunk=='BB3D':
                self.cb_data(chunk, {'version': self.i(1)[0]})
                continue

            if chunk=='ANIM':
                flags, frames = self.i(2)
                fps = self.f(1)[0]
                self.cb_data(chunk, {'flags':flags, 'frames':frames, 'fps':fps})

            elif chunk=='TEXS':
                data = []
                while self.fp.tell()<next:
                    name = self.gets()
                    flags, blend = self.i(2)
                    pos = self.f(2)
                    scale = self.f(2)
                    rot = self.f(1)[0]
                    data.append(dotdict({'name':name,'position':pos,'scale':scale,'rotation':rot}))
                self.cb_data(chunk,{'textures':data})

            elif chunk=='BRUS':
                n_texs = self.i(1)[0]
                data = []
                while self.fp.tell()<next:
                    name = self.gets()
                    rgba = self.f(4)
                    shine = self.f(1)[0]
                    blend, fx = self.i(2)
                    tids = self.i(n_texs)
                    data.append(dotdict({'name':name, 'rgba':rgba,'shine':shine, 'blend':blend,'fx':fx,'tids':tids}))
                self.cb_data(chunk, {'materials':data})

            elif chunk=='NODE':
                self.cb_next()
                stack.append(next)
                name = self.gets()
                p = self.f(3)
                s = self.f(3)
                r = self.f(4)
                self.cb_data(chunk, {'name':name, 'position':p, 'rotation':r, 'scale':s})
                continue

            elif chunk=='BONE':
                bones = []
                while self.fp.tell()<next:
                    vertex_id = self.i(1)[0]
                    weight = self.f(1)[0]
                    bones.append((vertex_id, weight))
                self.cb_data(chunk,{'bones': bones})

            elif chunk=='MESH':
                self.cb_data(chunk, {'brush_id': self.i(1)[0]})
                #self.cb_next()
                #stack.append(next)
                continue

            elif chunk=='VRTS':
                flags, tcs, tcss = self.i(3)
                v,n,c,u = [],[],[],[]
                while self.fp.tell()<next:
                    v.append(self.f(3))
                    if flags & 1: n.append(self.f(3))
                    if flags & 2: c.append(self.f(4))
                    if tcs*tcss: u.append(self.f(tcs*tcss))
                self.cb_data(chunk, {'vertices':v, 'normals':n, 'rgba':c, 'uvs':u})

            elif chunk=='TRIS':
                brush_id = self.i(1)[0]
                faces = []
                while self.fp.tell()<next:
                    vertex_id = self.i(3)
                    faces.append(vertex_id)
                self.cb_data(chunk, {'brush_id':brush_id, 'indices':faces})

            elif chunk=='KEYS':
                flags = self.i(1)[0]
                keys = []
                while self.fp.tell()<next:
                    key = dotdict({'frame':self.i(1)[0]})
                    if flags & 1: key['position'] = self.f(3)
                    if flags & 2: key['scale'] = self.f(3)
                    if flags & 4: key['rotation'] = self.f(4)
                    keys.append(key)
                self.cb_data(chunk, keys)

            self.fp.seek(next)

        return self.cb_result()

class dotdict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__

# json list format

class B3DList(B3DParser):
    def __init__(self):
        B3DParser.__init__(self)
        self.index = -1
        self.data = dotdict()
        self.data.nodes = []

    def cb_next(self):
        self.data.nodes.append(dotdict())
        parent = self.index
        self.index = len(self.data.nodes)-1
        self.data.nodes[self.index].parent = parent

    def cb_prev(self):
        self.index = self.data.nodes[self.index].parent

    def cb_data(self, chunk, data):
        if self.index != -1:
            node = self.data.nodes[self.index]

        if chunk in ['NODE','MESH','VRTS','BONE']:
            node.update(data)
        elif chunk=='TRIS':
            if 'faces' not in node:
                node.faces = []
            node.faces.append(dotdict(data))
        elif chunk=='KEYS':
            if 'keys' not in node:
                node['keys'] = []
            node['keys'].extend(data)
        elif chunk in ['ANIM', 'TEXS', 'BRUS']:
            self.data.update(data)

    def cb_result(self):
        return self.data

# json tree format (derived from B3DList, used in import)

class B3DTree(B3DList):
    def __init__(self):
        B3DList.__init__(self)

    def cb_result(self):
        tree = []
        nodes = self.data.nodes

        for node in nodes:
            node.nodes = []

        for i, node in enumerate(nodes):
            if node.parent == -1:
                tree.append(node)
            else:
                nodes[node.parent].nodes.append(node)
            del node['parent']

        self.data.update({'nodes':tree})
        return self.data

def dump(node, level=0):
    for node in node.nodes:
        print(node.name)
        dump(node, level+1)

# human readable text format

class B3DDebugParser(B3DParser):
    class B3DDebugParserItem:
        def __init__(self, chunk=None, data=None, level=0):
            self.chunk = chunk
            self.data = data
            self.level = level

    def __init__(self, max_width=256, max_items=3):
        B3DParser.__init__(self)
        self.max_width = max_width
        self.max_items = max_items
        self.level = 0
        self.counter = 0
        self.item = self.B3DDebugParserItem()

    def cb_next(self):
        self.level += 1

    def cb_prev(self):
        self.level -= 1

    def print_item(self, chunk, data, indent):
        w = {'TEXS':'textures', 'BRUS':'materials'}
        expand_data = chunk in w

        # non-node items are always extra-indented
        if chunk not in ('NODE','BB3D'):
            indent += 1

        if expand_data:
            section = w[chunk]
            print(' '*indent, end='')
            print(chunk)
            for i,d in enumerate(data[section]):
                print(' '*indent, end='')
                print(f' {chunk}[{i}]', d)
        else:
            print(' '*indent, end='')
            w = self.max_width if self.max_width else 8192
            s = str(data)
            s = s[:w]+ f' ...' if len(s)>w else s
            print(chunk, s)

    def cb_data(self, chunk, data):
        new = False
        if self.item.chunk != chunk:
            new = True
        else:
            self.counter += 1

        if new or self.counter <= self.max_items:

            # print the last repeated item, if any
            if self.counter > self.max_items:
                print(' '*self.item.level, end='')
                print(f' (... {self.item.chunk} repeated {self.counter-self.max_items} times ...)')
                self.print_item(self.item.chunk, self.item.data, self.item.level)

            self.print_item(chunk, data, self.level)

        if new:
            self.counter = 1

        self.item = self.B3DDebugParserItem(chunk, data, self.level)

debug = True
#filepath = 'C:/Games/GnomE/media/levels/level1.b3d'
filepath = 'C:/Games/GnomE/media/models/gnome/model.b3d'
#filepath = 'C:/Games/GnomE/media/models/medved/med_run.b3d'
#filepath = 'C:/Games/GnomE/media/levels/level2.b3d'
#filepath='C:/Games/MasterOfDefense/Data/Location1/location1.b3d'
#filepath='C:/Games/MasterOfDefense/Data/Location5/location5.b3d'
#filepath = 'C:/Games/GnomE/media/levels/level5.b3d'

#filepath= 'C:/Games/Sonic World DX 1.2.4/Data/Characters/bio.b3d'

if __name__ == '__main__':
    import sys
    if len(sys.argv)<2 and not debug:
        print('Usage: B3DParser.py [filename.b3d]')
        sys.exit(0)
    if not debug:
        filepath = sys.argv[1]

    #B3DDebugParser().parse(filepath) # text dump
    #data = B3DList().parse(filepath) # json list
    #data = B3DTree().parse(filepath) # json tree

    #import json
    #print(json.dumps(data, indent=1))
    #dump(data)

    sys.stdout = open('out.txt', 'w')
    p = B3DDebugParser() # human readable
    print('dumping', filepath)
    p.parse(filepath)

