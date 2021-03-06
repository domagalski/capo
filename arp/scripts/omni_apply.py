#! /usr/bin/env python

import omnical, aipy, numpy, capo
import pickle, optparse, os, sys

### Options ###
o = optparse.OptionParser()
o.set_usage('omni_apply.py [options] *uvcRRE')
o.set_description(__doc__)
o.add_option('--xtalk',dest='xtalk',default=False,action='store_true',
            help='Apply xtalk solutions to data.')
opts,args = o.parse_args(sys.argv[1:])

### Read Data and Solutions ###
for f,filename in enumerate(args):
    print 'Reading', filename
    newfile = filename+'O'
    if os.path.exists(newfile):
        print newfile, 'exists.  Skipping...'
        continue
    print '    omnical solutions from', filename+'.npz'
    _,gains,_,xtalk = capo.omni.from_npz(filename+'.npz')
    times = []
    def mfunc(uv,p,d,f): #loops over time and baseline
        global times
        _,t,(a1,a2) = p
        p1,p2 = pol = aipy.miriad.pol2str[uv['pol']]
        if len(times) == 0 or times[-1] != t: times.append(t)
        if opts.xtalk:
            try: d -= xtalk[pol][(a1,a2)]
            except(KeyError):
                try: d -= xtalk[pol][(a2,a1)].conj()
                except(KeyError): pass
        ti = len(times) - 1
        try: d /= gains[p1][a1][ti]
        except(KeyError): pass
        try: d /= gains[p2][a2][ti].conj() 
        except(KeyError): pass
        return p, numpy.where(f,0,d), f
    if opts.xtalk: print '    calibrating and subtracting xtalk'
    else: print '    calibrating'
    uvi = aipy.miriad.UV(filename)
    uvo = aipy.miriad.UV(newfile,status='new')
    uvo.init_from_uv(uvi)
    print '    writing', newfile
    uvo.pipe(uvi, mfunc=mfunc, raw=True, append2hist='OMNICAL: ' + ' '.join(sys.argv) + '\n')
